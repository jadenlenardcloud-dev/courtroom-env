"""
Courtroom Argument Simulator - OpenEnv Environment
Simulates a real courtroom proceeding where an AI agent acts as a defense attorney.
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from tasks import TASKS


# ── Typed Models (OpenEnv spec) ────────────────────────────────────────────────

class Observation(BaseModel):
    """What the agent sees at each step."""
    turn: int = Field(description="Current turn number (0-indexed)")
    max_turns: int = Field(description="Maximum turns allowed in this episode")
    phase: str = Field(description="Current phase: opening | examination | cross | closing | verdict")
    charge: str = Field(description="The criminal charge against the defendant")
    defendant_profile: Dict[str, Any] = Field(description="Background info about the defendant")
    current_witness: Optional[Dict[str, Any]] = Field(default=None, description="Active witness on stand")
    evidence_available: List[Dict[str, Any]] = Field(description="Evidence the agent can reference")
    prosecution_last_move: str = Field(description="Last statement/action by the prosecution")
    jury_mood: float = Field(description="Estimated jury sympathy 0.0 (hostile) to 1.0 (sympathetic)")
    judge_patience: float = Field(description="Judge patience 0.0 (angry) to 1.0 (patient)")
    case_strength: float = Field(description="Agent's case strength estimate 0.0-1.0")
    objections_remaining: int = Field(description="Objections agent can still raise this phase")
    message: str = Field(description="Narrative description of current situation")


class Action(BaseModel):
    """An action the agent can take."""
    action_type: str = Field(
        description=(
            "One of: present_argument | cross_examine | raise_objection | "
            "present_evidence | question_witness | negotiate_plea | "
            "request_recess | deliver_closing | accept_plea"
        )
    )
    content: str = Field(description="The actual argument text, question, or statement")
    target: Optional[str] = Field(default=None, description="Target witness name or evidence ID if applicable")


class Reward(BaseModel):
    """Reward signal with breakdown."""
    total: float = Field(description="Total reward for this step")
    argument_quality: float = Field(description="Quality score for the legal argument made")
    phase_appropriateness: float = Field(description="Was this the right action for this phase?")
    jury_impact: float = Field(description="How much did jury sympathy change?")
    judge_impact: float = Field(description="Effect on judge patience")
    penalty: float = Field(description="Any penalties applied (objections, irrelevance)")
    cumulative: float = Field(description="Total reward accumulated this episode")


# ── Environment Class ──────────────────────────────────────────────────────────

class CourtroomEnvironment:
    """
    OpenEnv-compliant Courtroom Argument Simulator.

    The agent plays a defense attorney navigating a criminal trial.
    It must argue effectively, examine witnesses, present evidence,
    and ultimately secure the best possible outcome for the defendant.
    """

    VALID_ACTIONS = {
        "present_argument",
        "cross_examine",
        "raise_objection",
        "present_evidence",
        "question_witness",
        "negotiate_plea",
        "request_recess",
        "deliver_closing",
        "accept_plea",
    }

    PHASES = ["opening", "examination", "cross", "closing", "verdict"]

    def __init__(self, task_id: str = "task_easy"):
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id '{task_id}'. Available: {list(TASKS.keys())}")
        self.task_id = task_id
        self.task = TASKS[task_id]
        self._state: Dict[str, Any] = {}
        self._cumulative_reward: float = 0.0
        self._done: bool = False
        self._action_log: List[Dict] = []

    # ── OpenEnv Required Methods ───────────────────────────────────────────────

    def reset(self) -> Observation:
        """Reset environment to initial state for this task."""
        task_def = self.task

        self._state = {
            "turn": 0,
            "max_turns": task_def["max_turns"],
            "phase": "opening",
            "phase_turn": 0,
            "charge": task_def["charge"],
            "defendant_profile": task_def["defendant_profile"].copy(),
            "witnesses": [w.copy() for w in task_def["witnesses"]],
            "current_witness_idx": 0,
            "evidence_available": [e.copy() for e in task_def["evidence"]],
            "evidence_presented": [],
            "prosecution_last_move": task_def["prosecution_opening"],
            "jury_mood": task_def["initial_jury_mood"],
            "judge_patience": 1.0,
            "case_strength": task_def["initial_case_strength"],
            "objections_remaining": task_def["objections_per_phase"],
            "objections_used": 0,
            "plea_available": task_def.get("plea_available", False),
            "plea_accepted": False,
            "verdict": None,
            "done": False,
        }
        self._cumulative_reward = 0.0
        self._done = False
        self._action_log = []

        return self._build_observation(
            message=f"Court is now in session. You represent {self._state['defendant_profile']['name']} "
                    f"charged with {self._state['charge']}. The prosecution has delivered their opening statement."
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """
        Execute one action and return (observation, reward, done, info).
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        if action.action_type not in self.VALID_ACTIONS:
            raise ValueError(f"Invalid action_type '{action.action_type}'. Valid: {self.VALID_ACTIONS}")

        # Compute reward for this action
        reward = self._compute_reward(action)

        # Update state based on action
        self._apply_action(action)

        # Advance turn
        self._state["turn"] += 1
        self._state["phase_turn"] += 1

        # Advance phase if needed
        self._maybe_advance_phase()

        # Check terminal conditions
        self._check_done()

        self._cumulative_reward += reward.total
        reward.cumulative = round(self._cumulative_reward, 4)

        self._action_log.append({
            "turn": self._state["turn"],
            "action": action.action_type,
            "content_snippet": action.content[:80],
            "reward": reward.total,
        })

        obs = self._build_observation(message=self._generate_message(action, reward))
        info = {
            "task_id": self.task_id,
            "phase": self._state["phase"],
            "turn": self._state["turn"],
            "action_log": self._action_log[-1],
        }

        return obs, reward, self._done, info

    def state(self) -> Dict[str, Any]:
        """Return full internal state (for debugging / grading)."""
        return {
            **self._state,
            "cumulative_reward": self._cumulative_reward,
            "done": self._done,
            "action_log": self._action_log,
            "task_id": self.task_id,
        }

    # ── Internal Helpers ───────────────────────────────────────────────────────

    def _build_observation(self, message: str = "") -> Observation:
        s = self._state
        current_witness = None
        if s["phase"] in ("examination", "cross") and s["witnesses"]:
            idx = min(s["current_witness_idx"], len(s["witnesses"]) - 1)
            current_witness = s["witnesses"][idx]

        return Observation(
            turn=s["turn"],
            max_turns=s["max_turns"],
            phase=s["phase"],
            charge=s["charge"],
            defendant_profile=s["defendant_profile"],
            current_witness=current_witness,
            evidence_available=[
                e for e in s["evidence_available"]
                if e["id"] not in s["evidence_presented"]
            ],
            prosecution_last_move=s["prosecution_last_move"],
            jury_mood=round(s["jury_mood"], 3),
            judge_patience=round(s["judge_patience"], 3),
            case_strength=round(s["case_strength"], 3),
            objections_remaining=s["objections_remaining"],
            message=message,
        )

    def _compute_reward(self, action: Action) -> Reward:
        s = self._state
        arg_quality = 0.0
        phase_score = 0.0
        jury_delta = 0.0
        judge_delta = 0.0
        penalty = 0.0

        # Phase-action alignment
        phase_action_map = {
            "opening": {"present_argument", "negotiate_plea"},
            "examination": {"question_witness", "present_evidence", "raise_objection"},
            "cross": {"cross_examine", "raise_objection", "present_evidence"},
            "closing": {"deliver_closing", "present_argument"},
            "verdict": {"accept_plea"},
        }
        valid_for_phase = phase_action_map.get(s["phase"], set())
        phase_score = 0.4 if action.action_type in valid_for_phase else -0.2

        # Argument quality heuristic (length + keyword matching)
        content_lower = action.content.lower()
        legal_keywords = [
            "evidence", "witness", "reasonable doubt", "alibi", "motive",
            "testimony", "objection", "sustained", "precedent", "defendant",
            "prosecution", "facts", "circumstantial", "constitutional", "rights",
        ]
        keyword_hits = sum(1 for kw in legal_keywords if kw in content_lower)
        content_length_score = min(len(action.content) / 200.0, 0.5)
        arg_quality = min(keyword_hits * 0.08 + content_length_score, 0.6)

        # Specific action bonuses
        if action.action_type == "raise_objection":
            if s["objections_remaining"] > 0:
                # Good if prosecution just made a weak move
                jury_delta = 0.05
                judge_delta = -0.05  # Uses judge's patience slightly
            else:
                penalty = -0.3  # No objections left!

        elif action.action_type == "present_evidence":
            # Check if referenced evidence exists
            if action.target:
                ev_ids = [e["id"] for e in s["evidence_available"]]
                if action.target in ev_ids and action.target not in s["evidence_presented"]:
                    jury_delta = 0.08
                    arg_quality += 0.2
                else:
                    penalty = -0.1  # Evidence already presented or doesn't exist

        elif action.action_type == "cross_examine":
            if s["phase"] == "cross":
                jury_delta = 0.1
                arg_quality += 0.1
            else:
                penalty = -0.15

        elif action.action_type == "deliver_closing":
            if s["phase"] == "closing":
                # Big moment — scale with case strength
                arg_quality = min(arg_quality + s["case_strength"] * 0.3, 0.9)
                jury_delta = 0.15 * s["case_strength"]
            else:
                penalty = -0.2

        elif action.action_type == "negotiate_plea":
            if s["plea_available"]:
                # Partial reward for attempting negotiation
                arg_quality = 0.3
                jury_delta = -0.05  # Jury sees this as weakness
            else:
                penalty = -0.1

        elif action.action_type == "request_recess":
            judge_delta = -0.1  # Slightly annoys judge
            penalty = -0.05

        # Clamp jury mood and judge patience
        new_jury = max(0.0, min(1.0, s["jury_mood"] + jury_delta))
        new_judge = max(0.0, min(1.0, s["judge_patience"] + judge_delta))

        # Update state immediately for reward calculation
        s["jury_mood"] = new_jury
        s["judge_patience"] = new_judge

        # Update case strength
        cs_delta = (arg_quality - 0.2) * 0.15
        s["case_strength"] = max(0.0, min(1.0, s["case_strength"] + cs_delta))

        total = round(arg_quality * 0.5 + phase_score * 0.3 + jury_delta * 0.2 + penalty, 4)
        total = max(-1.0, min(1.0, total))

        return Reward(
            total=total,
            argument_quality=round(arg_quality, 4),
            phase_appropriateness=round(phase_score, 4),
            jury_impact=round(jury_delta, 4),
            judge_impact=round(judge_delta, 4),
            penalty=round(penalty, 4),
            cumulative=0.0,  # filled in after
        )

    def _apply_action(self, action: Action):
        s = self._state
        if action.action_type == "raise_objection" and s["objections_remaining"] > 0:
            s["objections_remaining"] -= 1
            s["objections_used"] += 1

        if action.action_type == "present_evidence" and action.target:
            ev_ids = [e["id"] for e in s["evidence_available"]]
            if action.target in ev_ids and action.target not in s["evidence_presented"]:
                s["evidence_presented"].append(action.target)

        if action.action_type == "accept_plea" and s["plea_available"]:
            s["plea_accepted"] = True
            s["done"] = True
            self._done = True

        # Prosecution responds based on phase
        prosecution_responses = self.task.get("prosecution_responses", [])
        if prosecution_responses:
            s["prosecution_last_move"] = prosecution_responses[
                s["turn"] % len(prosecution_responses)
            ]

    def _maybe_advance_phase(self):
        s = self._state
        turns_per_phase = s["max_turns"] // len(self.PHASES)
        current_phase_idx = self.PHASES.index(s["phase"])

        if s["phase_turn"] >= turns_per_phase and current_phase_idx < len(self.PHASES) - 1:
            s["phase"] = self.PHASES[current_phase_idx + 1]
            s["phase_turn"] = 0
            s["objections_remaining"] = self.task["objections_per_phase"]
            # Move to next witness
            if s["phase"] == "cross":
                s["current_witness_idx"] = min(
                    s["current_witness_idx"] + 1, len(s["witnesses"]) - 1
                )

    def _check_done(self):
        s = self._state
        if s["turn"] >= s["max_turns"]:
            s["phase"] = "verdict"
            self._compute_verdict()
            self._done = True
        elif s["judge_patience"] <= 0.05:
            s["verdict"] = "dismissed_misconduct"
            self._done = True
        elif s["plea_accepted"]:
            self._done = True

    def _compute_verdict(self):
        s = self._state
        score = (
            s["jury_mood"] * 0.4
            + s["case_strength"] * 0.4
            + s["judge_patience"] * 0.2
        )
        if score >= 0.75:
            s["verdict"] = "not_guilty"
        elif score >= 0.55:
            s["verdict"] = "hung_jury"
        elif score >= 0.35:
            s["verdict"] = "guilty_reduced"
        else:
            s["verdict"] = "guilty_full"

    def _generate_message(self, action: Action, reward: Reward) -> str:
        s = self._state
        verdict_msg = ""
        if self._done and s.get("verdict"):
            vmap = {
                "not_guilty": "VERDICT: NOT GUILTY! Your client walks free.",
                "hung_jury": "VERDICT: HUNG JURY. Case will be retried.",
                "guilty_reduced": "VERDICT: GUILTY on reduced charges.",
                "guilty_full": "VERDICT: GUILTY on all counts.",
                "dismissed_misconduct": "CASE DISMISSED due to attorney misconduct.",
            }
            verdict_msg = " | " + vmap.get(s["verdict"], "")

        return (
            f"[Turn {s['turn']}/{s['max_turns']}] [{s['phase'].upper()}] "
            f"Jury mood: {s['jury_mood']:.2f} | Case strength: {s['case_strength']:.2f} | "
            f"Reward: {reward.total:+.3f}{verdict_msg}"
        )

"""
Inference Script — Courtroom Argument Simulator
================================================
MANDATORY ENVIRONMENT VARIABLES:
    API_BASE_URL   The API endpoint for the LLM.
    MODEL_NAME     The model identifier to use for inference.
    HF_TOKEN       Your Hugging Face / API key.

STDOUT FORMAT (strictly followed — deviations cause incorrect scoring):
    [START] task=<task_name> env=courtroom-simulator model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>

Usage:
    python inference.py
    python inference.py --task task_easy
    python inference.py --all
"""

import os
import sys
import json
import argparse
from typing import Any, Dict, List, Optional

from openai import OpenAI

from environment import CourtroomEnvironment, Action
from grader import grade_episode, grade_all


# ── Mandatory env vars (with defaults for local dev) ──────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "gpt-4o-mini")
HF_TOKEN     = os.getenv("HF_TOKEN")    or os.getenv("OPENAI_API_KEY")

BENCHMARK    = "courtroom-simulator"


# ── System prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert criminal defense attorney in a courtroom simulation.
At each step you receive the current trial state and must choose ONE action.

Your response MUST be valid JSON with exactly this structure:
{
  "action_type": "<one of the valid action types>",
  "content": "<your argument, question, or statement>",
  "target": "<witness_id or evidence_id if applicable, else null>"
}

Valid action_type values:
- present_argument   (opening, closing phases)
- cross_examine      (cross phase — challenge prosecution witnesses)
- raise_objection    (any phase — limited budget, use wisely)
- present_evidence   (set target = evidence id, e.g. "ev1")
- question_witness   (examination phase — support your own witnesses)
- negotiate_plea     (if plea_available)
- request_recess     (minor action)
- deliver_closing    (closing phase only)
- accept_plea        (accept prosecution offer)

Strategy:
- Opening: present_argument to establish narrative
- Examination: question_witness + present_evidence for alibi/key evidence
- Cross: cross_examine witnesses + raise_objection for weak prosecution claims
- Closing: deliver_closing with full case summary
- Always mention specific evidence IDs and witness names when available

Respond ONLY with the JSON object. No markdown, no explanation."""


def _log_start(task: str, model: str):
    """Emit mandatory [START] line."""
    print(f"[START] task={task} env={BENCHMARK} model={model}", flush=True)


def _log_step(step: int, action_str: str, reward: float, done: bool, error: Optional[str]):
    """Emit mandatory [STEP] line."""
    err = error if error else "null"
    done_str = "true" if done else "false"
    print(
        f"[STEP] step={step} action={action_str} "
        f"reward={reward:.2f} done={done_str} error={err}",
        flush=True,
    )


def _log_end(success: bool, steps: int, score: float, rewards: List[float]):
    """Emit mandatory [END] line."""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_str = "true" if success else "false"
    print(
        f"[END] success={success_str} steps={steps} "
        f"score={score:.2f} rewards={rewards_str}",
        flush=True,
    )


def _parse_action(raw: str) -> Optional[Action]:
    """Parse LLM JSON response into an Action. Returns None on failure."""
    try:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(
                l for l in lines if not l.strip().startswith("```")
            ).strip()
        data = json.loads(cleaned)
        return Action(**data)
    except Exception:
        return None


def _fallback_action(phase: str) -> Action:
    """Deterministic fallback when LLM response fails to parse."""
    fallbacks = {
        "opening":     ("present_argument",
                        "The defense will demonstrate that the prosecution has failed to meet "
                        "the burden of proof beyond reasonable doubt. The evidence will show "
                        "our client's innocence clearly.", None),
        "examination": ("question_witness",
                        "Please describe in detail what you witnessed and how you can confirm "
                        "the defendant's presence or actions at the time in question.", None),
        "cross":       ("cross_examine",
                        "Is it not true that your testimony is based entirely on circumstantial "
                        "evidence with no direct proof linking my client to this alleged crime?", None),
        "closing":     ("deliver_closing",
                        "Ladies and gentlemen of the jury, throughout this trial the defense has "
                        "shown that reasonable doubt exists. The prosecution has not met its burden. "
                        "We ask for a verdict of not guilty.", None),
        "verdict":     ("present_argument",
                        "The defense rests. The evidence clearly supports acquittal.", None),
    }
    atype, content, target = fallbacks.get(phase, fallbacks["opening"])
    return Action(action_type=atype, content=content, target=target)


def run_task(
    client: OpenAI,
    task_id: str,
    model: str,
) -> Dict[str, Any]:
    """
    Run one full episode on a task.
    Emits [START], one [STEP] per turn, then [END].
    Returns the grader result dict.
    """
    env = CourtroomEnvironment(task_id=task_id)
    obs = env.reset()

    _log_start(task=task_id, model=model)

    step_num   = 0
    rewards: List[float] = []
    last_error: Optional[str] = None

    while True:
        user_msg = (
            f"TRIAL STATE — Turn {obs.turn + 1}/{obs.max_turns}\n"
            f"Phase: {obs.phase.upper()}\n"
            f"Charge: {obs.charge}\n"
            f"Defendant: {obs.defendant_profile['name']} | "
            f"Prior record: {obs.defendant_profile.get('prior_record', 'None')}\n"
            f"Alibi: {obs.defendant_profile.get('alibi', 'None')}\n\n"
            f"Jury mood: {obs.jury_mood:.2f}/1.0  "
            f"Judge patience: {obs.judge_patience:.2f}/1.0  "
            f"Case strength: {obs.case_strength:.2f}/1.0\n"
            f"Objections remaining: {obs.objections_remaining}\n\n"
            f"Prosecution last move:\n\"{obs.prosecution_last_move}\"\n\n"
            f"Witness on stand: "
            + (json.dumps(obs.current_witness) if obs.current_witness else "None")
            + f"\n\nEvidence still available:\n"
            + json.dumps(obs.evidence_available, indent=2)
            + f"\n\nContext: {obs.message}\n\nChoose your action."
        )

        raw_response = None
        last_error = None
        action = None

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_msg},
                ],
                temperature=0.7,
                max_tokens=400,
            )
            raw_response = response.choices[0].message.content
            action = _parse_action(raw_response)
            if action is None:
                last_error = "json_parse_failed"
        except Exception as e:
            last_error = str(e)[:80].replace("\n", " ")

        if action is None:
            action = _fallback_action(obs.phase)

        obs, reward_obj, done, info = env.step(action)
        step_num += 1
        rewards.append(reward_obj.total)

        action_str = f"{action.action_type}(target={action.target})"
        _log_step(
            step=step_num,
            action_str=action_str,
            reward=reward_obj.total,
            done=done,
            error=last_error,
        )

        if done:
            break

    final_state = env.state()
    final_state["task_id"] = task_id
    grade = grade_episode(final_state)

    score   = grade["score"]
    success = grade["passed"]

    _log_end(success=success, steps=step_num, score=score, rewards=rewards)

    return grade


def run_all_tasks(client: OpenAI, model: str) -> Dict[str, Any]:
    """Run all 3 tasks sequentially and return combined grader report."""
    task_ids = ["task_easy", "task_medium", "task_hard"]
    all_grades = {}

    for task_id in task_ids:
        grade = run_task(client=client, task_id=task_id, model=model)
        all_grades[task_id] = grade

    total  = len(all_grades)
    passed = sum(1 for g in all_grades.values() if g["passed"])
    avg    = sum(g["score"] for g in all_grades.values()) / total

    # Summary goes to stderr — keeps stdout clean for automated parser
    print(f"\n# SUMMARY: {passed}/{total} tasks passed | avg score: {avg:.4f}", file=sys.stderr)
    for tid, g in all_grades.items():
        status = "PASS" if g["passed"] else "FAIL"
        print(
            f"#   {tid:<15} score={g['score']:.4f}  verdict={g['verdict']}  [{status}]",
            file=sys.stderr,
        )

    return all_grades


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Courtroom Argument Simulator — Baseline Inference"
    )
    parser.add_argument(
        "--task",
        default="task_easy",
        choices=["task_easy", "task_medium", "task_hard"],
        help="Single task to run (default: task_easy)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all 3 tasks sequentially",
    )
    args = parser.parse_args()

    if not HF_TOKEN:
        print(
            "ERROR: HF_TOKEN (or OPENAI_API_KEY) environment variable not set.\n"
            "Export it: export HF_TOKEN=hf-...",
            file=sys.stderr,
        )
        sys.exit(1)

    client = OpenAI(
        api_key=HF_TOKEN,
        base_url=API_BASE_URL,
    )

    if args.all:
        run_all_tasks(client=client, model=MODEL_NAME)
    else:
        run_task(client=client, task_id=args.task, model=MODEL_NAME)


if __name__ == "__main__":
    main()

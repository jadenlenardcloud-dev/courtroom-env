"""
Graders for the Courtroom Argument Simulator.
Each grader takes the final environment state and produces a score 0.0–1.0.
All graders are deterministic given the same final state.
"""

from __future__ import annotations
from typing import Any, Dict


def grade_episode(final_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Grade a completed episode. Dispatches to the task-specific grader.
    Returns a dict with score (0.0–1.0) and breakdown.
    """
    task_id = final_state.get("task_id", "task_easy")
    graders = {
        "task_easy": grade_easy,
        "task_medium": grade_medium,
        "task_hard": grade_hard,
    }
    grader = graders.get(task_id, grade_easy)
    return grader(final_state)


# ──────────────────────────────────────────────────────────────────────────────
# TASK 1 — EASY GRADER
# Win condition: not_guilty or hung_jury
# Measures: correct verdict, alibi evidence usage, jury mood
# ──────────────────────────────────────────────────────────────────────────────

def grade_easy(state: Dict[str, Any]) -> Dict[str, Any]:
    score = 0.0
    breakdown = {}

    # 1. Verdict outcome (50 points max)
    verdict = state.get("verdict")
    verdict_map = {
        "not_guilty": 0.50,
        "hung_jury": 0.35,
        "guilty_reduced": 0.10,
        "guilty_full": 0.0,
        "dismissed_misconduct": 0.0,
    }
    verdict_score = verdict_map.get(verdict, 0.0)
    score += verdict_score
    breakdown["verdict_score"] = verdict_score
    breakdown["verdict"] = verdict

    # 2. Alibi evidence presented (20 points)
    presented = state.get("evidence_presented", [])
    alibi_evidence = {"ev1", "ev3"}  # medical record + bus pass
    ev_score = len(alibi_evidence & set(presented)) / len(alibi_evidence) * 0.20
    score += ev_score
    breakdown["evidence_score"] = round(ev_score, 4)

    # 3. Final jury mood (20 points)
    jury_mood = state.get("jury_mood", 0.0)
    jury_score = min(jury_mood / 0.8, 1.0) * 0.20
    score += jury_score
    breakdown["jury_mood_score"] = round(jury_score, 4)

    # 4. Judge patience maintained (10 points)
    judge_patience = state.get("judge_patience", 0.0)
    judge_score = min(judge_patience, 1.0) * 0.10
    score += judge_score
    breakdown["judge_score"] = round(judge_score, 4)

    final_score = round(min(score, 1.0), 4)
    return {
        "task_id": "task_easy",
        "difficulty": "easy",
        "score": final_score,
        "passed": final_score >= 0.65,
        "breakdown": breakdown,
        "verdict": verdict,
    }


# ──────────────────────────────────────────────────────────────────────────────
# TASK 2 — MEDIUM GRADER
# Win condition: not_guilty, hung_jury, or guilty_reduced
# Measures: verdict, witness discrediting, evidence quality, efficiency
# ──────────────────────────────────────────────────────────────────────────────

def grade_medium(state: Dict[str, Any]) -> Dict[str, Any]:
    score = 0.0
    breakdown = {}

    # 1. Verdict outcome (40 points)
    verdict = state.get("verdict")
    verdict_map = {
        "not_guilty": 0.40,
        "hung_jury": 0.30,
        "guilty_reduced": 0.20,
        "guilty_full": 0.0,
        "dismissed_misconduct": 0.0,
    }
    verdict_score = verdict_map.get(verdict, 0.0)
    score += verdict_score
    breakdown["verdict_score"] = verdict_score
    breakdown["verdict"] = verdict

    # 2. Key evidence presented (25 points)
    presented = state.get("evidence_presented", [])
    key_evidence = {"ev1", "ev2", "ev3"}  # board minutes + HR record + audit trail
    ev_score = len(key_evidence & set(presented)) / len(key_evidence) * 0.25
    score += ev_score
    breakdown["evidence_score"] = round(ev_score, 4)

    # 3. Jury mood — needs to exceed hostile starting point (20 points)
    jury_mood = state.get("jury_mood", 0.0)
    # Started at 0.3, need to get above 0.6 for full marks
    jury_improvement = max(0.0, jury_mood - 0.30)
    jury_score = min(jury_improvement / 0.40, 1.0) * 0.20
    score += jury_score
    breakdown["jury_improvement_score"] = round(jury_score, 4)

    # 4. Case strength built up (15 points)
    case_strength = state.get("case_strength", 0.0)
    cs_score = min(case_strength / 0.75, 1.0) * 0.15
    score += cs_score
    breakdown["case_strength_score"] = round(cs_score, 4)

    final_score = round(min(score, 1.0), 4)
    return {
        "task_id": "task_medium",
        "difficulty": "medium",
        "score": final_score,
        "passed": final_score >= 0.50,
        "breakdown": breakdown,
        "verdict": verdict,
    }


# ──────────────────────────────────────────────────────────────────────────────
# TASK 3 — HARD GRADER
# Win condition: not_guilty or hung_jury ONLY
# Measures: verdict, suppression evidence, witness cross, jury swing, closing
# ──────────────────────────────────────────────────────────────────────────────

def grade_hard(state: Dict[str, Any]) -> Dict[str, Any]:
    score = 0.0
    breakdown = {}

    # 1. Verdict (40 points — only not_guilty or hung_jury counts meaningfully)
    verdict = state.get("verdict")
    verdict_map = {
        "not_guilty": 0.40,
        "hung_jury": 0.28,
        "guilty_reduced": 0.08,
        "guilty_full": 0.0,
        "dismissed_misconduct": 0.0,
    }
    verdict_score = verdict_map.get(verdict, 0.0)
    score += verdict_score
    breakdown["verdict_score"] = verdict_score
    breakdown["verdict"] = verdict

    # 2. Critical evidence presented (25 points)
    presented = state.get("evidence_presented", [])
    # Must present suppression motion + phone metadata + mediation agreement
    critical_evidence = {"ev1", "ev2", "ev3"}
    bonus_evidence = {"ev4", "ev5"}
    crit_score = len(critical_evidence & set(presented)) / len(critical_evidence) * 0.20
    bonus_score = len(bonus_evidence & set(presented)) / len(bonus_evidence) * 0.05
    ev_score = crit_score + bonus_score
    score += ev_score
    breakdown["evidence_score"] = round(ev_score, 4)

    # 3. Jury swing from hostile starting point (20 points)
    jury_mood = state.get("jury_mood", 0.0)
    # Started at 0.2, needs to reach 0.55+ for full marks
    jury_improvement = max(0.0, jury_mood - 0.20)
    jury_score = min(jury_improvement / 0.40, 1.0) * 0.20
    score += jury_score
    breakdown["jury_swing_score"] = round(jury_score, 4)

    # 4. Action log analysis — penalize poor phase discipline (15 points)
    action_log = state.get("action_log", [])
    total_actions = len(action_log)
    if total_actions > 0:
        # Check if closing was delivered in closing phase
        closing_attempts = [
            a for a in action_log
            if a["action"] == "deliver_closing"
        ]
        # Check cross-examinations happened
        cross_attempts = [
            a for a in action_log
            if a["action"] == "cross_examine"
        ]
        discipline_score = 0.0
        if closing_attempts:
            discipline_score += 0.08
        if len(cross_attempts) >= 2:
            discipline_score += 0.07
        score += discipline_score
        breakdown["discipline_score"] = round(discipline_score, 4)
    else:
        breakdown["discipline_score"] = 0.0

    final_score = round(min(score, 1.0), 4)
    return {
        "task_id": "task_hard",
        "difficulty": "hard",
        "score": final_score,
        "passed": final_score >= 0.40,
        "breakdown": breakdown,
        "verdict": verdict,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Utility: batch grade all tasks at once
# ──────────────────────────────────────────────────────────────────────────────

def grade_all(states: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Grade multiple task states at once. Returns combined report."""
    results = {}
    total_score = 0.0
    for task_id, state in states.items():
        state["task_id"] = task_id
        result = grade_episode(state)
        results[task_id] = result
        total_score += result["score"]

    avg_score = total_score / len(states) if states else 0.0
    return {
        "task_results": results,
        "average_score": round(avg_score, 4),
        "tasks_passed": sum(1 for r in results.values() if r["passed"]),
        "total_tasks": len(results),
    }

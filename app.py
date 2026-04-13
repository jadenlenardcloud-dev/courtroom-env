"""
Supply Chain OpenEnv — FastAPI Server
Exposes the OpenEnv HTTP API for remote agent interaction.
"""

from __future__ import annotations
import uuid
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env.environment import SupplyChainEnv
from env.models import AgentAction, ActionType, EnvironmentObservation
from tasks.graders import grade_episode, TASK_REGISTRY


app = FastAPI(
    title="Supply Chain Disruption Management — OpenEnv",
    description="An OpenEnv-compliant RL environment for real-world supply chain crisis management.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session store (in-memory; for production use Redis)
_sessions: Dict[str, Dict] = {}


# ─────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: str = "task_easy"


class ResetResponse(BaseModel):
    session_id: str
    task_id: str
    observation: EnvironmentObservation


class StepRequest(BaseModel):
    session_id: str
    action: AgentAction


class StepResponse(BaseModel):
    observation: EnvironmentObservation
    reward: float
    done: bool
    info: dict


class StateResponse(BaseModel):
    session_id: str
    observation: EnvironmentObservation


class GradeRequest(BaseModel):
    session_id: str


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "name": "Supply Chain Disruption Management OpenEnv",
        "version": "1.0.0",
        "tasks": list(TASK_REGISTRY.keys()),
        "endpoints": ["/reset", "/step", "/state", "/grade", "/tasks", "/health"],
    }


@app.get("/health")
def health():
    return {"status": "ok", "active_sessions": len(_sessions)}


@app.get("/tasks")
def list_tasks():
    return {
        tid: {
            "name": spec.name,
            "difficulty": spec.difficulty,
            "description": spec.description,
            "max_steps": spec.max_steps,
            "budget_usd": spec.budget_usd,
            "pass_threshold": spec.reward_threshold_pass,
        }
        for tid, spec in TASK_REGISTRY.items()
    }


@app.post("/reset", response_model=ResetResponse)
def reset(req: ResetRequest):
    if req.task_id not in TASK_REGISTRY:
        raise HTTPException(400, f"Unknown task_id. Valid: {list(TASK_REGISTRY.keys())}")

    session_id = str(uuid.uuid4())
    env = SupplyChainEnv()
    obs = env.reset(req.task_id)

    _sessions[session_id] = {
        "env": env,
        "task_id": req.task_id,
        "trajectory": [],
        "done": False,
    }

    return ResetResponse(session_id=session_id, task_id=req.task_id, observation=obs)


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    sess = _get_session(req.session_id)
    if sess["done"]:
        raise HTTPException(400, "Episode is done. Call /reset to start a new one.")

    result = sess["env"].step(req.action)

    sess["trajectory"].append({
        "step": result.observation.step,
        "action": req.action.action_type,
        "target_id": req.action.target_id,
        "reasoning": req.action.reasoning,
        "reward": result.reward,
        "events": result.info.get("events", []),
    })

    if result.done:
        sess["done"] = True

    return StepResponse(
        observation=result.observation,
        reward=result.reward,
        done=result.done,
        info=result.info,
    )


@app.get("/state/{session_id}", response_model=StateResponse)
def state(session_id: str):
    sess = _get_session(session_id)
    obs = sess["env"].state()
    return StateResponse(session_id=session_id, observation=obs)


@app.post("/grade")
def grade(req: GradeRequest):
    sess = _get_session(req.session_id)
    if not sess["done"]:
        raise HTTPException(400, "Episode not yet complete. Keep stepping.")

    env: SupplyChainEnv = sess["env"]
    final_obs = env.state()
    ep_result = env.get_episode_result()
    scores = grade_episode(sess["task_id"], sess["trajectory"], final_obs, ep_result)

    threshold = TASK_REGISTRY[sess["task_id"]].reward_threshold_pass
    return {
        "session_id": req.session_id,
        "task_id": sess["task_id"],
        "scores": scores,
        "passed": scores["total"] >= threshold,
        "pass_threshold": threshold,
        "steps": final_obs.step,
        "sla_breaches": final_obs.sla_breach_count,
        "budget_spent_usd": ep_result.financial_loss_usd,
    }


def _get_session(session_id: str) -> Dict:
    sess = _sessions.get(session_id)
    if sess is None:
        raise HTTPException(404, f"Session '{session_id}' not found. Call /reset first.")
    return sess

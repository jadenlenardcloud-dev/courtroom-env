"""
FastAPI server for the Courtroom Argument Simulator.
Exposes the OpenEnv interface over HTTP for Hugging Face Spaces.

Endpoints:
  POST /reset          — Start a new episode
  POST /step           — Take an action
  GET  /state          — Get current state
  GET  /tasks          — List available tasks
  GET  /health         — Health check
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from environment import CourtroomEnvironment, Action, Observation, Reward
from grader import grade_episode


app = FastAPI(
    title="Courtroom Argument Simulator",
    description=(
        "An OpenEnv-compliant reinforcement learning environment simulating "
        "criminal defense proceedings. The agent acts as a defense attorney."
    ),
    version="1.0.0",
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (keyed by session_id)
_sessions: Dict[str, CourtroomEnvironment] = {}


# ── Request / Response Models ──────────────────────────────────────────────────

class ResetRequest(BaseModel):
    task_id: str = "task_easy"
    session_id: Optional[str] = None


class ResetResponse(BaseModel):
    session_id: str
    observation: Dict[str, Any]
    task_info: Dict[str, Any]


class StepRequest(BaseModel):
    session_id: str
    action_type: str
    content: str
    target: Optional[str] = None


class StepResponse(BaseModel):
    observation: Dict[str, Any]
    reward: Dict[str, Any]
    done: bool
    info: Dict[str, Any]
    grade: Optional[Dict[str, Any]] = None


class StateResponse(BaseModel):
    session_id: str
    state: Dict[str, Any]


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "environment": "courtroom-argument-simulator", "version": "1.0.0"}


@app.get("/tasks")
def list_tasks():
    """List all available tasks with metadata."""
    from tasks import TASKS
    return {
        task_id: {
            "name": t["name"],
            "difficulty": t["difficulty"],
            "description": t["description"],
            "charge": t["charge"],
            "max_turns": t["max_turns"],
            "target_score": t["target_score"],
        }
        for task_id, t in TASKS.items()
    }


@app.post("/reset", response_model=ResetResponse)
def reset(req: ResetRequest):
    """Initialize or restart an episode for a given task."""
    session_id = req.session_id or str(uuid.uuid4())

    try:
        env = CourtroomEnvironment(task_id=req.task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    obs = env.reset()
    _sessions[session_id] = env

    from tasks import TASKS
    task_def = TASKS[req.task_id]

    return ResetResponse(
        session_id=session_id,
        observation=obs.model_dump(),
        task_info={
            "task_id": req.task_id,
            "name": task_def["name"],
            "difficulty": task_def["difficulty"],
            "charge": task_def["charge"],
            "max_turns": task_def["max_turns"],
            "target_score": task_def["target_score"],
        },
    )


@app.post("/step", response_model=StepResponse)
def step(req: StepRequest):
    """Take one action in the environment."""
    env = _sessions.get(req.session_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Session '{req.session_id}' not found. Call /reset first.")

    action = Action(
        action_type=req.action_type,
        content=req.content,
        target=req.target,
    )

    try:
        obs, reward, done, info = env.step(action)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    grade = None
    if done:
        final_state = env.state()
        grade = grade_episode(final_state)

    return StepResponse(
        observation=obs.model_dump(),
        reward=reward.model_dump(),
        done=done,
        info=info,
        grade=grade,
    )


@app.get("/state/{session_id}", response_model=StateResponse)
def get_state(session_id: str):
    """Get the full internal state of an active session."""
    env = _sessions.get(session_id)
    if env is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")

    return StateResponse(session_id=session_id, state=env.state())


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    """Clean up a session."""
    if session_id in _sessions:
        del _sessions[session_id]
        return {"deleted": session_id}
    raise HTTPException(status_code=404, detail="Session not found.")

"""
FastAPI server for the Courtroom Argument Simulator.
OpenEnv-compliant HTTP interface for Hugging Face Spaces.

Endpoints:
  POST /reset          — Start a new episode (body optional)
  POST /step           — Take an action
  GET  /state          — Get current state
  GET  /tasks          — List available tasks
  GET  /health         — Health check
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    task_id: Optional[str] = "task_easy"
    session_id: Optional[str] = None


class ResetResponse(BaseModel):
    session_id: str
    observation: Dict[str, Any]
    task_info: Dict[str, Any]


class StepRequest(BaseModel):
    session_id: Optional[str] = None
    action_type: Optional[str] = "present_argument"
    content: Optional[str] = "The defense argues for the client's innocence."
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
    return {
        "status": "ok",
        "environment": "courtroom-argument-simulator",
        "version": "1.0.0",
    }


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


@app.post("/reset")
async def reset(request: Request):
    """
    Initialize or restart an episode.
    Body is OPTIONAL — calling with no body starts task_easy with a new session.
    Body fields (all optional):
      task_id    : "task_easy" | "task_medium" | "task_hard"  (default: task_easy)
      session_id : string  (default: auto-generated UUID)
    """
    # Safely parse body — works with no body, empty body, or full JSON body
    task_id = "task_easy"
    session_id = None

    try:
        body_bytes = await request.body()
        if body_bytes:
            import json
            body = json.loads(body_bytes)
            task_id = body.get("task_id", "task_easy") or "task_easy"
            session_id = body.get("session_id", None)
    except Exception:
        pass  # No body or invalid JSON — use defaults

    session_id = session_id or str(uuid.uuid4())

    try:
        env = CourtroomEnvironment(task_id=task_id)
    except ValueError as e:
        return JSONResponse(status_code=400, content={"detail": str(e)})

    obs = env.reset()
    _sessions[session_id] = env

    from tasks import TASKS
    task_def = TASKS[task_id]

    return {
        "session_id": session_id,
        "observation": obs.model_dump(),
        "task_info": {
            "task_id": task_id,
            "name": task_def["name"],
            "difficulty": task_def["difficulty"],
            "charge": task_def["charge"],
            "max_turns": task_def["max_turns"],
            "target_score": task_def["target_score"],
        },
    }


@app.post("/step")
async def step(request: Request):
    """
    Take one action in the environment.
    Body fields:
      session_id  : string (from /reset response)
      action_type : string (e.g. "present_argument")
      content     : string (the argument text)
      target      : string | null (evidence_id or witness_id)
    """
    session_id = None
    action_type = "present_argument"
    content = "The defense argues for the client's innocence."
    target = None

    try:
        body_bytes = await request.body()
        if body_bytes:
            import json
            body = json.loads(body_bytes)
            session_id = body.get("session_id", None)
            action_type = body.get("action_type", "present_argument") or "present_argument"
            content = body.get("content", content) or content
            target = body.get("target", None)
    except Exception:
        pass

    # If no session_id provided, auto-create one for the checker
    if not session_id or session_id not in _sessions:
        env = CourtroomEnvironment(task_id="task_easy")
        env.reset()
        session_id = session_id or str(uuid.uuid4())
        _sessions[session_id] = env

    env = _sessions[session_id]

    action = Action(
        action_type=action_type,
        content=content,
        target=target,
    )

    try:
        obs, reward, done, info = env.step(action)
    except RuntimeError:
        # Episode done — auto-reset for checker convenience
        env.reset()
        obs, reward, done, info = env.step(action)
    except ValueError as e:
        return JSONResponse(status_code=422, content={"detail": str(e)})

    grade = None
    if done:
        final_state = env.state()
        grade = grade_episode(final_state)

    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info,
        "grade": grade,
    }


@app.get("/state/{session_id}")
def get_state(session_id: str):
    """Get the full internal state of an active session."""
    env = _sessions.get(session_id)
    if env is None:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Session '{session_id}' not found."}
        )
    return {"session_id": session_id, "state": env.state()}


@app.delete("/session/{session_id}")
def delete_session(session_id: str):
    """Clean up a session."""
    if session_id in _sessions:
        del _sessions[session_id]
        return {"deleted": session_id}
    return JSONResponse(status_code=404, content={"detail": "Session not found."})

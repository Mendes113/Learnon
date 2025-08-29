"""
Education API endpoints for Archon (educational workflows).

Endpoints:
- POST /api/education/processes: start a new process
- POST /api/education/processes/{id}/advance: advance current step with optional user input
- GET  /api/education/processes/{id}: get process state
- GET  /api/education/processes: list active processes for a user (in-memory)
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config.logfire_config import get_logger
from ..services.education.orchestrator import orchestrator
from ..services.education.session_service import EducationSessionService

logger = get_logger(__name__)

router = APIRouter(prefix="/api/education", tags=["education"])


class StartProcessRequest(BaseModel):
    user_id: str
    topic: str
    process_type: str = "fundamental_explanation"


class AdvanceProcessRequest(BaseModel):
    user_input: str | None = None


@router.post("/processes")
async def start_process(req: StartProcessRequest):
    try:
        inst = orchestrator.start_process(req.user_id, req.topic, req.process_type)
        return {
            "success": True,
            "process_id": inst.id,
            "process_type": inst.process_type,
            "steps": [str(s) for s in inst.steps],
            "current_step": str(inst.current_step()),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start education process: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/processes/{process_id}")
async def get_process(process_id: str):
    inst = orchestrator.get_process(process_id)
    if not inst:
        raise HTTPException(status_code=404, detail="process_not_found")
    return {
        "success": True,
        "process_id": inst.id,
        "process_type": str(inst.process_type),
        "topic": inst.topic,
        "steps": [str(s) for s in inst.steps],
        "current_index": inst.current_index,
        "current_step": str(inst.current_step()) if not inst.is_complete() else None,
        "completed": inst.is_complete(),
        "history": [
            {
                "step": str(h.step),
                "content": h.content,
                "context": h.context,
                "created_at": h.created_at,
            }
            for h in inst.history
        ],
    }


@router.post("/processes/{process_id}/advance")
async def advance_process(process_id: str, req: AdvanceProcessRequest):
    try:
        result = await orchestrator.advance(process_id, req.user_input)
        if not result.get("success"):
            if result.get("error") == "process_not_found":
                raise HTTPException(status_code=404, detail="process_not_found")
            raise HTTPException(status_code=400, detail=result)

        payload: dict[str, Any] = {
            "success": True,
            "completed": result.get("completed", False),
        }

        step_result = result.get("result")
        if step_result:
            payload["step_result"] = {
                "step": str(step_result.step),
                "content": step_result.content,
                "context": step_result.context,
                "created_at": step_result.created_at,
            }
        return payload
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to advance education process: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})


@router.get("/processes")
async def list_processes(user_id: str | None = None):
    service = EducationSessionService()
    ok, res = service.list_sessions(user_id=user_id)
    if not ok:
        raise HTTPException(status_code=500, detail=res)
    processes = []
    for inst in res.get("sessions", []):
        processes.append(
            {
                "process_id": inst.id,
                "user_id": inst.user_id,
                "topic": inst.topic,
                "process_type": str(inst.process_type),
                "current_index": inst.current_index,
                "completed": inst.is_complete(),
            }
        )
    return {"success": True, "count": len(processes), "processes": processes}


class SuggestNextStepRequest(BaseModel):
    score: float | None = None
    apply: bool | None = False


@router.post("/processes/{process_id}/suggest-next-step")
async def suggest_next_step(process_id: str, req: SuggestNextStepRequest):
    try:
        result = orchestrator.suggest_next_step(process_id, score=req.score, apply=bool(req.apply))
        if not result.get("success"):
            if result.get("error") == "process_not_found":
                raise HTTPException(status_code=404, detail="process_not_found")
            raise HTTPException(status_code=400, detail=result)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to suggest next step: {e}")
        raise HTTPException(status_code=500, detail={"error": str(e)})

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, List

from supabase import Client

from ...utils import get_supabase_client
from .models import ProcessInstance, ProcessType, StepResult, StepType


class EducationSessionService:
    """Persistence layer for education sessions backed by Supabase."""

    def __init__(self, supabase_client: Client | None = None) -> None:
        self.supabase_client = supabase_client or get_supabase_client()

    # ---- Serialization helpers ----
    def _serialize_instance(self, inst: ProcessInstance) -> dict[str, Any]:
        return {
            "id": inst.id,
            "user_id": inst.user_id,
            "topic": inst.topic,
            "process_type": str(inst.process_type),
            "steps": [str(s) for s in inst.steps],
            "current_index": inst.current_index,
            "history": [
                {
                    "step": str(h.step),
                    "content": h.content,
                    "context": h.context,
                    "created_at": h.created_at,
                }
                for h in inst.history
            ],
            "created_at": inst.created_at,
            "updated_at": datetime.now().isoformat(),
        }

    def _deserialize_instance(self, row: dict[str, Any]) -> ProcessInstance:
        history: List[StepResult] = []
        for h in (row.get("history") or []):
            history.append(
                StepResult(
                    step=StepType(h.get("step")),
                    content=h.get("content", ""),
                    context=h.get("context") or {},
                    created_at=h.get("created_at") or datetime.now().isoformat(),
                )
            )
        steps = [StepType(s) for s in (row.get("steps") or [])]
        return ProcessInstance(
            id=row["id"],
            user_id=row["user_id"],
            topic=row["topic"],
            process_type=ProcessType(row["process_type"]),
            steps=steps,
            current_index=row.get("current_index", 0),
            history=history,
            created_at=row.get("created_at") or datetime.now().isoformat(),
            updated_at=row.get("updated_at") or datetime.now().isoformat(),
        )

    # ---- CRUD operations ----
    def create_session(self, instance: ProcessInstance) -> tuple[bool, dict[str, Any]]:
        payload = self._serialize_instance(instance)
        try:
            resp = self.supabase_client.table("education_sessions").insert(payload).execute()
            if resp.data:
                return True, {"session": self._deserialize_instance(resp.data[0])}
            return False, {"error": "failed_to_insert"}
        except Exception as e:
            return False, {"error": str(e)}

    def get_session(self, session_id: str) -> tuple[bool, dict[str, Any]]:
        try:
            resp = (
                self.supabase_client.table("education_sessions").select("*").eq("id", session_id).limit(1).execute()
            )
            if resp.data:
                return True, {"session": self._deserialize_instance(resp.data[0])}
            return False, {"error": "not_found"}
        except Exception as e:
            return False, {"error": str(e)}

    def save_session(self, instance: ProcessInstance) -> tuple[bool, dict[str, Any]]:
        payload = self._serialize_instance(instance)
        try:
            resp = (
                self.supabase_client.table("education_sessions")
                .update(payload)
                .eq("id", instance.id)
                .execute()
            )
            if resp.data:
                return True, {"session": self._deserialize_instance(resp.data[0])}
            return False, {"error": "update_failed"}
        except Exception as e:
            return False, {"error": str(e)}

    def list_sessions(self, user_id: str | None = None, limit: int = 100) -> tuple[bool, dict[str, Any]]:
        try:
            query = self.supabase_client.table("education_sessions").select("*").order("updated_at", desc=True)
            if user_id:
                query = query.eq("user_id", user_id)
            if limit:
                query = query.limit(limit)
            resp = query.execute()
            sessions = [self._deserialize_instance(row) for row in (resp.data or [])]
            return True, {"sessions": sessions, "count": len(sessions)}
        except Exception as e:
            return False, {"error": str(e)}


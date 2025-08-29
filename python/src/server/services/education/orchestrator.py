from __future__ import annotations

import uuid
from typing import Any

from ..search.rag_service import RAGService
from ..projects.progress_service import progress_service
from .models import ProcessInstance, ProcessType, StepResult, StepType
from .workflows import get_workflow
from .session_service import EducationSessionService


class EducationOrchestrator:
    """
    Orchestrates pedagogical processes using predefined workflows and RAG context.
    Persists sessions in Supabase via EducationSessionService.
    """

    def __init__(self):
        self.rag = RAGService()
        self.sessions = EducationSessionService()

    def start_process(self, user_id: str, topic: str, process_type: str) -> ProcessInstance:
        ptype = ProcessType(process_type)
        steps = get_workflow(ptype)
        pid = str(uuid.uuid4())
        instance = ProcessInstance(
            id=pid,
            user_id=user_id,
            topic=topic,
            process_type=ptype,
            steps=steps,
        )

        # Persist session
        self.sessions.create_session(instance)

        # Fire initial progress event
        try:
            progress_service.start_operation(pid, "education_process", {"topic": topic, "step": str(steps[0])})
        except Exception:
            pass
        return instance

    def get_process(self, process_id: str) -> ProcessInstance | None:
        ok, res = self.sessions.get_session(process_id)
        if not ok:
            return None
        return res["session"]

    async def advance(self, process_id: str, user_input: str | None = None) -> dict[str, Any]:
        ok, res = self.sessions.get_session(process_id)
        if not ok:
            return {"success": False, "error": "process_not_found"}
        instance: ProcessInstance = res["session"]

        if instance.is_complete():
            return {"success": True, "completed": True, "instance": instance}

        step = instance.current_step()

        # Retrieve supporting context via RAG
        context_chunks = []
        try:
            query = f"{instance.topic} — etapa: {step}"
            context_chunks = await self.rag.search_documents(query=query, match_count=5)
        except Exception:
            context_chunks = []

        # Build content per step (simple placeholder logic for now)
        score: float | None = None
        if step == StepType.explain:
            content = f"Explicação do tópico '{instance.topic}' com base em fontes relevantes."
        elif step == StepType.example:
            content = f"Exemplo prático sobre '{instance.topic}'."
        elif step == StepType.exercise:
            content = f"Exercício proposto: resolva um problema relacionado a '{instance.topic}'."
        elif step == StepType.evaluate:
            # In real impl, analyze user_input
            score = 1.0 if user_input else 0.5
            content = f"Avaliação da resposta: score={score:.2f}."
        elif step == StepType.feedback:
            content = "Feedback objetivo e próximos passos."
        else:
            content = ""

        context = {"citations": context_chunks, "user_input": user_input}
        if score is not None:
            context["score"] = score

        result = StepResult(step=step, content=content, context=context)

        instance.history.append(result)
        instance.current_index += 1

        # Persist update
        self.sessions.save_session(instance)

        # Broadcast progress update
        try:
            await progress_service.update_progress(
                process_id,
                {
                    "status": "in_progress" if not instance.is_complete() else "completed",
                    "step": str(step),
                    "percentage": int(100 * instance.current_index / max(len(instance.steps), 1)),
                    "log": f"Step {step} completed",
                },
            )
            if instance.is_complete():
                await progress_service.complete_operation(process_id, {"result": "ok"})
        except Exception:
            pass

        return {"success": True, "completed": instance.is_complete(), "result": result, "instance": instance}

    def suggest_next_step(self, process_id: str, score: float | None = None, apply: bool = False) -> dict[str, Any]:
        ok, res = self.sessions.get_session(process_id)
        if not ok:
            return {"success": False, "error": "process_not_found"}
        instance: ProcessInstance = res["session"]

        if instance.is_complete():
            return {"success": True, "completed": True, "suggestion": None}

        # Determine last known score if not provided
        last_score: float | None = score
        if last_score is None:
            for h in reversed(instance.history):
                if h.step == StepType.evaluate and isinstance(h.context.get("score"), (int, float)):
                    last_score = float(h.context["score"])
                    break

        # Default: proceed to the next planned step
        default_next: StepType | None = None
        if instance.current_index < len(instance.steps):
            default_next = instance.steps[instance.current_index]

        suggestion: StepType | None = default_next
        rationale = "Progredir conforme o fluxo padrão."
        confidence = 0.6

        if last_score is not None:
            if last_score < 0.6:
                # Go back to reinforce with explain or example
                suggestion = StepType.explain if StepType.explain in instance.steps else StepType.example
                rationale = f"Desempenho baixo (score={last_score:.2f}); reforçar explicação/exemplo."
                confidence = 0.8
            elif last_score < 0.85:
                suggestion = StepType.exercise
                rationale = f"Desempenho razoável (score={last_score:.2f}); praticar com novo exercício."
                confidence = 0.7
            else:
                suggestion = StepType.feedback
                rationale = f"Desempenho alto (score={last_score:.2f}); consolidar com feedback e concluir."
                confidence = 0.75

        applied = False
        if apply and suggestion is not None:
            # Insert suggestion at current index so it becomes the next step
            instance.steps = (
                instance.steps[: instance.current_index]
                + [suggestion]
                + instance.steps[instance.current_index :]
            )
            self.sessions.save_session(instance)
            applied = True

        return {
            "success": True,
            "completed": instance.is_complete(),
            "suggestion": str(suggestion) if suggestion else None,
            "rationale": rationale,
            "confidence": confidence,
            "applied": applied,
        }


# Singleton orchestrator
orchestrator = EducationOrchestrator()

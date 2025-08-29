from __future__ import annotations

from .models import ProcessType, StepType


DEFAULT_WORKFLOWS: dict[ProcessType, list[StepType]] = {
    ProcessType.fundamental_explanation: [
        StepType.explain,
        StepType.example,
        StepType.exercise,
        StepType.evaluate,
        StepType.feedback,
    ],
    ProcessType.guided_practice: [
        StepType.example,
        StepType.exercise,
        StepType.feedback,
    ],
    ProcessType.assessment: [
        StepType.exercise,
        StepType.evaluate,
        StepType.feedback,
    ],
}


def get_workflow(process_type: ProcessType) -> list[StepType]:
    return DEFAULT_WORKFLOWS.get(process_type, DEFAULT_WORKFLOWS[ProcessType.fundamental_explanation])


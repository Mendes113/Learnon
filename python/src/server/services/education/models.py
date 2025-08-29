from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, List, Optional


class ProcessType(str, Enum):
    fundamental_explanation = "fundamental_explanation"
    guided_practice = "guided_practice"
    assessment = "assessment"


class StepType(str, Enum):
    explain = "explain"
    example = "example"
    exercise = "exercise"
    evaluate = "evaluate"
    feedback = "feedback"


@dataclass
class StepResult:
    step: StepType
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ProcessInstance:
    id: str
    user_id: str
    topic: str
    process_type: ProcessType
    steps: List[StepType]
    current_index: int = 0
    history: List[StepResult] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def current_step(self) -> StepType:
        return self.steps[self.current_index]

    def is_complete(self) -> bool:
        return self.current_index >= len(self.steps)


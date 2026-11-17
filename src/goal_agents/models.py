from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    REVIEW = "review"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Task:
    title: str
    description: str
    role: str = "researcher"
    id: str = field(default_factory=lambda: str(uuid4())[:8])
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    output: str = ""
    review: str = ""

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass
class GoalState:
    goal: str
    success_criteria: list[str]
    tasks: list[Task] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    final_answer: str = ""
    completed: bool = False

    def log(self, event: str, **data: Any) -> None:
        self.events.append({"event": event, **data})

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "success_criteria": self.success_criteria,
            "tasks": [task.to_dict() for task in self.tasks],
            "events": self.events,
            "final_answer": self.final_answer,
            "completed": self.completed,
        }

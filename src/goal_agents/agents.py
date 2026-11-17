from __future__ import annotations

import json
import re
from dataclasses import dataclass

from .llm import LLM
from .models import GoalState, Task


def parse_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"Model did not return JSON: {text[:160]}")
    return json.loads(match.group())


@dataclass
class PlannerAgent:
    llm: LLM

    def plan(self, state: GoalState) -> list[Task]:
        result = self.llm.complete(
            "PLANNER_JSON: You decompose goals. Return only JSON: "
            '{"tasks":[{"title":"...","description":"...","role":"..."}]}. Use 2-6 tasks.',
            f"Goal: {state.goal}\nSuccess criteria: {state.success_criteria}",
        )
        items = parse_json(result).get("tasks", [])
        if not items:
            raise ValueError("Planner returned no tasks")
        return [Task(title=x["title"], description=x["description"], role=x.get("role", "specialist")) for x in items]


@dataclass
class WorkerAgent:
    llm: LLM

    def execute(self, task: Task, state: GoalState) -> str:
        context = "\n\n".join(f"{t.title}: {t.output}" for t in state.tasks if t.output)
        return self.llm.complete(
            f"You are the {task.role} agent. Produce a concrete, concise deliverable for your assigned task.",
            f"Overall goal: {state.goal}\nTask: {task.title}\nInstructions: {task.description}\nPrior work:\n{context}",
        )


@dataclass
class ReviewerAgent:
    llm: LLM

    def review(self, task: Task, state: GoalState) -> tuple[bool, str]:
        result = self.llm.complete(
            "REVIEW_JSON: You are a strict reviewer. Return only JSON: "
            '{"approved":true,"feedback":"..."}.',
            f"Goal: {state.goal}\nCriteria: {state.success_criteria}\nTask: {task.description}\nOutput: {task.output}",
        )
        payload = parse_json(result)
        return bool(payload.get("approved")), str(payload.get("feedback", ""))


@dataclass
class SynthesizerAgent:
    llm: LLM

    def synthesize(self, state: GoalState) -> str:
        work = "\n\n".join(f"## {t.title}\n{t.output}" for t in state.tasks)
        return self.llm.complete(
            "SYNTHESIZER: Combine the agents' work into a final answer that directly achieves the goal.",
            f"Goal: {state.goal}\nSuccess criteria: {state.success_criteria}\nAgent work:\n{work}",
        )

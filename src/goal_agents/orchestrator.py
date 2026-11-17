from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from .agents import PlannerAgent, ReviewerAgent, SynthesizerAgent, WorkerAgent
from .llm import LLM
from .models import GoalState, Task, TaskStatus


class Orchestrator:
    def __init__(self, llm: LLM, max_attempts: int = 2, concurrency: int = 3) -> None:
        self.planner = PlannerAgent(llm)
        self.worker = WorkerAgent(llm)
        self.reviewer = ReviewerAgent(llm)
        self.synthesizer = SynthesizerAgent(llm)
        self.max_attempts = max_attempts
        self.concurrency = concurrency

    def run(self, goal: str, criteria: list[str], state_path: Path | None = None) -> GoalState:
        state = GoalState(goal=goal, success_criteria=criteria)
        state.log("goal_created", goal=goal)
        state.tasks = self.planner.plan(state)
        state.log("plan_created", task_count=len(state.tasks))
        self._save(state, state_path)

        pending = list(state.tasks)
        while pending:
            with ThreadPoolExecutor(max_workers=self.concurrency) as pool:
                futures = {pool.submit(self._execute, task, state): task for task in pending}
                for future in as_completed(futures):
                    task = futures[future]
                    try:
                        task.output = future.result()
                        task.status = TaskStatus.REVIEW
                        approved, feedback = self.reviewer.review(task, state)
                        task.review = feedback
                        task.status = TaskStatus.DONE if approved else TaskStatus.PENDING
                        state.log("task_reviewed", task_id=task.id, approved=approved, feedback=feedback)
                    except Exception as exc:
                        task.review = str(exc)
                        task.status = TaskStatus.PENDING
                        state.log("task_error", task_id=task.id, error=str(exc))
                    if task.status == TaskStatus.PENDING and task.attempts >= self.max_attempts:
                        task.status = TaskStatus.FAILED
                    self._save(state, state_path)
            pending = [task for task in state.tasks if task.status == TaskStatus.PENDING]

        failures = [task for task in state.tasks if task.status == TaskStatus.FAILED]
        if failures:
            state.log("goal_failed", failed_tasks=[task.id for task in failures])
        else:
            state.final_answer = self.synthesizer.synthesize(state)
            state.completed = True
            state.log("goal_completed")
        self._save(state, state_path)
        return state

    def _execute(self, task: Task, state: GoalState) -> str:
        task.status = TaskStatus.RUNNING
        task.attempts += 1
        state.log("task_started", task_id=task.id, attempt=task.attempts)
        return self.worker.execute(task, state)

    @staticmethod
    def _save(state: GoalState, path: Path | None) -> None:
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

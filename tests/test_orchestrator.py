import tempfile
import unittest
from pathlib import Path

from goal_agents.llm import MockLLM
from goal_agents.models import TaskStatus
from goal_agents.orchestrator import Orchestrator


class OrchestratorTest(unittest.TestCase):
    def test_workflow_completes_and_persists(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "state.json"
            state = Orchestrator(MockLLM()).run("制定发布计划", ["有明确步骤"], target)

            self.assertTrue(state.completed)
            self.assertEqual(len(state.tasks), 3)
            self.assertTrue(all(task.status == TaskStatus.DONE for task in state.tasks))
            self.assertTrue(target.exists())
            self.assertIn("goal_completed", target.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import argparse
from pathlib import Path

from .llm import MockLLM, OpenAICompatibleLLM
from .orchestrator import Orchestrator


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a goal-driven multi-agent workflow")
    parser.add_argument("goal", help="The outcome the agent team should achieve")
    parser.add_argument("--criteria", action="append", default=[], help="Success criterion (repeatable)")
    parser.add_argument("--provider", choices=["mock", "openai"], default="mock")
    parser.add_argument("--model")
    parser.add_argument("--state", type=Path, default=Path("run-state.json"))
    args = parser.parse_args()

    llm = MockLLM() if args.provider == "mock" else OpenAICompatibleLLM(model=args.model)
    criteria = args.criteria or ["输出具体且可执行", "覆盖目标的主要约束"]
    state = Orchestrator(llm).run(args.goal, criteria, args.state)
    if state.completed:
        print(state.final_answer)
    else:
        raise SystemExit(f"Goal failed. Inspect {args.state}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Protocol


class LLM(Protocol):
    def complete(self, system: str, prompt: str) -> str: ...


class OpenAICompatibleLLM:
    """Tiny dependency-free adapter for OpenAI-compatible chat APIs."""

    def __init__(self, model: str | None = None, base_url: str | None = None) -> None:
        self.api_key = os.environ.get("OPENAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required when provider=openai")
        self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
        self.base_url = (base_url or os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")

    def complete(self, system: str, prompt: str) -> str:
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }).encode()
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                payload = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace")
            raise RuntimeError(f"LLM request failed ({exc.code}): {detail}") from exc
        return payload["choices"][0]["message"]["content"]


class MockLLM:
    """Deterministic local model for demos and tests."""

    def complete(self, system: str, prompt: str) -> str:
        if "PLANNER_JSON" in system:
            return json.dumps({"tasks": [
                {"title": "分析目标", "description": "澄清约束、受众和验收标准", "role": "analyst"},
                {"title": "制定方案", "description": "基于分析形成可执行方案", "role": "strategist"},
                {"title": "验证结果", "description": "检查遗漏、风险和成功标准", "role": "reviewer"},
            ]}, ensure_ascii=False)
        if "REVIEW_JSON" in system:
            return json.dumps({"approved": True, "feedback": "结果满足任务要求。"}, ensure_ascii=False)
        if "SYNTHESIZER" in system:
            return "目标已完成。\n\n" + prompt[-1200:]
        return f"已完成该子任务。\n\n输入摘要：{prompt[-500:]}"

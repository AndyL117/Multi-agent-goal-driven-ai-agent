# Goal Agents

一个小而完整的目标驱动多智能体编排器。它将高层目标拆为子任务，让不同角色并发执行，经过独立评审后汇总最终答案，并把全过程持久化为可审计状态。

## 架构

```text
Goal → Planner → [Analyst | Strategist | Specialist] → Reviewer → Synthesizer
                    ↖──────── retry on rejection ────────↙
```

- **Planner**：将目标和成功标准拆成 2–6 个角色任务
- **Worker**：按角色并行执行子任务
- **Reviewer**：用结构化质量门禁决定通过或重试
- **Synthesizer**：汇总已通过产物，形成最终答案
- **Shared state**：记录任务状态、尝试次数、评审意见和事件日志

## 快速开始

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .

# 离线演示，不需要 API Key
goal-agents "为新产品制定两周发布计划" \
  --criteria "包含负责人和里程碑" \
  --criteria "列出主要风险"
```

使用 OpenAI 兼容接口：

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-4.1-mini"
goal-agents "分析客户流失并提出改进方案" --provider openai
```

如使用其他兼容服务，可设置 `OPENAI_BASE_URL`。每次运行会生成 `run-state.json`，便于恢复能力、Web UI、人工审批和长期记忆等后续扩展。

## 测试

```bash
python -m unittest discover -s tests -v
```

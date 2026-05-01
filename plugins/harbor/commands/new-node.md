---
description: Add a node to a Harbor graph (DSPy module / ML model / tool call / retrieval / sub-graph)
argument-hint: <graph> <node-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Node

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md`.

## Interview

1. **Type?** (dspy:Predict | dspy:ChainOfThought | dspy:ReAct | model:onnx | tool:<name> | retrieval:<store> | subgraph:<graph>)
2. **Inputs?** (state fields read)
3. **Outputs?** (state fields written; mark which are annotated)
4. **Annotated outputs to mirror?**

## Delegate

Task tool → `node-builder`.

## Report

Updated graph hash; if changed, warn that existing checkpoints need migrate block.

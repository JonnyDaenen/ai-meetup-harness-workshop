# 05: Watch the context grow (stretch)

Goal: see why long agent sessions get slow and expensive, then fix it with compaction.

Start from your exercise 04 agent or a copy of `agent/j5_02_tools.py`.

## Part A: measure

1. After each model call, print `response.usage.input_tokens` and the number of messages in the history.
2. Give the agent a task that reads a few files ("summarise every README in this repo"). Watch the numbers climb.
3. In the proxy, find the biggest request. What is taking up the space: tool results, the system prompt or your own messages?

## Part B: compact

Add a `/compact` command:

1. Send the current history to the model with the instruction "Summarise this conversation for yourself: goals, decisions, files touched, open TODOs."
2. Replace the history with a single user message: `"Summary of the conversation so far: ..."`.
3. Compare `input_tokens` on the next call before and after.

## Part C: automatic

- Compact automatically when `input_tokens` passes a threshold (say 20k, or less on a small local model).
- Cheaper alternative: replace old `tool_result` contents with `"(output removed)"` and keep the last N turns intact. What do you lose?

## Think about

- Look for `cache_control` in [`proxy/captures/02_first_turn.json`](../../proxy/captures/02_first_turn.json). Prompt caching makes a repeated *prefix* cheap. Why does compaction break the cache, and when is it still worth it?
- Context also sets the speed on a local model: every token has to be processed before the first output token appears.

Upstream: [s08_context_compact](https://github.com/shareAI-lab/learn-claude-code/tree/main/s08_context_compact)

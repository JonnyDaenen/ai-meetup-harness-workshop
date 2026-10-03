# 02: Add a tool loop

Goal: turn a chatbot into an agent. Give the model a `bash` tool and keep calling it until it stops asking for tools.

```
messages ──▶ model ──▶ stop_reason == "tool_use"? ──no──▶ done
                ▲                  │yes
                └── tool_result ◀── run the command
```

Starter: [`starter.py`](starter.py), which is `j5_00` with `TODO 1`–`TODO 4`. Solution: [`agent/j5_01_bash.py`](../../agent/j5_01_bash.py).

```bash
uv run --project agent python exercises/02-add-a-tool-loop/starter.py
```

## Steps

1. **TODO 1: define the tool.** Add a `bash` entry to `TOOLS`. Send it (TODO 3) and look in the proxy: the schema goes to the model as-is. The description is a prompt too.
2. **Run it once.** Ask "what files are in this folder?" Look at the response in the proxy: `stop_reason` is `tool_use`, and there's a `tool_use` block with an `id` and an `input`. Nothing ran yet, because the model can only *ask*.
3. **TODO 2: implement `run_bash`.** Ask y/n before running. Return stdout and stderr together, capped in size.
4. **TODO 4: write the loop.** Append the assistant message, run every `tool_use` block, then send **one user message** with all the `tool_result`s and call the model again.
5. **Test it:** "how many Python files are in this repo, and which is the longest?" Count the model calls in the proxy for that one question.

## Check yourself

- What happens if a `tool_result`'s `tool_use_id` doesn't match the `tool_use` block's `id`? Try it.
- What does the model do when you answer `n`? Read the next request in the proxy to see what it was told.
- The blocklist in the solution checks substrings (`"rm -rf"`). Find a command that gets past it. Exercise 04 fixes this properly.

Upstream: [s01_agent_loop](https://github.com/shareAI-lab/learn-claude-code/tree/main/s01_agent_loop)

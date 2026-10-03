# J5: a minimal coding agent

Three versions of the same agent. Each one adds one idea:

| File | Adds | About |
|---|---|---|
| [`j5_00_vanilla.py`](j5_00_vanilla.py) | A chat loop: the whole history goes to the model on every turn. No tools. | 225 lines |
| [`j5_01_bash.py`](j5_01_bash.py) | **The agent loop**: one `bash` tool, `while True` until `stop_reason != "tool_use"`, a y/n prompt before each command, and a naive blocklist | 275 lines |
| [`j5_02_tools.py`](j5_02_tools.py) | **A tool table** (`TOOL_HANDLERS`), plus `read_file`, `write_file` and `edit_file` sandboxed to the working folder with `safe_path()` | 345 lines |

Each version also:
- logs every call (messages and response) to `.j5/history/<date>/<time>/<session>/callNNNN.log`
- tracks input and output tokens, call count, time and an estimated cost; the summary prints when you quit
- supports `/clear`, `/history` and `q`

## Run

From the repo root (so `.env` is found and `.j5/` lands there):

```bash
uv run --project agent python agent/j5_00_vanilla.py
DEBUG=1 uv run --project agent python agent/j5_01_bash.py      # print every request
AUTO_APPROVE=1 uv run --project agent python agent/j5_02_tools.py  # no y/n prompts (careful!)
```

> ⚠️ `j5_01` and `j5_02` run real shell commands on your machine. Read what you approve, or use the devcontainer.

## Credits

J5 is based on lessons s01 and s02 of [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code), MIT License, © 2024 shareAI Lab.

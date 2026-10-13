# J5: a minimal coding agent

Four versions of the same agent. Each one adds one idea. The first three come in two flavours with the same file names:

- [`mini/`](mini/): just the loop. No colours, logging, token tracking or commands. Start here to read the code.
- [`maxi/`](maxi/): the same loop plus the extras below. The exercises build on these.

| File | Adds | mini | maxi |
|---|---|---|---|
| `j5_00_vanilla.py` | A chat loop: the whole history goes to the model on every turn. No tools. | 18 lines | 225 lines |
| `j5_01_bash.py` | **The agent loop**: one `bash` tool, `while True` until `stop_reason != "tool_use"`, a y/n prompt before each command | 47 lines | 275 lines |
| `j5_02_tools.py` | **A tool table** (`TOOL_HANDLERS`), plus `read_file`, `write_file` and `edit_file` sandboxed to the working folder with `safe_path()` | 92 lines | 345 lines |
| `j5_03_mcp.py` | **Tools from an MCP server**: at startup J5 lists the server's tools and adds them to the tool table next to `bash`, so the model can call them like its own | — | 395 lines |

The maxi versions also:
- log every call (messages and response) to `.j5/history/<date>/<time>/<session>/callNNNN.log`
- track input and output tokens, call count, time and an estimated cost; the summary prints when you quit
- support `/clear`, `/history` and `q` (quit the mini versions with Ctrl-C)
- print every request with `DEBUG=1`
- block a few dangerous commands (`j5_01`, `j5_02`, `j5_03`), and skip the y/n prompts with `AUTO_APPROVE=1` (`j5_02`, `j5_03`)

## Run

From the repo root (so `.env` is found and `.j5/` lands there):

```bash
uv run --project agent python agent/mini/j5_00_vanilla.py
```

Swap `mini` for `maxi` and pick any of the files. The maxi extras:

```bash
DEBUG=1 uv run --project agent python agent/maxi/j5_01_bash.py          # print every request
AUTO_APPROVE=1 uv run --project agent python agent/maxi/j5_02_tools.py  # no y/n prompts (careful!)
```

`j5_03_mcp.py` needs an MCP server that speaks streamable HTTP and needs no login. J5 connects to `http://localhost:8000/mcp`, or to whatever `MCP_URL` says:

```bash
MCP_URL=http://localhost:8765/mcp uv run --project agent python agent/maxi/j5_03_mcp.py
```

Type `/tools` to see what the server offers. The proxy only shows the model traffic; the MCP calls go straight from J5 to the server.

> ⚠️ `j5_01`, `j5_02` and `j5_03` run real shell commands on your machine. Read what you approve, or use the devcontainer.

## Credits

J5 is based on lessons s01 and s02 of [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code), MIT License, © 2024 shareAI Lab.

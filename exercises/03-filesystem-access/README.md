# 03: File system access

Goal: give the agent dedicated file tools instead of making it do everything through `cat` and `sed`, and keep them inside the working folder.

Starter: [`starter.py`](starter.py), which is `j5_01` with `TODO 1`–`TODO 4`. Solution: [`agent/j5_02_tools.py`](../../agent/j5_02_tools.py).

```bash
uv run --project agent python exercises/03-filesystem-access/starter.py
```

## Steps

1. **TODO 1: describe `read_file`, `write_file` and `edit_file`** in `TOOLS`. Keep the descriptions short but precise. The model only knows what you tell it.
2. **TODO 2: build `TOOL_HANDLERS`**, a dict that maps each tool name to a function. Adding a tool is now one line in each table, and the loop stays the same.
3. **TODO 3: write `safe_path`.** Resolve the path and refuse anything outside the working folder.
4. **TODO 4: dispatch** through `TOOL_HANDLERS` in the loop, and return an error string for unknown tools.
5. **Test it:**
   - "Create `hello.py` that prints the date, then run it."
   - "Change it to print the time as well." Does it use `edit_file` or rewrite the whole file?
   - "Read `../../.env`." Does `safe_path` stop it?

## Check yourself

- Now ask it to show `.env` *using bash*. What does that tell you about sandboxing individual tools while `bash` has no limits? (This is why the [devcontainer](../../.devcontainer/devcontainer.json) exists.)
- `edit_file` replaces exact text. What happens when the model gets the whitespace slightly wrong, and how does it recover? Look in the proxy.
- In the proxy, compare the size of `tools` now with exercise 02. Every tool you add costs input tokens on **every** call.

Upstream: [s02_tool_use](https://github.com/shareAI-lab/learn-claude-code/tree/main/s02_tool_use)

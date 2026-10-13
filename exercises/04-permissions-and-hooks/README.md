# 04: Permissions and hooks (stretch)

Goal: replace "y/n before every call, plus a substring blocklist" with something you'd actually trust.

Start from a copy of `agent/maxi/j5_02_tools.py`:

```bash
cp agent/maxi/j5_02_tools.py exercises/04-permissions-and-hooks/my_agent.py
uv run --project agent python exercises/04-permissions-and-hooks/my_agent.py
```

## Part A: permission rules

1. Write a rules list that is checked in order, where the first match wins:
   ```python
   RULES = [
       ("deny",  "bash", r"\brm\b|\bsudo\b|curl .*\|\s*sh"),
       ("allow", "bash", r"^(ls|pwd|cat|head|wc|git status|git diff)\b"),
       ("allow", "read_file", r".*"),
       ("ask",   "*",    r".*"),          # default
   ]
   ```
2. `check_permission(name, inputs)` returns `"allow"`, `"deny"` or `"ask"`. Replace `_confirm_tool` with it.
3. When you deny, tell the model *why* in the `tool_result`, and watch in the proxy how it adapts.

## Part B: hooks

1. Add two hook lists: `PRE_TOOL_USE` and `POST_TOOL_USE`. Each hook is a function `(name, inputs[, output]) -> ...`.
2. Write a pre-hook that blocks writes to `*.env` and `.git/`, and a post-hook that logs every tool call to `.j5/audit.log`.
3. Write a post-hook that truncates long outputs and adds a note such as `"(truncated, 1234 more lines)"`.

## Think about

- Your bash regexes are easy to get around (`r''m`, `$(echo rm)`). Where does real safety have to come from? (Hint: the devcontainer.)
- Claude Code has a similar system ("permission modes" and hooks). How does a rule system change what you dare to auto-approve?

Upstream: [s03_permission](https://github.com/shareAI-lab/learn-claude-code/tree/main/s03_permission), [s04_hooks](https://github.com/shareAI-lab/learn-claude-code/tree/main/s04_hooks)

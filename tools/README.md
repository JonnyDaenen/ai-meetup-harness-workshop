# Organiser tools

## `openrouter_keys.py`: workshop keys

Hands out [OpenRouter](https://openrouter.ai) keys to participants who can't run a model locally, and takes them back afterwards. Every key gets a spending limit and an expiry date, and the script only ever touches keys whose name starts with `meetup-`.

**One-time setup in the OpenRouter dashboard**

1. Create a workspace for the event, e.g. `AI Meetup`.
2. In that workspace, open **Guardrails** and edit the workspace's default guardrail: allow only the workshop models (`qwen/qwen3.5-9b`, `anthropic/claude-haiku-5.5`) and set a budget as an overall ceiling. It applies to every key in the workspace.
3. Create a **management key** and put it in the repo's `.env` (never commit it):
   ```env
   OPENROUTER_MANAGEMENT_KEY=sk-or-v1-...
   ```

**Before the event**

```bash
uv run tools/openrouter_keys.py create 80 --workspace-id <workspace uuid>
```

This writes `tools/out/meetup-keys.csv` and `tools/out/meetup-cards.html` (print it: two cards per row, cut along the dashed lines). Each key is $1, expiring 14 Oct 2026 at midnight (`--limit`, `--expires` to change). Need more on the night? `create 20 --start 81 ...`.

**During and after**

```bash
uv run tools/openrouter_keys.py list      # usage per key and the total
uv run tools/openrouter_keys.py disable   # stop every workshop key (reversible in the dashboard)
uv run tools/openrouter_keys.py delete    # remove them for good
```

`tools/out/` holds live keys and is in `.gitignore`. Delete it after the event.

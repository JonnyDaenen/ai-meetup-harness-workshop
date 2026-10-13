# OpenRouter workshop keys: organiser checklist

For organisers. Participants who can't run a model locally get a card with an [OpenRouter](https://openrouter.ai) key: capped, limited to the workshop models, and dead after the event. Participants only need [remote-model.md](remote-model.md#workshop-key-openrouter).

Budget: about $0.03 per participant for an evening; 70 people stay well under $10. Buy $50–100 of credit to be safe.

## One-time setup (dashboard, ~15 min)

- [ ] Account with **two-step verification** on (Preferences → User → Manage)
- [ ] **Credits** → Add Credits. For an invoice with VAT: open *Edit Tax ID* in the purchase form and turn on *Send me invoices*
- [ ] **Workspace** for the event (Workspaces → New workspace), with a **lifetime budget** as the overall ceiling
- [ ] In that workspace, **Guardrails → Workspace Guardrail → Budget Policies**: $1 per key (the script also sets $1 per key)
- [ ] Account **Privacy**: training on paid endpoints off, free endpoints off (we only allow paid models)
- [ ] **Management Keys** → create one with an expiry date, then add it to the repo's `.env`:
  ```env
  OPENROUTER_MANAGEMENT_KEY=sk-or-v1-...
  ```
- [ ] Delete the auto-created **Default key** in the Default Workspace if you don't use it
- [ ] Set `WORKSPACE` at the top of [`tools/openrouter_keys.py`](../tools/openrouter_keys.py) to the workspace slug or id

Leave ZDR, prompt-injection and sensitive-info detection **off**: they can exclude the providers serving the workshop model or trip on workshop prompts.

## Before the event

```bash
uv run tools/openrouter_keys.py guard       # only the workshop models (MODELS in the script)
uv run tools/openrouter_keys.py create 80   # $1 each, expire 14 Oct 23:59 (--limit, --expires)
```

- [ ] Print `tools/out/meetup-cards.html` (two cards per row) and cut along the dashed lines
- [ ] Test one card end to end: J5 through the proxy (`--mode reverse:https://openrouter.ai`, `ANTHROPIC_BASE_URL=http://127.0.0.1:8080/api`)
- [ ] Keep `tools/out/meetup-keys.csv` on your laptop only: it holds the live keys

## On the night

- Watch spend: `uv run tools/openrouter_keys.py list`
- Need more keys: `uv run tools/openrouter_keys.py create 20 --start 81`
- Tell people: the workshop key means someone else's server, so no company code, data or secrets

## Afterwards

```bash
uv run tools/openrouter_keys.py delete      # or `disable` to keep them around, reversible
```

- [ ] Delete `tools/out/`
- [ ] Delete or expire the management key
- [ ] Check the spend under the workspace's **Activity**

## Troubleshooting

| Symptom | Cause |
|---|---|
| 404 on every call | `ANTHROPIC_BASE_URL` doesn't end in `/api`, or the model isn't in the guardrail's allowed list |
| 404 only on `count_tokens` | Normal: OpenRouter has no such endpoint; J5 ignores it |
| 401 | Key disabled, deleted or expired |
| 402 | Key reached its spending limit: hand out a new card |
| `'ThinkingBlock' object has no attribute 'text'` | Qwen sends a thinking block before its text: print only blocks with `type == "text"` |

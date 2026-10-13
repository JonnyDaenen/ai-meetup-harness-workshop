# Talk runbook

Three terminals: **T1** model, **T2** proxy, **T3** Claude / J5. Viewer: <http://127.0.0.1:8082>.

## Before the talk

```bash
lms server start
lms load qwen/qwen3.5-9b --context-length 65536   # Claude Code's prompt is big; the default context is too small
mkdir -p /tmp/claude-demo
```

Put the workshop key (`sk-or-...`) in `.env` as `ANTHROPIC_API_KEY`, so it never appears on screen. Everything else below is set inline, and inline wins over `.env`.

## 1. Show Claude

T3:

```bash
cd /tmp/claude-demo && claude
```

Say "hi".

## 2. Claude on the local model (no proxy)

T3 (Ctrl-C the previous one). First the raw API, to show it's just HTTP:

```bash
curl -s localhost:1234/v1/messages -H 'content-type: application/json' -d '{"model":"qwen/qwen3.5-9b","max_tokens":100,"messages":[{"role":"user","content":"hi"}]}'
```

About 2 s. Note the `usage`: 13 input tokens for "hi". Then Claude on the same model:

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:1234 ANTHROPIC_AUTH_TOKEN=local CLAUDE_CODE_MAX_CONTEXT_TOKENS=65536 CLAUDE_CODE_MODEL_CAPABILITIES=-mid_conv_system claude --model qwen/qwen3.5-9b
```

Say "hi" and wait: the first answer can take a few minutes (3+ min in rehearsal).

- `CLAUDE_CODE_MAX_CONTEXT_TOKENS` must match `--context-length`. Claude Code doesn't know this model and would otherwise assume 200k before compacting. The unknown-model warning may still show; it's harmless.
- `-mid_conv_system`: Claude Code sends its `# Environment` block as a `role: "system"` message mid-conversation. LM Studio only accepts `user`/`assistant` and answers `400 ... messages.1.role: Invalid discriminator value`. This turns that off. It's slow: a 9B model has to read tens of thousands of tokens of system prompt and tools first.

## 3. Proxy between Claude and Anthropic

T2:

```bash
cd proxy && uv run mitmweb --mode reverse:https://api.anthropic.com -p 8080 --set store_streamed_bodies=true --set stream_large_bodies=0 --set http2=false -s viewer.py -s sse_clean.py
```

T3:

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8080 DISABLE_TELEMETRY=1 DISABLE_ERROR_REPORTING=1 claude
```

Say "hi", then go through the viewer: session-title call, size of `system` + `tools`, `<system-reminder>`, `cache_control`, `usage`.
Don't open request headers in mitmweb (:8081): it shows your login token.

## 4. J5, our mini agent

T2 stays in `proxy/`; `cd` T3 back to the repo root. Each model gets its own proxy target, so restart T2 (Ctrl-C) between the two. Each model also has a no-proxy variant: only `ANTHROPIC_BASE_URL` changes, and nothing shows in the viewer.

**Local model**

T2:

```bash
uv run mitmweb --mode reverse:http://127.0.0.1:1234 -p 8080 --set store_streamed_bodies=true --set stream_large_bodies=0 --set http2=false -s viewer.py -s sse_clean.py
```

T3:

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8080 ANTHROPIC_API_KEY=local MODEL_ID=qwen/qwen3.5-9b uv run --project agent python agent/mini/j5_00_vanilla.py
```

No proxy (straight to LM Studio):

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:1234 ANTHROPIC_API_KEY=local MODEL_ID=qwen/qwen3.5-9b uv run --project agent python agent/mini/j5_00_vanilla.py
```

**Remote model (workshop key)**

T2:

```bash
uv run mitmweb --mode reverse:https://openrouter.ai -p 8080 --set store_streamed_bodies=true --set stream_large_bodies=0 --set http2=false -s viewer.py -s sse_clean.py
```

T3:

```bash
ANTHROPIC_BASE_URL=http://127.0.0.1:8080/api MODEL_ID=qwen/qwen3.5-9b uv run --project agent python agent/mini/j5_00_vanilla.py
```

No proxy (straight to OpenRouter):

```bash
ANTHROPIC_BASE_URL=https://openrouter.ai/api MODEL_ID=qwen/qwen3.5-9b uv run --project agent python agent/mini/j5_00_vanilla.py
```

Same model, someone else's GPU. Swap in `MODEL_ID=anthropic/claude-haiku-5.5` for a contrast. Use `j5_02_tools.py` instead of `j5_00_vanilla.py` to show tool calls, and `maxi` instead of `mini` for logging and token counts.

## After

```bash
lms unload --all && lms server stop
```

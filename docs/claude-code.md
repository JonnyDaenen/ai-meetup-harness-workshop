# Claude Code through the proxy

Once J5 makes sense, look at a production harness. Claude Code reads `ANTHROPIC_BASE_URL` too, so the same reverse proxy works.

## Against Anthropic (your normal login or API key)

```bash
# terminal 1
cd proxy
uv run mitmweb --mode reverse:https://api.anthropic.com -p 8080 \
  --set store_streamed_bodies=true --set stream_large_bodies=0 --set http2=false \
  -s sse_clean.py

# terminal 2, in a throwaway folder
ANTHROPIC_BASE_URL=http://127.0.0.1:8080 DISABLE_TELEMETRY=1 DISABLE_ERROR_REPORTING=1 claude
```

The stream flags are required here. Claude Code streams its responses, and without them it breaks.

## Against your local model

```bash
# terminal 1: proxy in front of LM Studio
uv run mitmweb --mode reverse:http://127.0.0.1:1234 -p 8080 \
  --set store_streamed_bodies=true --set stream_large_bodies=0 --set http2=false \
  -s sse_clean.py

# terminal 2
ANTHROPIC_BASE_URL=http://127.0.0.1:8080 ANTHROPIC_API_KEY=local \
  claude --model qwen/qwen3.5-9b -p "Hello, what model are you?"
```

Expect it to be slow. Claude Code sends a system prompt and tool definitions of tens of thousands of tokens, and a 9B model has to read all of that before every answer. That alone tells you something about harness design.

## What to look for

- The hidden **session title** call to a small model, sent before your first answer arrives.
- The size of `system` and `tools`, compared with J5's single-sentence system prompt.
- `<system-reminder>` blocks injected into **user** messages: date, IDE selection, available skills.
- `cache_control` markers. Claude Code asks the server to cache the stable prefix so it doesn't pay for it on every turn.
- `count_tokens` calls, and how `usage.input_tokens` grows turn after turn.

If you don't have Claude Code, the scrubbed samples in [`proxy/captures/`](../proxy/captures/) show the same things.

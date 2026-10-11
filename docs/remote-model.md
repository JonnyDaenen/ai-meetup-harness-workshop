# Remote model via an API

No model on your laptop? Use the workshop key below. Remote models are faster and much better at tool calling than a laptop-sized model, and cost a little: the whole workshop is a few cents to a dollar with a mid-size model.

## Workshop key (OpenRouter)

At the meetup you get a key card with an [OpenRouter](https://openrouter.ai) key. OpenRouter speaks the same Messages API as Anthropic, so J5 works unchanged. The key has a small spending limit, only works with the workshop models, and stops working after the meetup.

1. In `.env`, use block **B**:
   ```env
   ANTHROPIC_BASE_URL=http://127.0.0.1:8080/api
   ANTHROPIC_API_KEY=sk-or-v1-...
   MODEL_ID=qwen/qwen3.5-9b
   ```
   Note the `/api` at the end: OpenRouter's Messages API lives under `https://openrouter.ai/api`.
2. Start the proxy pointing at OpenRouter:
   ```bash
   cd proxy
   uv run mitmweb --mode reverse:https://openrouter.ai -p 8080 \
     --set store_streamed_bodies=true --set stream_large_bodies=0 --set http2=false \
     -s viewer.py -s sse_clean.py
   ```

Workshop models:

| `MODEL_ID` | Why | Price per million tokens (in / out) |
|---|---|---|
| `qwen/qwen3.5-9b` | **Default.** The same model as the local path, on someone else's GPU | $0.10 / $0.15 |
| `anthropic/claude-haiku-5.5` | Compare with a Claude model | $0.10 / $0.50 |

An evening of exercises costs about $0.03 per person with either model. Two things you'll notice in the proxy:
- `count_tokens` calls come back as **404**: OpenRouter doesn't offer that endpoint. J5 ignores the error.
- J5's cost summary is far too high: it calculates with Sonnet prices. Compare it with the real `usage` in the responses (exercise 01).

## Anthropic

1. Create a key at <https://console.anthropic.com/> (Settings → API keys) and add a few dollars of credit.
2. In `.env`, use block **C**:
   ```env
   ANTHROPIC_BASE_URL=http://127.0.0.1:8080
   ANTHROPIC_API_KEY=sk-ant-...
   MODEL_ID=claude-sonnet-4-6
   ```
3. Start the proxy pointing at Anthropic:
   ```bash
   cd proxy
   uv run mitmweb --mode reverse:https://api.anthropic.com -p 8080 \
     --set store_streamed_bodies=true --set stream_large_bodies=0 --set http2=false \
     -s viewer.py -s sse_clean.py
   ```

To skip the proxy, comment out `ANTHROPIC_BASE_URL`. The SDK then talks to `https://api.anthropic.com` directly.

Model ids and prices are listed at <https://docs.claude.com/en/docs/about-claude/models>. J5's cost estimate uses a fixed $3 per million input tokens and $15 per million output tokens (Sonnet pricing); change `INPUT_TOKEN_COST_PER_1M` and `OUTPUT_TOKEN_COST_PER_1M` in the agent for other models.

## Other Anthropic-compatible providers

Several providers expose the same Messages API, so only the base URL, key and model change:

| Provider | Base URL | `MODEL_ID` |
|---|---|---|
| MiniMax | `https://api.minimax.io/anthropic` | `MiniMax-M2.5` |
| GLM (Zhipu) | `https://api.z.ai/api/anthropic` | `glm-5` |
| Kimi (Moonshot) | `https://api.moonshot.ai/anthropic` | `kimi-k2.5` |
| DeepSeek | `https://api.deepseek.com/anthropic` | `deepseek-chat` |

Use the base URL in the proxy's `--mode reverse:<base url>`, and keep `ANTHROPIC_BASE_URL=http://127.0.0.1:8080` in `.env`.

## Keep your key safe

- `.env` is in `.gitignore`. Don't commit it, and don't paste it in the meetup chat.
- The proxy records the `x-api-key` header. Don't share saved flows.

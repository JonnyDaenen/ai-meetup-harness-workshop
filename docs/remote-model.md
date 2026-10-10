# Remote model via an API

Faster and much better at tool calling than a laptop-sized model. It costs a little: the whole workshop is a few cents to a dollar with a mid-size model.

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

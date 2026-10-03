# Proxy: see what the agent sends

[mitmproxy](https://mitmproxy.org) sits between the agent and the model server and records every request and response. `sse_clean.py` is a small add-on that turns streamed responses (Server-Sent Events) back into readable JSON in the UI.

## Run it (reverse mode, the default)

The agent talks to the proxy as if it were the model server, and the proxy forwards everything upstream. **No certificates, no `HTTPS_PROXY`.** It works for any client that lets you set a base URL (`ANTHROPIC_BASE_URL`).

```bash
cd proxy

# local model (LM Studio)
uv run mitmweb --mode reverse:http://127.0.0.1:1234 -p 8080 \
  --set store_streamed_bodies=true --set stream_large_bodies=0 --set http2=false \
  -s sse_clean.py

# remote model (Anthropic); swap in another provider's base URL if you use one
uv run mitmweb --mode reverse:https://api.anthropic.com -p 8080 \
  --set store_streamed_bodies=true --set stream_large_bodies=0 --set http2=false \
  -s sse_clean.py
```

Then:

- Point the agent at the proxy: `ANTHROPIC_BASE_URL=http://127.0.0.1:8080` (the default in `.env.example`).
- Open the UI at <http://127.0.0.1:8081>.

Prefer the terminal? Use `mitmdump` with the same flags, and add `--flow-detail 3` to print bodies.

### Why those flags?

| Flag | Why |
|---|---|
| `stream_large_bodies=0` | Forward every response to the client as it arrives. Streaming clients like Claude Code need this. |
| `store_streamed_bodies=true` | Still keep a copy of each streamed body, so the UI can show it. |
| `http2=false` | Keeps every call as a plain HTTP/1.1 request, which is simpler to read. |
| `-s sse_clean.py` | Rewrites the **stored copy** of an SSE response into `{"assistant_text": ..., "tool_calls": [...]}`. |

The first two matter. Without them, `sse_clean.py` would also rewrite the response the client receives, and a streaming client crashes because it expects SSE and gets JSON. With them, the client gets the original stream and only the UI shows the cleaned-up version. J5 doesn't stream, so its responses arrive as plain JSON either way.

## Useful mitmweb filters

| Filter | Shows |
|---|---|
| `~u /v1/messages$` | only model calls |
| `~u count_tokens` | token-counting calls |
| `~bs tool_use` | responses that contain a tool call |
| `~bq tool_result` | requests that send tool results back |

## Sample captures: [`captures/`](captures/)

Real Claude Code requests, captured with this proxy. They're scrubbed: device, account and session IDs, billing hashes, home paths and the git user name are replaced by placeholders.

| File | What to look for |
|---|---|
| `01_session_title.json` | A hidden call to a **small, cheap model** that only generates a title for the session. You never see this one in the UI. |
| `02_first_turn.json` | The user typed `hi!`. Look at what was sent along with it: about 27k characters of system prompt, 9 tool definitions with long descriptions, `<system-reminder>` blocks (skills, deferred tools, the IDE selection, the date) and `cache_control` markers. |
| `03_tool_call.json` | A few turns later: the **whole history is resent** on every call, including a `tool_use` → `tool_result` pair. |

## Advanced: forward mode (any HTTPS client)

If a client has no base-URL setting, run mitmproxy as a regular HTTPS proxy. This needs its certificate:

1. `uv run mitmweb -p 8080 --set store_streamed_bodies=true --set stream_large_bodies=0 --set http2=false -s sse_clean.py`
2. Install the certificate: run the client once through the proxy, then trust `~/.mitmproxy/mitmproxy-ca-cert.pem`. Alternatively, open <http://mitm.it> in a browser that uses the proxy and follow the steps for your OS.
3. In the client's terminal:
   ```bash
   export HTTPS_PROXY=http://127.0.0.1:8080
   export NODE_EXTRA_CA_CERTS=$HOME/.mitmproxy/mitmproxy-ca-cert.pem   # Node apps such as Claude Code
   export SSL_CERT_FILE=$HOME/.mitmproxy/mitmproxy-ca-cert.pem         # Python apps
   unset NO_PROXY
   ```
4. Filter on `~d anthropic.com` to hide everything else.

> ⚠️ Captured traffic contains everything the agent sends: your prompts, your files and your API keys (in headers). Don't share flows or captures without scrubbing them.

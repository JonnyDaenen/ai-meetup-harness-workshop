# Local model

Everything stays on your laptop: no API key, no cost, and you can read every byte. The trade-off is that small models are slower and less reliable at tool calling.

## Option A: LM Studio (recommended)

LM Studio serves an **Anthropic-compatible** API (`POST /v1/messages`), so the agent code is the same as for the remote path.

1. Install [LM Studio](https://lmstudio.ai) and open it once. That also installs the `lms` command line tool. If `lms` isn't found, run `~/.lmstudio/bin/lms bootstrap` and open a new terminal.
2. Download a model **before the workshop**:
   ```bash
   lms get qwen/qwen3.5-9b          # about 6.5 GB, the default
   ```
3. Start the server and load the model:
   ```bash
   lms server start                 # listens on http://127.0.0.1:1234
   lms load qwen/qwen3.5-9b
   lms ps                           # shows what is loaded
   ```
4. Check that it answers:
   ```bash
   curl -s http://127.0.0.1:1234/v1/messages \
     -H 'content-type: application/json' -H 'x-api-key: local' -H 'anthropic-version: 2023-06-01' \
     -d '{"model":"qwen/qwen3.5-9b","max_tokens":50,"messages":[{"role":"user","content":"Say hi"}]}'
   ```
5. In `.env`, use block **A** (through the proxy) or **B** (direct) from `.env.example`.

When you're done, `lms unload --all` and `lms server stop` give the memory back.

### Which model?

| Model | Size | RAM | Notes |
|---|---|---|---|
| `mistralai/ministral-3-3b` | 3 GB | 8 GB | Fast, but weak at tool calls. Fine for exercises 00–01. |
| `qwen/qwen3.5-9b` | 6.5 GB | 16 GB | **Default.** Decent tool calling. |
| `google/gemma-4-26b-a4b` | 18 GB | 32 GB | Best of the three. Only 4B parameters are active per token, so it's still quick. |

The model plus its context must fit in RAM. If your laptop starts swapping, pick a smaller model or lower the context length in LM Studio.

## Option B: Ollama

Recent Ollama versions also serve the Anthropic Messages API, on port `11434`. Older versions only offer the OpenAI-style API, so update first.

```bash
ollama --version                     # update if this is old
ollama pull qwen3.5:9b                # check the exact tag at ollama.com/library
ollama serve                         # if it isn't already running
```

Then use `ANTHROPIC_BASE_URL=http://127.0.0.1:11434` (or the proxy with `--mode reverse:http://127.0.0.1:11434`) and `MODEL_ID=qwen3.5:9b`.

## Running the agent in the devcontainer

The devcontainer reaches the host through `host.docker.internal`, and is preconfigured for the proxy on `:8080`. LM Studio only listens on `127.0.0.1` by default; if the container can't reach it, enable "Serve on local network" in LM Studio's server settings.

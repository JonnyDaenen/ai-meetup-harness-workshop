# Before the meetup (15 minutes at home)

Venue Wi-Fi won't cope with 60 people downloading packages and models at once, so please do this at home.

## 1. What you need

| | Required? | Why |
|---|---|---|
| A laptop with a terminal | Yes | macOS, Linux, or Windows with **WSL2** (see below) |
| [git](https://git-scm.com/downloads) | Yes | To clone the repo |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | Yes | Installs Python and all packages for you |
| [LM Studio](https://lmstudio.ai) + a model | Only for the local path | Running the model on your own laptop. No good hardware? You'll get a workshop key at the meetup |
| [Claude Code](https://docs.claude.com/en/docs/claude-code) | No | Nice to inspect a production agent yourself |

## 2. Install and download

```bash
git clone https://github.com/JonnyDaenen/ai-meetup-harness-workshop.git
cd ai-meetup-harness-workshop
uv sync --project agent      # the agent's packages
uv sync --project proxy      # mitmproxy (about 40 packages)
cp .env.example .env
```

## 3. Pick your model path

**A. Local (free, private, slow).** You need about 16 GB of RAM; Apple Silicon or a recent GPU helps a lot. Download the model now (6.5 GB):

```bash
lms get qwen/qwen3.5-9b
```

Details in [local-model.md](local-model.md). Less RAM? Try `mistralai/ministral-3-3b` (3 GB), or use B.

**B. Workshop key (fast, nothing to install).** We hand out cards with a key at the meetup. Nothing to prepare beyond step 2.

**C. Your own API key.** Anthropic or a compatible provider, see [remote-model.md](remote-model.md).

## 4. Check it works

```bash
uv run --project agent python -c "import anthropic, dotenv; print('agent OK')"
cd proxy && uv run mitmdump --version | head -1 && cd ..
```

Local path: also start LM Studio's server and check it answers (the `curl` test in [local-model.md](local-model.md)).

## Windows

Use **WSL2** with Ubuntu (`wsl --install` in an admin PowerShell, then reboot) and do everything above inside the Ubuntu terminal. Plain Windows mostly works, but the agent's bash tool would run commands through `cmd.exe`, where `ls`, `cat` and pipes the model likes to use don't exist, and the docs use bash syntax.

LM Studio runs on Windows itself, not inside WSL. To let WSL reach it on `127.0.0.1:1234`, turn on mirrored networking: create `%UserProfile%\.wslconfig` with

```ini
[wsl2]
networkingMode=mirrored
```

then run `wsl --shutdown` and reopen Ubuntu. If that doesn't work, enable "Serve on local network" in LM Studio's server settings, or simply use the workshop key.

## At the meetup

Bring your laptop charged (and a charger): the local model makes it work hard.

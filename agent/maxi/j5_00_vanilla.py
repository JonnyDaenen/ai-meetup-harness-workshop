
import itertools
import json
import logging
import os
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=False)

# --- colours & logging ---

_GREY   = "\033[2;37m"
_PURPLE = "\033[35m"
_BLUE   = "\033[1;34m"
_CYAN   = "\033[36m"
_RED    = "\033[1;31m"
_GREEN  = "\033[1;32m"
_ITALIC = "\033[3m"
_RESET  = "\033[0m"


def _cprint(text, color):
    print(f"{color}{text}{_RESET}")


class _GreyFormatter(logging.Formatter):
    def format(self, record):
        return f"{_GREY}{super().format(record)}{_RESET}"

_handler = logging.StreamHandler()
_handler.setFormatter(_GreyFormatter("%(message)s"))
log = logging.getLogger("j5")
log.addHandler(_handler)
log.setLevel(logging.DEBUG if os.getenv("DEBUG") else logging.WARNING)

# --- client setup ---

# When using a local proxy, drop the auth token so it doesn't conflict.
if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))

log.debug("ANTHROPIC_BASE_URL: %s", os.getenv("ANTHROPIC_BASE_URL"))
log.debug("MODEL_ID: %s", os.getenv("MODEL_ID"))

MODEL = os.environ["MODEL_ID"]

SYSTEM = f"You are a J5, a coding agent at {os.getcwd()}. Use bash to solve tasks. Act, don't explain. Be brief, always answer in SMS style super brief, and sign off with - J5."

OUTPUT_TOKEN_COST_PER_1M = 15
INPUT_TOKEN_COST_PER_1M = 3

# --- session / history ---

total_input_tokens = 0
total_output_tokens = 0
num_message_calls = 0
total_elapsed = 0.0

# Each session gets its own folder: .j5/history/YYYY-MM-DD/HHMMSS/<uuid>/
_now = datetime.now()
_session_dir = (
    Path(".j5") / "history"
    / _now.strftime("%Y-%m-%d")
    / _now.strftime("%H%M%S")
    / str(uuid.uuid4())
)
_session_dir.mkdir(parents=True, exist_ok=True)
_call_counter = 0


def _log_call(messages, response):
    global _call_counter
    _call_counter += 1
    path = _session_dir / f"call{_call_counter:04d}.log"
    payload = {
        "messages": [
            m if isinstance(m, dict) else m.model_dump()
            for m in messages
        ],
        "response": response.model_dump(),
    }
    path.write_text(json.dumps(payload, indent=2, default=str))


def calculate_tokens(messages) -> tuple[int, int]:
    """Returns (message_tokens, system_tokens) — used for debug logging only."""
    try:
        input_token_count = client.messages.count_tokens(
            model=MODEL, messages=messages
        ).input_tokens or 0
        system_token_count = (client.messages.count_tokens(
            model=MODEL, system=SYSTEM, messages=messages
        ).input_tokens or 0) - input_token_count
    except Exception:
        input_token_count, system_token_count = 0, 0
    return input_token_count, system_token_count

# --- agent loop ---

def print_token_usage():
    total_input_cost = (total_input_tokens / 1_000_000) * INPUT_TOKEN_COST_PER_1M
    total_output_cost = (total_output_tokens / 1_000_000) * OUTPUT_TOKEN_COST_PER_1M
    total_cost = total_input_cost + total_output_cost
    _cprint(f"Total input tokens: {total_input_tokens} ({total_input_cost:.6f}$)", _BLUE)
    _cprint(f"Total output tokens: {total_output_tokens} ({total_output_cost:.6f}$)", _BLUE)
    _cprint(f"Number of message calls: {num_message_calls}", _BLUE)
    _cprint(f"Estimated total cost: ${total_cost:.6f}", _BLUE)
    _cprint(f"Total answer time: {total_elapsed:.2f}s", _BLUE)
    if num_message_calls > 0:
        _cprint(f"Average time per call: {total_elapsed / num_message_calls:.2f}s", _BLUE)


def _track_usage(response):
    global total_input_tokens, total_output_tokens, num_message_calls
    total_input_tokens += response.usage.input_tokens
    total_output_tokens += response.usage.output_tokens
    num_message_calls += 1
    log.debug("usage: %s", vars(response.usage))
    log.debug(f"running total — input: {total_input_tokens}, output: {total_output_tokens}, calls: {num_message_calls}")
    log.debug(f"running cost: ${(total_input_tokens / 1_000_000) * INPUT_TOKEN_COST_PER_1M + (total_output_tokens / 1_000_000) * OUTPUT_TOKEN_COST_PER_1M:.6f}")


def agent_loop(messages: list) -> float:
    """Single model call — no tools, just a response."""
    log.debug("messages: %s", messages)
    log.debug("estimated tokens: %s", calculate_tokens(messages))

    t0 = time.perf_counter()
    response = client.messages.create(
        model=MODEL,
        system=SYSTEM,
        tools=[],
        messages=messages,
        max_tokens=8000,
    )
    elapsed = time.perf_counter() - t0

    _log_call(messages, response)
    _track_usage(response)

    messages.append({"role": "assistant", "content": response.content})
    return elapsed

# --- chat loop ---

def print_agent_response(history):
    response_content = history[-1]["content"]
    if isinstance(response_content, list):
        for block in response_content:
            if hasattr(block, "text"):
                _cprint(f"🌪️ {block.text}", _PURPLE)


def _spin(stop_event, msg="J5 is thinking"):
    frames = itertools.cycle(["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"])
    while not stop_event.is_set():
        sys.stdout.write(f"\r{_GREY}{next(frames)} {msg}...{_RESET}")
        sys.stdout.flush()
        time.sleep(0.1)
    sys.stdout.write("\r" + " " * (len(msg) + 10) + "\r")
    sys.stdout.flush()


def _exit():
    _cprint("Exiting J5. Goodbye!", _RED)
    print_token_usage()


def _run_agent(history):
    if log.isEnabledFor(logging.DEBUG):
        _cprint("💬 J5 is thinking...", _GREY)
        return agent_loop(history)
    stop = threading.Event()
    t = threading.Thread(target=_spin, args=(stop,))
    t.start()
    try:
        return agent_loop(history)
    finally:  # stop the spinner even if the API call fails, or the process hangs
        stop.set()
        t.join()


def chat_loop():
    global total_elapsed
    history = []  # full conversation, sent to the model on every turn
    while True:
        try:
            query = input(f"{_CYAN}s01 >> {_RESET}")
        except (EOFError, KeyboardInterrupt):
            _exit(); break

        clean_query = query.strip().lower()

        # Built-in commands — handled before hitting the model.
        if clean_query in ("q", "exit", "quit", "/quit", "/exit"):
            _exit(); break
        if clean_query == "":
            _cprint("Please enter a command or query.", _ITALIC); continue
        if clean_query == "/clear":
            history.clear(); _cprint("History cleared.", _GREEN); continue
        if clean_query == "/history":
            _cprint("Conversation History:", _BLUE); print(history); continue

        # Normal query — append to history, run the agent, print the response.
        history.append({"role": "user", "content": query})
        elapsed = _run_agent(history)
        total_elapsed += elapsed
        print()
        print_agent_response(history)
        _cprint(f"⏱ {elapsed:.2f}s", _GREY)
        print()


if __name__ == "__main__":
    _cprint("Welcome to J5, the coding agent! Type your commands below.", _PURPLE)
    chat_loop()

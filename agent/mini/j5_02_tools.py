import os
import subprocess
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()  # reads ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY
MODEL = os.environ["MODEL_ID"]
WORKDIR = Path.cwd()
SYSTEM = f"You are J5, a coding agent at {WORKDIR}. Use the tools to solve tasks. Be brief."


def safe_path(p):
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path


def run_bash(command):
    r = subprocess.run(command, shell=True, cwd=WORKDIR, capture_output=True, text=True, timeout=120)
    return (r.stdout + r.stderr)[:50000] or "(no output)"


def read_file(path):
    return safe_path(path).read_text()[:50000]


def write_file(path, content):
    fp = safe_path(path)
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)
    return f"Wrote {len(content)} bytes to {path}"


def edit_file(path, old_text, new_text):
    fp = safe_path(path)
    text = fp.read_text()
    if old_text not in text:
        return f"Error: text not found in {path}"
    fp.write_text(text.replace(old_text, new_text, 1))
    return f"Edited {path}"


# The tool table: name -> handler. The model's input becomes the handler's keyword arguments.
TOOL_HANDLERS = {"bash": run_bash, "read_file": read_file, "write_file": write_file, "edit_file": edit_file}


def schema(**props):
    return {"type": "object", "properties": {k: {"type": v} for k, v in props.items()}, "required": list(props)}


TOOLS = [
    {"name": "bash", "description": "Run a shell command.", "input_schema": schema(command="string")},
    {"name": "read_file", "description": "Read a file.", "input_schema": schema(path="string")},
    {"name": "write_file", "description": "Write content to a file.", "input_schema": schema(path="string", content="string")},
    {"name": "edit_file", "description": "Replace exact text in a file.", "input_schema": schema(path="string", old_text="string", new_text="string")},
]


def run_tool(block):
    if input(f"{block.name} {block.input}\nRun? (y/n) ") != "y":
        return "Denied by user"
    try:
        return TOOL_HANDLERS[block.name](**block.input)
    except Exception as e:  # errors go back to the model, so it can try again
        return f"Error: {e}"


def agent_loop(history):
    """Call the model, run the tools it asks for, repeat until it stops asking."""
    while True:
        response = client.messages.create(model=MODEL, system=SYSTEM, tools=TOOLS, messages=history, max_tokens=8000)
        history.append({"role": "assistant", "content": response.content})
        for block in response.content:
            if block.type == "text":
                print(block.text)
        if response.stop_reason != "tool_use":
            return
        results = []
        for block in response.content:
            if block.type == "tool_use":
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": run_tool(block)})
        history.append({"role": "user", "content": results})


history = []
while True:
    history.append({"role": "user", "content": input(">> ")})
    agent_loop(history)

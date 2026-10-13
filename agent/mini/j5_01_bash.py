import os
import subprocess

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()  # reads ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY
MODEL = os.environ["MODEL_ID"]
SYSTEM = f"You are J5, a coding agent at {os.getcwd()}. Use bash to solve tasks. Be brief."

TOOLS = [{
    "name": "bash",
    "description": "Run a shell command.",
    "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]},
}]


def run_bash(command):
    if input(f"$ {command}\nRun? (y/n) ") != "y":
        return "Denied by user"
    r = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=120)
    return (r.stdout + r.stderr)[:50000] or "(no output)"


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
                output = run_bash(block.input["command"])
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        history.append({"role": "user", "content": results})


history = []
while True:
    history.append({"role": "user", "content": input(">> ")})
    agent_loop(history)

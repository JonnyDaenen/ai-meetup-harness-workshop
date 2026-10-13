import os

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic()  # reads ANTHROPIC_BASE_URL and ANTHROPIC_API_KEY
MODEL = os.environ["MODEL_ID"]
SYSTEM = "You are J5, a coding agent. Be brief."

history = []  # the whole conversation, sent on every turn
while True:
    history.append({"role": "user", "content": input(">> ")})
    response = client.messages.create(model=MODEL, system=SYSTEM, messages=history, max_tokens=8000)
    history.append({"role": "assistant", "content": response.content})
    for block in response.content:
        if block.type == "text":
            print(block.text)

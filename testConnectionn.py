import os
from anthropic import Anthropic
from dotenv import load_dotenv

chat = True
history = []
load_dotenv()
client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)
while chat:
    msg = input()
    if msg == "sleep":
        chat = False
        break
    history.append({"role": "user","content": msg})
    message = client.messages.create(
        max_tokens = 1024,
        messages = history,
        model = "claude-sonnet-5",
    )
    for i in message.content:
        if i.type == "text":
            print(i.text)
            history.append({"role": "assistant", "content": i.text})
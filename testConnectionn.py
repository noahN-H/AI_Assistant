import os
from anthropic import Anthropic
from dotenv import load_dotenv


chat = True
history = []
load_dotenv()
client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)

persistantHistory = open(r"D:\Obsidian\Knowledge\history.md", "r")
read_history = persistantHistory.read()
   
while chat:
    msg = input()
    if msg == "sleep":
        chat = False
        exit_msg = client.messages.create(
            max_tokens = 1024,
            system = "review and output what you think is relevant in long term memory",
            messages = history + [{"role": "user","content": "review and output what you think is relevant in long term memory"}], 
            model = "claude-sonnet-5",
        )  
        
        with open(r"D:\Obsidian\Knowledge\history.md", "a") as persistantHistory:
            for i in exit_msg.content:
                if i.type == "text":
                    persistantHistory.write(i.text)
        break
    
    
    history.append({"role": "user","content": msg})
    
    message = client.messages.create(
        max_tokens = 1024,
        system = read_history,
        messages = history,
        model = "claude-sonnet-5",
    )
    for i in message.content:
        if i.type == "text":
            print(i.text)
            history.append({"role": "assistant", "content": i.text})
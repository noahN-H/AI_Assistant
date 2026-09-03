import os
from anthropic import Anthropic
from dotenv import load_dotenv
import json


chat = True
history = []
load_dotenv()
obsidian_vault = r"D:\Obsidian\Knowledge"
obsidian_dir = os.listdir(obsidian_vault)
client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)

def access_files(filename):
    with open(os.path.join(obsidian_vault,filename), "r") as open_file:
        read_file = open_file.read()
        return read_file
    
tools = [
    {
        "name": "access_files",
        "description": "Reads and returns the contents of a specific file from the user's memory vault, given its filename. Use this when a file mentioned in the file index seems relevant to the current conversation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The exact filename to read, as it appears in the file index (e.g. 'eeg_project.md')."
                }
            },
            "required": ["filename"]
        }
    }
]

with open(os.path.join(obsidian_vault,"startup.md"), "r") as startup:
    read_startup = startup.read()

with open(os.path.join(obsidian_vault,"me.md"), "r") as user_profile:
    read_user_profile = user_profile.read()
   
while chat:
    msg = input()
    if msg == "sleep":
        chat = False
        exit_msg = client.messages.create(
            max_tokens = 1024,
            system = "review and output what you think is relevant in long term memory. Respond with ONLY valid JSON (no other text) in this exact format: a list of objects, each with a 'filename' key and a 'content' key. Example: [{'filename': 'example.md', 'content': ...}]. If nothing is worth saving, respond with an empty list []",
            messages = history + [{"role": "user","content": "review and output what you think is relevant in long term memory"}], 
            model = "claude-sonnet-5",
        )
        
        for i in exit_msg.content:
            if i.type == "text":
                try:
                    enteries = json.loads(i.text)
                    for entry in enteries:
                        filename = entry['filename']
                        if filename != "startup.md":
                            content = entry['content']
                            path = os.path.join(obsidian_vault,filename)
                            with open(path, "a") as file:
                                file.write(content)
                except:
                    print("could not load conversation into memory")
                    
        break
    
    if msg == "abort":
        break
    
    history.append({"role": "user","content": msg})
    
    resp = client.messages.create(
        max_tokens = 1024,
        tools = tools,
        system = f"The following is infomation is the relevant startup infomation:\n\n{read_startup}, you can also view files that are in the directory: {obsidian_dir}. infomation about the user can be found here in: {read_user_profile}",
        messages = history,
        model = "claude-sonnet-5",
    )       

    while resp.stop_reason == "tool_use":
        tool_use = []
        tool_result = []
        for i in resp.content:
            if i.type == "tool_use":
                tool_use.append(i)
        for j in tool_use:
            result = access_files(j.input["filename"])
            tool_result.append(
                {"type": "tool_result",
                "tool_use_id": j.id,
                "content": str(result)})

        resp = client.messages.create(
            max_tokens = 1024,
            tools = tools,
            messages = history + [{"role": "assistant", "content": resp.content},
                    {"role": "user", "content": tool_result}],
            model = "claude-sonnet-5",
        )
        
    for i in resp.content:
        if i.type == "text":
            print(i.text)
            history.append({"role": "assistant", "content": i.text})
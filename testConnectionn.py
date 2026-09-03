import os
from anthropic import Anthropic
from dotenv import load_dotenv
import json
import requests
from geopy.geocoders import Nominatim


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
    
def edit_files(filename, content, mode):
    if filename != "startup.md":
        with open(os.path.join(obsidian_vault,filename), mode) as edit_file:
            edit_file.write(content)
        return f"Successfully wrote to {filename} in {mode} mode. Content written: {content}"
    
def get_weather(location, unit):
    try:
        geolocator = Nominatim(user_agent = "Assistant")
        location_coords = geolocator.geocode(location)
        weather_params = {
            "latitude": location_coords.latitude,
            "longitude": location_coords.longitude,
            "current": "temperature_2m",
            "temperature_unit": unit,
        }
        response = requests.get("https://api.open-meteo.com/v1/forecast", params = weather_params)
        data = response.json()
        return f"The weather in {location} is {data['current']['temperature_2m']}"
    except Exception as e:
        return f"Weather could not be returned: {e}"
    
    
tools = [
    {
        "name": "access_files",
        "description": "Reads and returns the contents of a specific file from the user's memory vault, given its filename. Use this when a file mentioned in the file index seems relevant to the current conversation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The exact filename to read, as it appears in the file index (e.g. 'eeg_project.md').",
                }
            },
            "required": ["filename"]
        }
    },
    
    {
        "name": "edit_files",
        "description": "Creates and/or edits the contents of a specific file from the user's memory vault, given its filename. Use this when a file mentioned in the file index or not in the index but seems relevant to the current conversation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "The exact filename that will either created or the exact filename of the file as it appears in the the file index (e.g. 'eeg_project.md').",
                },
                "content": {
                    "type": "string",
                    "description": "the content of which either will be appended to the file or overwrite in the file",
                },
                "mode": {
                    "type": "string",
                    "description": "the mode either 'a' for append where a file is created, or 'w' where a file is written to.",
                    "enum": ["a", "w"],
                },
            },
         "required": ["filename", "content", "mode"],
        }
    },
    
    {
        "name": "get_weather",
        "description": "Get the current weather in a given location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The city and state, e.g. San Francisco, CA",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "The unit of temperature",
                },
            },
            "required": ["location"],
        },
        "input_examples": [
            {"location": "San Francisco, CA", "unit": "fahrenheit"},
            {"location": "Tokyo, Japan", "unit": "celsius"},
            {"location": "New York, NY"},
        ],
    },
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
                except Exception as e:
                    print(f"Could not load conversation into memory because: {e}")
                    
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
            if j.name == "access_files":
                result = access_files(j.input["filename"])
            elif j.name == "edit_files":
                result = edit_files(j.input["filename"],j.input["content"], j.input["mode"] )
            elif j.name == "get_weather":
                result = get_weather(j.input["location"], j.input["unit"])
            else:
                result = "agent not found"
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
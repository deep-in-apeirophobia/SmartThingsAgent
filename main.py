
import asyncio
import colorsys
import json
import os

import aiohttp
import dotenv
from openai import OpenAI

dotenv.load_dotenv()

client = OpenAI()


def rgb_to_hs(r, g, b):
    """
    Convert 8-bit RGB to (H, S) using colorsys.
    Returns H in degrees [0,360), S in [0,1].
    """
    # normalize to [0,1]
    r_, g_, b_ = r/255.0, g/255.0, b/255.0
    h, s, _v = colorsys.rgb_to_hsv(r_, g_, b_)
    return h * 100, s * 100


function_definitions = [{
    "type": "function",
    "name": "update_lights",
    "description": """You can use this command to update 6 lights, in 2 rows of three. You'll send 6 configs, one for each light. you can set switch, and their rgb values. Here's how the lights are placed, from left
    to right, and top to bottom:
        I1 I2 I3
        I4 I5 I6
        """,
    "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "I1": {
                    "type": "object",
                    "description": "Config for I1",
                    "properties": {
                        "switch": {
                            "type": "string",
                            "enum": ["on", "off"],
                        },
                        "red": {"type": "integer", },
                        "green": {"type": "integer", },
                        "blue": {"type": "integer", },
                    },
                },
                "I2": {
                    "type": "object",
                    "description": "Config for I2",
                    "properties": {
                        "switch": {
                            "type": "string",
                            "enum": ["on", "off"],
                        },
                        "red": {"type": "integer", },
                        "green": {"type": "integer", },
                        "blue": {"type": "integer", },
                    },
                },
                "I3": {
                    "type": "object",
                    "description": "Config for I3",
                    "properties": {
                        "switch": {
                            "type": "string",
                            "enum": ["on", "off"],
                        },
                        "red": {"type": "integer", },
                        "green": {"type": "integer", },
                        "blue": {"type": "integer", },
                    },
                },
                "I4": {
                    "type": "object",
                    "description": "Config for I4",
                    "properties": {
                        "switch": {
                            "type": "string",
                            "enum": ["on", "off"],
                        },
                        "red": {"type": "integer", },
                        "green": {"type": "integer", },
                        "blue": {"type": "integer", },
                    },
                },
                "I5": {
                    "type": "object",
                    "description": "Config for I5",
                    "properties": {
                        "switch": {
                            "type": "string",
                            "enum": ["on", "off"],
                        },
                        "red": {"type": "integer", },
                        "green": {"type": "integer", },
                        "blue": {"type": "integer", },
                    },
                },
                "I6": {
                    "type": "object",
                    "description": "Config for I6",
                    "properties": {
                        "switch": {
                            "type": "string",
                            "enum": ["on", "off"],
                        },
                        "red": {"type": "integer", },
                        "green": {"type": "integer", },
                        "blue": {"type": "integer", },
                    },
                },
            },

    }
}]

DEVICES = {}
with open("./devices.json") as f:
    DEVICES = json.load(f)

LIGHTS = DEVICES.get("lights", {})


def convert_config(config: dict):
    commands = []

    if 'switch' in config:
        commands.append({
            "command": config['switch'],
            "capability": "switch",
            "component": "main"
        })

    if 'red' in config or 'green' in config or 'blue' in config:
        h, s = rgb_to_hs(config.get('red', 0), config.get(
            'green', 0), config.get('blue', 0))
        commands.append({
            "command": "setColor",
            "capability": "colorControl",
            "component": "main",
            "arguments": [
                {
                        "hue": h,
                        "saturation": s,
                        }
            ],
        })

    return {"commands": commands}


async def update_light(session: aiohttp.ClientSession, id, config):
    conf = convert_config(config)
    print("Updating light", config, conf, id)
    async with session.post(f"https://api.smartthings.com/v1/devices/{id}/commands", json=conf, headers={
        'Authorization': f"Bearer {os.environ.get('SMARTTHINGS_TOKEN')}"
    }) as resp:
        resp.raise_for_status()
        return await resp.text()


async def update_lights(configs):
    print("Updating lights", configs)
    async with aiohttp.ClientSession() as session:
        reqs = [update_light(session, id, configs[name])
                for name, id in LIGHTS.items() if name in configs]
        resps = await asyncio.gather(*reqs, return_exceptions=True)

        print(resps)

        for r in resps:
            if isinstance(r, Exception):
                return "FAILED TO UPDATED LIGHTS"

        return f"{len(resps)} LIGHTS UPDATED"


functions = {
    'update_lights': update_lights,
}


async def call_function(fnname, args):
    fn = functions[fnname]
    print("Calling", fnname, fn)
    return await fn(args)


async def run_agent(command: str):
    messages = [
        {"role": "system", "content": "You're a personal assistant, helping me run my smart home"},
        {"role": "user", "content": command},
    ]

    while True:
        resp = client.responses.create(
            model="gpt-4o-mini",
            input=messages,
            tools=function_definitions,
        )
        msg = resp.output

        print(msg)

        if msg[0].type == "function_call":
            tool_call = msg[0]

            fn_name = tool_call.name
            fn_args = json.loads(tool_call.arguments or "{}")

            print("Calling function", fn_name, fn_args)

            if fn_name not in functions:
                output = 'FUNCTION NOT FOUND'
            else:
                output = await call_function(fn_name, fn_args)

            messages.append(tool_call)
            messages.append({
                "type": "function_call_output",
                "call_id": tool_call.call_id,
                "output": output
            })

            continue

        return msg['content']


if __name__ == '__main__':
    command = input("Enter prompt: ")
    asyncio.run(run_agent(command))
    # asyncio.run(call_function("update_lights", {
    #     "I1": {
    #         "switch": "off",
    #     },
    #     "I2": {
    #         "switch": "on",
    #         "hue": 0,
    #         "saturation": 100,
    #     },
    # }))

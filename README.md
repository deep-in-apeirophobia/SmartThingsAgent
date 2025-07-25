# SmartThings Agent

This repo defines some simple function calls for samsung smartthings to be used with an Agent(in this case, an OpenAI model).

For now you can control your lights using this. You need an OpenAI key and a SmartThings PAT to use this.
Then create a `devices.json` file and configure your lights as described in `devices-example.json`:

You can prompt the agent to change the lights, like asking it to `give my room an automn vibe`, or `I want to feel like i'm in a club`.

# Refernces

- [SmartThings API Reference](https://developer.smartthings.com/docs/api/public#section/Authentication/OAuth2-scopes)
- You need to get a list of your devices first
- Then you can see what command each one would accept

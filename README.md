# zyntra.py

> [!warning]
> This library is no longer being updated.


An unofficial bot library for making bots in [Zyntra](https://zyntra.gg), written for Python.

# Usage
Download the library using `pip`:
```
pip install zyntra.py
```

Create a bot at [the developer site](https://zyntra.gg/developers/applications), you can view [this guide](https://zyntra.gg/developers/documentation/bots).

**Atleast Python 3.9 or higher is required in order to use this library.**

# Bot Example
> [!note]
> If you're used to [discord.py](https://github.com/Rapptz/discord.py), then this should be mildly similar.
```python
from zyntra import *
from zyntra.utils.color import Color

# ID = Bot ID
# Optionally, you can set a prefix using prefix="prefix!"
client = Client(TOKEN, ID)

# If a user tries to run a command that's currently on cooldown.
@client.on_cooldown()
async def on_cooldown(command: CommandData, channel: Channel, remaining: float):
    await channel.send(f"⏳ Command `{command.name}` is on cooldown!\nTry again in **{remaining:.2f}** second(s).")

# Once the client logs in.
@client.on_ready()
async def ready():
    print("Client is ready!")

# Once the client's socket connects
@client.on_socket_connect()
async def connect():
    print("Connected to socket!")

# When a message is created.
@client.on_message_create()
async def on_message(msg: Message):
    print(msg.content)

# Registers an echo command (Order: name, description, cooldown in seconds)
@client.command("echo", "Echoes text.", 1)
async def echo(ctx: Interaction, args: list):
    await ctx.reply(" ".join(args))

# A help command displaying all the commands.
@client.command("help", "Gets all commands")
async def help(ctx: Interaction, args: list):
    cmds = [f"`{client.prefix}{command.name}` - {command.description}" for command in client.commands]

    embed = Embed(
        title=f"Commands",
        description="\n".join(cmds),
        color=Color.get_color("green"),
        footer=f"There are currently {len(cmds)} command(s)!"
    )
    await ctx.reply(embed=embed)

# Starts the main bot loop
client.start()
```

# Currently supported events:
- `on_message_create` (Socket.IO name: messageCreate) - Occurs when a message is created.

- `on_socket_connect` (Socket.IO name: join) - Occurs when the bot connects to the socket.

- `on_ready` - Occurs when everything is done successfully.

- `on_cooldown` - Occurs when a user tries to run a command that is on cooldown.

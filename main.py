import asyncio
import logging
import os
from discord.ext import commands
import discord
from tortoise import run_async

from modules import config, database

client = commands.Bot(auto_sync_commands=True,
                      command_prefix=config.get("DISCORD", "PREFIX"))

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(
    filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


@client.event
async def on_ready():
    print(f"Logged in as \"{client.user.name}\" (ID: {client.user.id})")
    print(f"Discord.py version: {discord.__version__}")
    print(f"Bot is ready and running on {len(client.guilds)} servers")
    await client.change_presence(activity=discord.Game(name=f"on {len(client.guilds)} servers"))

    print("\n-----------------------------")
    loaded = 0
    for cog in os.listdir("./cogs"):
        if cog.endswith(".py"):
            try:
                client.load_extension(f"cogs.{cog[:-3]}")
                print(f"Cog {cog[:-3]} loaded")
                loaded += 1
            except Exception as ex:
                print(f"Failed to load cog {cog[:-3]}\n{ex}")
    print(f"Loaded {loaded} cogs")
    print("-----------------------------\n\n")


def cogList():
    return [x[:-3] for x in os.listdir("./cogs") if x.endswith(".py")]


@client.slash_command(
    name="load",
    aliases=["l"])
async def load(ctx, cog: discord.Option(str, "Enter a cog name", choices=cogList())):
    await client.wait_until_ready()
    try:
        client.load_extension(f"cogs.{cog}")
        await ctx.respond(f"Loaded cogs {cog}")
        logger.info(f"Loaded cogs {cog}")
    except:
        await ctx.respond(f"Failed to load cogs {cog}")


@client.slash_command(
    name="unload",
    aliases=["u"])
async def unload(ctx, cog: discord.Option(str, "Enter a cog name", choices=cogList())):
    await client.wait_until_ready()
    try:
        client.unload_extension(f"cogs.{cog}")
        await ctx.respond(f"Unloaded cogs {cog}")
        logger.info(f"Unloaded cog {cog}")
    except:
        await ctx.respond(f"Failed to unload cog {cog}")


@client.slash_command(
    name="reload",
    aliases=["r"])
async def reload(ctx, cog: discord.Option(str, "Enter a cog name", choices=cogList())):
    await client.wait_until_ready()
    try:
        client.reload_extension(f"cogs.{cog}")
        await ctx.respond(f"Reloaded cog {cog}")
        logger.info(f"Reloaded cog {cog}")
    except:
        await ctx.respond(f"Failed to reload cog {cog}")


@client.slash_command(
    name="reloadall",
    aliases=["rall"]
)
async def reloadall(ctx):
    await client.wait_until_ready()
    for cog in os.listdir("./cog"):
        if cog.endswith(".py"):
            try:
                client.reload_extension(f"cogs.{cog[:-3]}")
                logger.info(f"Reloaded cog {cog[:-3]}")
            except:
                await ctx.respond(f"Failed to reload all cogs")
        await ctx.respond(f"Reloaded all cogs")

run_async(database.init())
loop = asyncio.new_event_loop()
loop.create_task(client.start(config.get("DISCORD", "TOKEN")))
try:
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.close()
    print("\nShutting down...")

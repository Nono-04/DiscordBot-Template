import datetime
import json
import time
from os import path
import os.path

import aiofiles as aiofiles
import aiohttp
import discord
from discord.ext import commands, tasks
from modules import config


async def generateToken(session) -> dict:
    data = {
        'client_id': config.get("TWITCH", "clientId"),
        'client_secret': config.get("TWITCH", "clientSecret"),
        'grant_type': 'client_credentials'
    }
    async with session.post(f"https://id.twitch.tv/oauth2/token?", params=data) as resp:
        data = await resp.json()
        expires_in = datetime.datetime.now() + datetime.timedelta(seconds=data["expires_in"])
        data["expires_in"] = int(expires_in.utcnow().timestamp())
        async with aiofiles.open("cache/twitchoauth.json", "w") as f:
            await f.write(json.dumps(data))
        return data


async def getToken(session) -> dict:
    if path.exists("cache/twitchoauth.json"):
        async with aiofiles.open("cache/twitchoauth.json", "r") as f:
            access_token = json.loads(await f.read())
            if int(datetime.datetime.now().timestamp()) < access_token["expires_in"]:  # if token is still valid
                return access_token["access_token"]
            return (await generateToken(session))["access_token"]
    else:
        return (await generateToken(session))["access_token"]


async def getStream(session: aiohttp.ClientSession, user_login: str = config.get("TWITCH", "twitchChannel")) -> dict:
    access_token = await getToken(session)
    params2 = {
        'Authorization': f'Bearer {access_token}',
        'client_id': config.get("TWITCH", "clientId"),
        'client_secret': config.get("TWITCH", "clientSecret"),
        'user_login': user_login
    }
    headers = {
        'Authorization': f'Bearer {access_token}',
        'client-id': config.get("TWITCH", "clientId"),
        'client-secret': config.get("TWITCH", "clientSecret"),
    }
    async with session.get(f"https://api.twitch.tv/helix/streams", params=params2, headers=headers) as resp2:
        stream = await resp2.json()
        return stream


async def getCache() -> dict:
    async with aiofiles.open("cache/twitch.json", "r") as f:
        return json.loads(await f.read())


async def setCache(cache):
    async with aiofiles.open("cache/twitch.json", "w") as f:
        await f.write(json.dumps(cache))


class Twitch(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client
        self.twitch_check.start()

        self.wentLive = {}

    @tasks.loop(seconds=15)
    async def twitch_check(self):
        await self.client.wait_until_ready()
        async with aiohttp.ClientSession() as session:
            stream = await getStream(session)
            try:
                if (await getCache())["data"][0]["started_at"] == stream["data"][0]["started_at"]:
                    return
            except IndexError:
                pass

            if not stream["data"]:
                await setCache(stream)
                return  # offline

            if stream["data"][0]["type"] == "live":
                try:
                    if stream["data"][0]["started_at"] == (await getCache())["data"][0]["started_at"]:
                        print("Still live")
                        return
                except IndexError:
                    pass

                await setCache(stream)

                print("Stream is live")

                channel = await self.client.fetch_channel(config.get("DISCORD", "twitchChatChannel"))

                embed = discord.Embed(color=0x00ff00)
                embed.add_field(value=f"[Watch the Stream](https://twitch.tv/{stream['data'][0]['user_name']})",
                                name=f"{stream['data'][0]['title']}")
                embed.set_author(name=f"{stream['data'][0]['user_name']} is live now")
                embed.set_image(
                    url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{stream['data'][0]['user_login']}-640x360.jpg")

                await channel.send(f"@everyone", embed=embed)

    @commands.command(name="twitch", description="Get the current stream of the channel")
    async def twitch(self, ctx: commands.Context, *, user_login: str = config.get("TWITCH", "twitchChannel")):
        async with aiohttp.ClientSession() as session:
            await self.client.wait_until_ready()
            stream = await getStream(session, user_login)
            if stream["data"]:
                if stream["data"][0]["type"] == "live":
                    embed = discord.Embed(color=0x00ff00)
                    embed.add_field(value=stream["data"][0]["title"],
                                    name="Title:")
                    embed.set_author(name=f"{user_login} is live")
                    embed.set_image(
                        url=f"https://static-cdn.jtvnw.net/previews-ttv/live_user_{stream['data'][0]['user_login']}-640x360.jpg")

                    embed.set_footer(
                        text=f"{stream['data'][0]['game_name']} with {stream['data'][0]['viewer_count']} viewers")

                    await ctx.reply(embed=embed, mention_author=True)
            else:
                await ctx.reply(user_login + " is not live", mention_author=True)


def setup(client):
    client.add_cog(Twitch(client))

from datetime import datetime

import aiohttp
import discord
from discord.ext import commands

from modules import checks
import modules

TIME_DURATION_UNITS = (
    ('week', 60 * 60 * 24 * 7),
    ('day', 60 * 60 * 24),
    ('hour', 60 * 60),
    ('min', 60),
    ('sec', 1)
)


def human_time_duration(seconds):
    if seconds == 0:
        return 'inf'
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{} {}{}'.format(amount, unit, "" if amount == 1 else "s"))
    return ', '.join(parts)


async def getPajbotUser(session: aiohttp.ClientSession, userLogin: str):
    async with session.get(modules.config.get("PAJBOT", "API") + f"users/{userLogin}") as resp:
        if resp.status == 200:
            return await resp.json(), resp.status
        else:
            return {}, resp.status


class Pajbot(commands.Cog):
    def __init__(self, client):
        self.client: commands.Bot = client

    @commands.command(name="watchtime", description="Get your watchtime from the Chat")
    async def watchtime(self, ctx: commands.Context, user_login: str = None):
        if await checks.simpleChannelCheck(ctx) is False:
            return
        if user_login is None:
            return await ctx.reply("Please provide a Twitch username.")
        async with aiohttp.ClientSession() as session:
            await self.client.wait_until_ready()
            pajbotUser = await getPajbotUser(session, user_login.lower())
            if pajbotUser[1] == 404:
                return await ctx.reply("This user does not exist.")
            elif pajbotUser[1] != 404 and pajbotUser[1] != 200:
                return await ctx.reply("Something went wrong.")
            data = pajbotUser[0]
            if data["ignored"] is True:
                return await ctx.reply("This user does not exist.")

            embed = discord.Embed(colour=discord.Colour.red(), title="Watchtime",
                                  description=f"{data['name']}'s watchtime is {human_time_duration(data['time_in_chat_online'])}.")
            embed.set_footer(
                text=f"In Offlinechat {data['name']}'s has a watchtime of {human_time_duration(data['time_in_chat_offline'])}.")

            await ctx.reply(embed=embed)

    @commands.command(name="points", description="Get your points from the Chat")
    async def points(self, ctx: commands.Context, user_login: str = None):
        if await checks.simpleChannelCheck(ctx) is False:
            return
        if user_login is None:
            return await ctx.reply("Please provide a Twitch username.")
        async with aiohttp.ClientSession() as session:
            await self.client.wait_until_ready()
            pajbotUser = await getPajbotUser(session, user_login.lower())
            if pajbotUser[1] == 404:
                return await ctx.reply("This user does not exist.")
            elif pajbotUser[1] != 404 and pajbotUser[1] != 200:
                return await ctx.reply("Something went wrong.")
            data = pajbotUser[0]
            if data["ignored"] is True:
                return await ctx.reply("This user does not exist.")
            embed = discord.Embed(colour=discord.Colour.red(), title="Points",
                                  description=f"{data['name']}'s has {data['points']} Points in Chat.")
            embed.set_footer(text=f"{data['name']} is #{data['points_rank']} on the Leaderboard.")
            await ctx.reply(embed=embed)

    @commands.command(name="lastseen", description="Get the last time someone were seen on the Chat")
    async def lastseen(self, ctx: commands.Context, user_login: str = None):
        if await checks.simpleChannelCheck(ctx) is False:
            return
        if user_login is None:
            return await ctx.reply("Please provide a Twitch username.")
        async with aiohttp.ClientSession() as session:
            await self.client.wait_until_ready()
            pajbotUser = await getPajbotUser(session, user_login.lower())
            if pajbotUser[1] == 404:
                return await ctx.reply("This user does not exist.")
            elif pajbotUser[1] != 404 and pajbotUser[1] != 200:
                return await ctx.reply("Something went wrong.")
            data = pajbotUser[0]
            if data["ignored"] is True:
                return await ctx.reply("This user does not exist.")

            if data["last_seen"] is None:
                return await ctx.reply("This user has never been seen.")

            timeDiffLastSeen = datetime.now().timestamp() - datetime.strptime(
                data['last_seen'],
                '%Y-%m-%dT%H:%M:%S.%f%z').timestamp()
            timeDiffLastActive = datetime.now().timestamp() - datetime.strptime(
                data['last_active'],
                '%Y-%m-%dT%H:%M:%S.%f%z').timestamp()

            embed = discord.Embed(colour=discord.Colour.red(), title="Last Seen",
                                  description=f"{data['name']} was last seen {human_time_duration(timeDiffLastSeen)} ago.")
            embed.set_footer(
                text=f"The last activity of {data['name']} was {human_time_duration(timeDiffLastActive)} ago.")

            await ctx.reply(embed=embed)


def setup(client):
    client.add_cog(Pajbot(client))

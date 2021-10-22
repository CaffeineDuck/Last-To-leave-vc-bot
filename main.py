#!/bin/env python3

import asyncio

import discord
from discord.ext import commands

from bot import Bot
from constants import *

bot = Bot(command_prefix=BOT_PREFIX)


@commands.check_any(
    commands.is_owner(), bot.is_manager(), bot.has_manage_guild_permissions()
)
@bot.command()
async def addmanagers(ctx: commands.Context, members: commands.Greedy[discord.Member]):
    members = [member.id for member in members]
    bot.event_managers.extend(members)
    await ctx.send("Added them as event managers!")


@commands.check_any(
    commands.is_owner(), bot.is_manager(), bot.has_manage_guild_permissions()
)
@bot.command()
async def managers(ctx: commands.Context):
    await ctx.send(
        ", ".join([f"{bot.get_user(member).mention}" for member in bot.event_managers])
        if bot.event_managers
        else "There are no managers yet!"
    )


@commands.check_any(
    commands.is_owner(), bot.is_manager(), bot.has_manage_guild_permissions()
)
@bot.command()
async def addwords(ctx: commands.Context, *words):
    bot.random_words.extend(words)
    await ctx.send("New random words added to this list!")


@commands.check_any(
    commands.is_owner(), bot.is_manager(), bot.has_manage_guild_permissions()
)
@bot.command()
async def start(ctx: commands.Context):
    if bot.event_started:
        raise commands.CommandError("LTLVC has already started!")

    if not bot.random_words:
        raise commands.CommandError("Random words have not yet been added!")

    bot.event_started = True
    asyncio.create_task(bot.message_check())

    ltlvc_channel = bot.get_channel(EVENT_LOGGING_CHANNEL_ID)
    general_channel = bot.get_channel(GENERAL_ID)

    embed = discord.Embed(
        description="**Last To Leave VC Event** has started!", title="EVENT STARTED"
    )

    await general_channel.send(embed=embed)
    await ltlvc_channel.send(embed=embed)
    await ctx.send("LTLVC event has been started!")


@commands.check_any(
    commands.is_owner(), bot.is_manager(), bot.has_manage_guild_permissions()
)
@bot.command()
async def stop(ctx: commands.Context):
    bot.event_started = False
    ltlvc_channel = bot.get_channel(EVENT_LOGGING_CHANNEL_ID)

    await ltlvc_channel.send(
        embed=discord.Embed(
            description="**Last To Leave VC Event** has ended!", title="EVENT ENDED"
        )
    )
    await ctx.send("LTLVC event stopped!")


@commands.check_any(
    commands.is_owner(), bot.is_manager(), bot.has_manage_guild_permissions()
)
@bot.command()
async def cwaittime(ctx: commands.Context, time_limit: int) -> None:
    global DM_TIME_LIMIT
    DM_TIME_LIMIT = time_limit
    await ctx.send(f"Time limit has been changed to {time_limit} seconds")


@commands.check_any(
    commands.is_owner(), bot.is_manager(), bot.has_manage_guild_permissions()
)
@bot.command()
async def crandomtime(
    ctx: commands.Context, first_number: int, second_number: int
) -> None:
    global TIME_LIMIT
    TIME_LIMIT = (first_number, second_number)
    await ctx.send(
        f"DM check random time will be done between {first_number}m and {second_number}m."
    )


@bot.command()
async def timeinfo(ctx: commands.Context) -> None:
    await ctx.send(
        f"DM Wait Time: {DM_TIME_LIMIT}s \nRandom DM Check Time: {TIME_LIMIT}m"
    )


@bot.command()
async def participants(ctx: commands.Context):
    members = len(bot.ltlvc_participants)
    await ctx.send(f"There are {members} participants left!")


@bot.command()
async def words(ctx: commands.Context):
    await ctx.send(
        ", ".join(bot.random_words)
        if bot.random_words
        else "There are no random words yet."
    )


if __name__ == "__main__":
    bot.run(BOT_TOKEN)

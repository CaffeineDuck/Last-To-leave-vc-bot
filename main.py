import random
from typing import List
import discord
from discord.ext import commands, tasks
import asyncio

from constants import *


event_managers = []
random_words = [
    "pegyan",
    "sussy",
    "nou",
    "heheboi",
    "gib moni",
    "nitro",
    "spotify",
    "uwu",
    "smh",
    "baun",
    "ikiru",
    "nettles",
]
time_interval = (15, 25)
event_started = False
event_bot_kicked_users = []

bot = commands.Bot(command_prefix="lt!", intents=discord.Intents.all())


async def dm_random_check(self, member: discord.Member) -> None:
    logging_channel = await member.guild.get_channel(EVENT_LOGGING_CHANNEL_ID)

    word = random.choice(random_words)

    def msg_check(m):
        return m.content.lower() == word and m.author.id == member.id

    try:
        await member.send(
            f"Reply with `{word}` within the next 120 seconds or get kicked!"
        )
    except discord.Forbidden:
        await logging_channel.send(
            f"{member.mention} **Reply this msg with** `{word}` withing the next 120 secs or get kicked!"
        )

    try:
        await self.bot.wait_for("message", check=msg_check, timeout=120)
        await member.send("You passed the AFK check!")
    except asyncio.TimeoutError:
        embed = discord.Embed(
            title=f"Member Kicked From The Event!",
            description=f"{member.mention} was kicked from the ltlvc event, as the member didn't reply to DMs!",
            color=discord.Color.red(),
        )
        event_bot_kicked_users.append(member.id)

        await member.move_to(
            channel=None,
            reason="Member didn't respond in time for the LTLVC DM check!",
        )
        await logging_channel.send(embed=embed)


@tasks.loop(minutes=random.randrange(*time_interval))
async def message_check():
    if not event_started:
        return
    guild = bot.get_guild(GUILD_ID)

    ltlvc_praticipants: List[discord.Member] = [
        member
        for member in (
            discord.utils.get(guild.roles, name="LtlVC Participants")
        ).members
        if not member.bot and member.id not in event_managers
    ]

    for member in ltlvc_praticipants:
        asyncio.create_task(dm_random_check(member))


@bot.event
async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    if member.id in event_managers:
        return

    before_channel_id = getattr(before.channel, "id", None)
    after_channel_id = getattr(after.channel, "id", None)
    
    ltlvc_role = await member.guild.get_role(LTLVC_ROLE_ID)
    logging_channel = await member.guild.get_channel(EVENT_LOGGING_CHANNEL_ID)
    embed = None

    if after_channel_id != EVENT_VOICE_CHANNEL_ID:
        embed = discord.Embed(
            title=f"{member} Left",
            description=f"{member.mention} left the LTLVC event!",
            color=discord.Color.green(),
        )
        await member.add_roles(ltlvc_role)
    elif (
        after_channel_id == EVENT_VOICE_CHANNEL_ID
        and before_channel_id != EVENT_VOICE_CHANNEL_ID
    ):
        embed = discord.Embed(
            title=f"{member} Joined",
            description=f"{member.mention} joined the LTLVC event!",
            color=discord.Color.red(),
        )
        await member.remove_roles(ltlvc_role)

    if embed:
        await logging_channel.send(embed)


@bot.group()
async def ltlvc(ctx: commands.Context):
    pass

@ltlvc.command()
async def setup(ctx: commands.Context):
    pass

@ltlvc.command()
async def addwords(ctx: commands.Context, *words):
    pass

@ltlvc.command()
async def start(ctx: commands.Context):
    pass

@ltlvc.command()
async def changeinterval(ctx: commands.Context, start: int, end:int):
    pass
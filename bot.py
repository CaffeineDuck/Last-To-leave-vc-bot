import asyncio
import random
import re
from typing import List

import discord
from discord.ext import commands

from constants import *


class Bot(commands.Bot):
    def __init__(self, command_prefix: str):
        super().__init__(command_prefix=command_prefix, intents=discord.Intents.all())
        self.event_started = False
        self.random_words = []
        self.event_bot_kicked_users = []
        self.event_managers = []

        self.load_extension("jishaku")

    def is_manager(self):
        def predicate(ctx):
            return ctx.message.author.id in self.event_managers

        return commands.check(predicate)

    def has_manage_guild_permissions(self):
        def predicate(ctx: commands.Context):
            author_perms: discord.Permissions = ctx.channel.permissions_for(ctx.author)
            return ctx.guild is not None and author_perms.manage_guild

        return commands.check(predicate)

    async def dm_random_check(self, member: discord.Member) -> None:
        logging_channel = member.guild.get_channel(EVENT_LOGGING_CHANNEL_ID)
        general_channel = member.guild.get_channel(GENERAL_ID)

        word = random.choice(self.random_words)

        def msg_check(m):
            return m.content.lower() == word.lower() and m.author.id == member.id

        message = f"{member.mention} Reply with `{word}` within the next `{DM_TIME_LIMIT}` seconds or get disconnected!"
        try:
            await member.send(message)
        except discord.Forbidden:
            await general_channel.send(message)

        try:
            await self.wait_for("message", check=msg_check, timeout=DM_TIME_LIMIT)
            await logging_channel.send(f"{member.mention} passed the AFK check!")

            try:
                await member.send("You passed the afk check!")
            except discord.Forbidden:
                pass
                
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"Member Kicked From The Event!",
                description=f"{member.mention} was kicked from the ltlvc event, as the member didn't reply to DMs!",
                color=discord.Color.red(),
            )
            embed.set_footer(text=member.id)
            self.event_bot_kicked_users.append(member.id)

            await member.move_to(
                channel=None,
                reason="Member didn't respond in time for the LTLVC DM check!",
            )
            await logging_channel.send(embed=embed)

    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member.id in self.event_managers:
            return

        if member.id in self.event_bot_kicked_users:
            return

        before_channel_id = getattr(before.channel, "id", None)
        after_channel_id = getattr(after.channel, "id", None)

        ltlvc_role = member.guild.get_role(LTLVC_ROLE_ID)
        logging_channel = member.guild.get_channel(EVENT_LOGGING_CHANNEL_ID)
        embed = None

        if (
            after_channel_id != EVENT_VOICE_CHANNEL_ID
            and before_channel_id == EVENT_VOICE_CHANNEL_ID
        ):

            embed = discord.Embed(
                title=f"{member} Left",
                description=f"{member.mention} left the LTLVC event!",
                color=discord.Color.red(),
            )
            embed.set_footer(text=member.id)
            await member.remove_roles(ltlvc_role)
        elif (
            after_channel_id == EVENT_VOICE_CHANNEL_ID
            and before_channel_id != EVENT_VOICE_CHANNEL_ID
        ):
            embed = discord.Embed(
                title=f"{member} Joined",
                description=f"{member.mention} joined the LTLVC event!",
                color=discord.Color.green(),
            )
            embed.set_footer(text=member.id)
            await member.add_roles(ltlvc_role)

        if embed:
            await logging_channel.send(embed=embed)

    async def on_ready(self):
        print(f"Logged in with {self.user.name}")

    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ):
        if isinstance(error, commands.BotMissingPermissions):
            return await ctx.reply(
                f"I am missing the following permissions:\n **{','.join(error.missing_perms)}**"
            )
        elif isinstance(error, commands.MissingPermissions):
            return await ctx.reply(
                f"You are missing the following permissions:\n**{','.join(error.missing_perms)}**"
            )
        else:
            title = " ".join(
                re.compile(r"[A-Z][a-z]*").findall(error.__class__.__name__)
            )
            return await ctx.send(
                embed=discord.Embed(
                    title=title, description=str(error), color=discord.Color.red()
                )
            )

    @property
    def ltlvc_participants(self) -> List[discord.Member]:
        guild = self.get_guild(GUILD_ID)
        ltlvc_role = guild.get_role(LTLVC_ROLE_ID)

        return [
            member
            for member in ltlvc_role.members
            if not member.bot and member.id not in self.event_managers
        ]

    async def message_check(self):
        while self.event_started:

            for member in self.ltlvc_participants:
                asyncio.create_task(self.dm_random_check(member))

            await asyncio.sleep(random.randrange(*[limit * 60 for limit in TIME_LIMIT]))

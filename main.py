import asyncio
import random
import re
from typing import List

import discord
from discord.ext import commands, tasks

from constants import *


class Bot(commands.Bot):
    def __init__(self, command_prefix: str):
        super().__init__(command_prefix=command_prefix, intents=discord.Intents.all())
        self.event_started = False
        self.random_words = [
            "pegyan",
            "sussy",
            "nou",
            "heheboi",
            "moni",
            "nitro",
            "spotify",
            "uwu",
            "smh",
            "baun",
            "ikiru",
            "nettles",
        ]

        self.event_bot_kicked_users = []
        self.event_managers = []

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

        await general_channel.send(
            f"{member.mention} Reply with `{word}` within the next 500 seconds or get disconnected!"
        )

        try:
            await self.wait_for("message", check=msg_check, timeout=500)
            await general_channel.send(f"{member.mention} passed the AFK check!")
        except asyncio.TimeoutError:
            embed = discord.Embed(
                title=f"Member Kicked From The Event!",
                description=f"{member.mention} was kicked from the ltlvc event, as the member didn't reply to DMs!",
                color=discord.Color.red(),
            )
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

    @tasks.loop(minutes=random.randrange(15, 25))
    async def message_check(self):
        if not self.event_started:
            return

        guild = self.get_guild(GUILD_ID)
        ltlvc_role = guild.get_role(LTLVC_ROLE_ID)

        ltlvc_praticipants: List[discord.Member] = [
            member
            for member in ltlvc_role.members
            if not member.bot and member.id not in self.event_managers
        ]

        for member in ltlvc_praticipants:
            asyncio.create_task(self.dm_random_check(member))


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
    try:
        await ctx.send(
            ", ".join(
                [f"{bot.get_user(member).mention}" for member in bot.event_managers]
            )
        )
    except discord.HTTPException:
        await ctx.send("There are no managers yet!")


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
async def words(ctx: commands.Context):
    await ctx.send(", ".join(bot.random_words))


@commands.check_any(
    commands.is_owner(), bot.is_manager(), bot.has_manage_guild_permissions()
)
@bot.command()
async def start(ctx: commands.Context):
    bot.event_started = True

    try:
        bot.message_check.start()
    except RuntimeError:
        bot.message_check.restart()

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
    bot.message_check.stop()
    ltlvc_channel = bot.get_channel(EVENT_LOGGING_CHANNEL_ID)

    await ltlvc_channel.send(
        embed=discord.Embed(
            description="**Last To Leave VC Event** has ended!", title="EVENT ENDED"
        )
    )
    await ctx.send("LTLVC event stopped!")


@bot.command()
async def participants(ctx: commands.Context):
    members = len(
        [
            member
            for member in ctx.guild.get_role(LTLVC_ROLE_ID).members
            if member.bot not in bot.event_managers
        ]
    )
    await ctx.send(f"There are {members} participants left!")


if __name__ == "__main__":
    bot.run(BOT_TOKEN)

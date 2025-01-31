# Imports
import os
import os.path
import json
import time
import datetime
import discord
import asyncio
import api.auth
from utils import logger, ping
from math import floor
from random import randint
from framework.isobot import currency, colors, settings
from framework.isobot.db import levelling
from discord import ApplicationContext, option
from discord.ext import commands
from cogs.economy import new_userdat
from cogs.isocoin import create_isocoin_key

# Slash option types:
# Just use variable types to define option types.
# For example, if the option has to be only str:
# @option(name="something", description="A description", type=str)

#Variables
client = discord.Bot()
color = discord.Color.random()
with open('database/items.json', 'r', encoding="utf-8") as f: items = json.load(f)
with open('config/shop.json', 'r', encoding="utf-8") as f: shopitem = json.load(f)
with open('database/presence.json', 'r', encoding="utf-8") as f: presence = json.load(f)
with open('config/commands.json', 'r', encoding="utf-8") as f: commandsdb = json.load(f)
with open('database/automod.json', 'r', encoding="utf-8") as f: automod_config = json.load(f)
cmd_list = commandsdb.keys()

#Pre-Initialization Commands
def save():
    """Dumps all cached data to the local databases."""
    with open('database/items.json', 'w+', encoding="utf-8") as e: json.dump(items, e, indent=4)
    with open('database/presence.json', 'w+', encoding="utf-8") as e: json.dump(presence, e, indent=4)
    with open('database/automod.json', 'w+', encoding="utf-8") as e: json.dump(automod_config, e, indent=4)

if not os.path.isdir("logs"):
    os.mkdir('logs')
    try:
        open('logs/info-log.txt', 'x', encoding="utf-8")
        logger.info("Created info log", nolog=True)
        time.sleep(0.5)
        open('logs/error-log.txt', 'x', encoding="utf-8")
        logger.info("Created error log", nolog=True)
        time.sleep(0.5)
        open('logs/currency.log', 'x', encoding="utf-8")
        logger.info("Created currency log", nolog=True)
    except IOError as e:
        logger.error(f"Failed to make log file: {e}", nolog=True)

#Framework Module Loader
colors = colors.Colors()
currency = currency.CurrencyAPI("database/currency.json", "logs/currency.log")
settings = settings.Configurator()
levelling = levelling.Levelling()

# Theme Loader
themes = False  # True: enables themes; False: disables themes;

if themes:
    with open("themes/halloween.theme.json", 'r', encoding="utf-8") as f:
        theme = json.load(f)
        try:
            color_loaded = theme["theme"]["embed_color"]
            color = int(color_loaded, 16)
        except KeyError:
            print(f"{colors.red}The theme file being loaded might be broken. Rolling back to default configuration...{colors.end}")
            color = discord.Color.random()
else: color = discord.Color.random()

#Events
@client.event
async def on_ready():
    """This event is fired when the bot client is ready"""
    print("""
Isobot  Copyright (C) 2022  PyBotDevs/NKA
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions.
__________________________________________________""")
    time.sleep(1)
    print(f'[main/Client] Logged in as {client.user.name}.\n[main/Client] Ready to accept commands.')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="GitHub"), status=discord.Status.idle)
    print(f'[main/Log] {colors.green}Status set to IDLE. Rich presence set.{colors.end}')
    print("[main/Flask] Starting pinger service...")
    ping.host()
    time.sleep(5)

@client.event
async def on_message(ctx):
    """This event is fired whenever a message is sent (in a readable channel)"""
    currency.new_wallet(ctx.author.id)
    currency.new_bank(ctx.author.id)
    create_isocoin_key(ctx.author.id)
    new_userdat(ctx.author.id)
    settings.generate(ctx.author.id)
    if str(ctx.author.id) not in items:
        items[str(ctx.author.id)] = {}
    levelling.generate(ctx.author.id)
    if str(ctx.guild.id) not in automod_config:
        automod_config[str(ctx.guild.id)] = {
            "swear_filter": {
                "enabled": False,
                "keywords": {
                    "use_default": True,
                    "default": ["fuck", "shit", "pussy", "penis", "cock", "vagina", "sex", "moan", "bitch", "hoe", "nigga", "nigger", "xxx", "porn"],
                    "custom": []
                }
            }
        }
    for z in shopitem:
        if z in items[str(ctx.author.id)]: pass
        else: items[str(ctx.author.id)][str(z)] = 0
    save()
    uList = list()
    if str(ctx.guild.id) in presence:
        for userid in presence[str(ctx.guild.id)].keys(): uList.append(userid)
    else: pass
    for user in uList:
        if user in ctx.content and not ctx.author.bot:
            fetch_user = client.get_user(id(user))
            await ctx.channel.send(f"{fetch_user.display_name} went AFK <t:{floor(presence[str(ctx.guild.id)][str(user)]['time'])}:R>: {presence[str(ctx.guild.id)][str(user)]['response']}")
    if str(ctx.guild.id) in presence and str(ctx.author.id) in presence[str(ctx.guild.id)]:
        del presence[str(ctx.guild.id)][str(ctx.author.id)]
        save()
        m1 = await ctx.channel.send(f"Welcome back {ctx.author.mention}. Your AFK has been removed.")
        await asyncio.sleep(5)
        await m1.delete()
    if not ctx.author.bot:
        levelling.add_xp(ctx.author.id, randint(1, 5))
        xpreq = 0
        for level in range(levelling.get_level(ctx.author.id)):
            xpreq += 50
            if xpreq >= 5000: break
        if levelling.get_xp(ctx.author.id) >= xpreq:
            levelling.set_xp(ctx.author.id, 0)
            levelling.add_levels(ctx.author.id, 1)
            if settings.fetch_setting(ctx.author.id, "levelup_messages") is True:
                await ctx.author.send(f"{ctx.author.mention}, you just ranked up to **level {levelling.get_level(ctx.author.id)}**. Nice!")
        save()
        if automod_config[str(ctx.guild.id)]["swear_filter"]["enabled"] is True:
            if automod_config[str(ctx.guild.id)]["swear_filter"]["keywords"]["use_default"] and any(x in ctx.content.lower() for x in automod_config[str(ctx.guild.id)]["swear_filter"]["keywords"]["default"]):
                await ctx.delete()
                await ctx.channel.send(f'{ctx.author.mention} watch your language.', delete_after=5)
            elif automod_config[str(ctx.guild.id)]["swear_filter"]["keywords"]["custom"] != [] and any(x in ctx.content.lower() for x in automod_config[str(ctx.guild.id)]["swear_filter"]["keywords"]["custom"]):
                await ctx.delete()
                await ctx.channel.send(f'{ctx.author.mention} watch your language.', delete_after=5)

#Error handler
@client.event
async def on_application_command_error(ctx: ApplicationContext, error: discord.DiscordException):
    """An event handler to handle command exceptions when things go wrong."""
    current_time = datetime.time().strftime("%H:%M:%S")
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.respond(f":stopwatch: Not now! Please try after **{str(datetime.timedelta(seconds=int(round(error.retry_after))))}**")
        print(f"[{current_time}] Ignoring exception at {colors.cyan}CommandOnCooldown{colors.end}. Details: This command is currently on cooldown.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.respond("You don't have permission to do this!", ephemeral=True)
        print(f"[{current_time}] Ignoring exception at {colors.cyan}MissingPermissions{colors.end}. Details: The user doesn\'t have the required permissions.")
    elif isinstance(error, commands.BadArgument):
        await ctx.respond(":x: Invalid argument.", delete_after=8)
        print(f"[{current_time}] Ignoring exception at {colors.cyan}BadArgument{colors.end}.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.respond(":x: I don\'t have the required permissions to use this.")
        print(f"[{current_time}] Ignoring exception at {colors.cyan}BotMissingPremissions{colors.end}. Details: The bot doesn\'t have the required permissions.")
    elif isinstance(error, commands.BadBoolArgument):
        await ctx.respond(":x: Invalid true/false argument.", delete_after=8)
        print(f"[{current_time}] Ignoring exception at {colors.cyan}BadBoolArgument{colors.end}.")
    else:
        await ctx.respond(f"An uncaught error occured while running the command.\n```\n{error}\n```")

#Commands
@client.slash_command(
    name="help",
    description="Gives you help with a specific command, or shows a list of all commands"
)
@option(name="command", description="Which command do you need help with?", type=str, default=None)
async def help(ctx: ApplicationContext, command: str = None):
    """Gives you help with a specific command, or shows a list of all commands"""
    if command is not None:
        try:
            localembed = discord.Embed(
                title=f"{commandsdb[command]['name']} Command (/{command})",
                description=commandsdb[command]['description'],
                color=color
            )
            localembed.add_field(name="Command Type", value=commandsdb[command]['type'], inline=False)
            if commandsdb[command]['cooldown'] is not None:
                localembed.add_field(name="Cooldown", value=f"{str(datetime.timedelta(seconds=commandsdb[command]['cooldown']))}", inline=False)
            localembed.add_field(name="Usable By", value=commandsdb[command]['usable_by'], inline=False)
            if commandsdb[command]['args'] is not None:
                args = ""
                for arg in commandsdb[command]['args']: args += f"`{arg}` "
                localembed.add_field(name="Arguments", value=args, inline=False)
            if commandsdb[command]['bugged'] is True:
                localembed.set_footer(text="⚠ This command might be bugged (experiencing issues), but will be fixed later.")
            if commandsdb[command]['disabled'] is True:
                localembed.set_footer(text="⚠ This command is currently disabled")
            await ctx.respond(embed=localembed)
        except KeyError:
            return await ctx.respond(
                embed=discord.Embed(description=f"No results found for {command}."),
                ephemeral=True
            )
    else:
        commands_list = ""
        for _command in commandsdb:
            if commandsdb[_command]["type"] != "DevTools": commands_list += f"`/{_command}`\n"
        localembed = discord.Embed(title="Isobot Command Help", description=f"**Bot Commands:**\n{commands_list}", color = color)
        await ctx.author.send(embed=localembed)
        await ctx.respond("Check your direct messages.", ephemeral=True)

# Cog Commands (these cannot be moved into a cog)
cogs = client.create_group("cog", "Commands for working with isobot cogs.")

@cogs.command(
    name="load",
    description="Loads a cog."
)
@option(name="cog", description="What cog do you want to load?", type=str)
async def load(ctx: ApplicationContext, cog: str):
    """Loads a cog."""
    if ctx.author.id != 738290097170153472:
        return await ctx.respond("You can't use this command!", ephemeral=True)
    try:
        client.load_extension(f"cogs.{cog}")
        await ctx.respond(
            embed=discord.Embed(
                description=f"{cog} cog successfully loaded.",
                color=discord.Color.green()
            )
        )
    except discord.errors.ExtensionNotFound:
        return await ctx.respond(
            embed=discord.Embed(
                title=f"{cog} failed to load",
                description="Cog does not exist.",
                color=discord.Color.red()
            )
        )
    except discord.errors.ExtensionAlreadyLoaded:
        return await ctx.respond(
            embed=discord.Embed(
                title=f"{cog} failed to load",
                description="Cog does not exist.",
                color=discord.Color.red()
            )
        )

@cogs.command(
    name="disable",
    description="Disables a cog."
)
@option(name="cog", description="What cog do you want to disable?", type=str)
async def disable(ctx: ApplicationContext, cog: str):
    """Disables a cog."""
    if ctx.author.id != 738290097170153472:
        return await ctx.respond("You can't use this command!", ephemeral=True)
    try:
        client.unload_extension(f"cogs.{cog}")
        await ctx.respond(
            embed=discord.Embed(
                description=f"{cog} cog successfully disabled.",
                color=discord.Color.green()
            )
        )
    except discord.errors.ExtensionNotFound:
        return await ctx.respond(
            embed=discord.Embed(
                title=f"{cog} failed to disable",
                description="Cog does not exist.",
                color=discord.Color.red()
            )
        )

@cogs.command(
    name="reload",
    description="Reloads a cog."
)
@option(name="cog", description="What cog do you want to reload?", type=str)
async def reload(ctx: ApplicationContext, cog: str):
    """Reloads a cog."""
    if ctx.author.id != 738290097170153472:
        return await ctx.respond("You can't use this command!", ephemeral=True)
    try:
        client.reload_extension(f"cogs.{cog}")
        await ctx.respond(
            embed=discord.Embed(
                description=f"{cog} cog successfully reloaded.",
                color=discord.Color.green()
            )
        )
    except discord.errors.ExtensionNotFound:
        return await ctx.respond(
            embed=discord.Embed(
                title=f"{cog} failed to reload",
                description="Cog does not exist.",
                color=discord.Color.red()
            )
        )

# Settings commands
config = client.create_group("settings", "Commands used to change bot settings.")

@config.command(
    name="levelup_messages",
    description="Configure whether you want to be notified for level ups or not."
)
@option(name="enabled", description="Do you want this setting enabled?", type=bool)
async def levelup_messages(ctx: ApplicationContext, enabled: bool):
    """Configure whether you want to be notified for level ups or not."""
    if settings.fetch_setting(ctx.author.id, "levelup_messages") == enabled:
        return await ctx.respond("This is already done.", ephemeral=True)
    settings.edit_setting(ctx.author.id, "levelup_messages", enabled)
    localembed = discord.Embed(
        description="Setting successfully updated.",
        color=discord.Color.green()
    )
    await ctx.respond(embed=localembed)

# Initialization
active_cogs = [
    "economy",
    "maths",
    "reddit",
    "moderation",
    "minigames",
    "automod",
    "isobank",
    "levelling",
    "fun",
    "utils",
    "afk",
    "osu",
    "weather",
    "isocard"
]
i = 1
cog_errors = 0
for x in active_cogs:
    print(f"[main/Cogs] Loading isobot Cog ({i}/{len(active_cogs)})")
    i += 1
    try: client.load_extension(f"cogs.{x}")
    except discord.errors.ExtensionFailed as e:
        cog_errors += 1
        print(f"[main/Cogs] {colors.red}ERROR: Cog '{x}' failed to load: {e}{colors.end}")
if cog_errors == 0: print(f"[main/Cogs] {colors.green}All cogs successfully loaded.{colors.end}")
else: print(f"[main/Cogs] {colors.yellow}{cog_errors}/{len(active_cogs)} cogs failed to load.{colors.end}")
print("--------------------")
if api.auth.get_mode():
    print(f"[main/Client] Starting client in {colors.cyan}Replit mode{colors.end}...")
    client.run(os.getenv("TOKEN"))
else:
    print(f"[main/Client] Starting client in {colors.orange}local mode{colors.end}...")
    client.run(api.auth.get_token())




# btw i use arch

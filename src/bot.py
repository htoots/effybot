#!/usr/bin/env python3
print("Starting discordbot...")

import discord
from discord.ext import commands
import logging,sys,argparse,json

# custom commands
ALLOWED_CHANNELS_ID = []

#TODO: Make this use embeds
#TODO: Make bot remember channels between restarts

async def on_cmd_channel(ctx):
  arg = ctx.args[0] #there should only be one argument for this cmd
  cid = ctx.channel.id
  
  if arg == "start":
    if not cid in ALLOWED_CHANNELS_ID:
      ALLOWED_CHANNELS_ID.append(cid)
      return await ctx.send("Now listening in this channel for commands. :blush:")
    else:
      return await ctx.send("I'm already listening in this channel :wink:")
  elif arg == "stop":
    if cid in ALLOWED_CHANNELS_ID:
      ALLOWED_CHANNELS_ID.remove(cid)
      return await ctx.send("Stopped listening in this channel for commands. :sob:")
    else:
      return await ctx.send("I'm not listening in this channel :blush:")

async def on_cmd_channels(ctx):
  cid = ctx.channel.id
  channels_list = []
  
  for channel_id in ALLOWED_CHANNELS_ID:
    channels_list.append(channel_id)
  
  msg = discord.Embed(title="Channels", description=str(channel_list), color=0xFFFFFF)
  await channel.send(embed=msg)

bot_commands = [
                
                # Channel
                {
                "name": "channel",
                "has_args": True,
                "num_args": 1,
                "valid_args": [
                               "start",
                               "stop"
                               ],
                "on_command": on_cmd_channel
                },
                
                # Channels
                {
                "name": "channels",
                "has_args": False,
                "on_command": on_cmd_channels
                }
                ]

# bot setup

use_console_logging = True
logging_level = logging.DEBUG

logger = logging.getLogger("Discord_Bot")
logger.setLevel(logging_level)

#log file
fh = logging.FileHandler("log.txt")
fh.setLevel(logging_level)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#console log
if use_console_logging:
  ch = logging.StreamHandler()
  ch.setLevel(logging_level)
  ch.setFormatter(formatter)
  logger.addHandler(ch)

fh.setFormatter(formatter)

logger.addHandler(fh)

logger.info("Logging setup successfully")

OWNER_ID = ""
BIG_BRAIN_ID = 421464243339001860
BOT_ERRORS_ID = 0
PREFIX = ""
ping_response = ""
initial_extensions = []
modules = []

TOKEN = ""

ap = argparse.ArgumentParser()
ap.add_argument("-c", "--no-console", required=False, help="Disables console output")
args = vars(ap.parse_args())

if args["no_console"]:
  use_console_logging = False

logger.info("Using Discord.py ({0})".format(discord.__version__))

logger.info("Loading credentials...")

creds = []
with open("configs/bot.json") as f:
  creds = json.load(f)

bot_name = creds["name"]
TOKEN = creds["token"]
OWNER_ID = creds["owner_id"]

logger.info("Loaded credentials")

logger.info("Loading settings...")

settings = []
with open("configs/settings.json") as f:
  settings = json.load(f)

PREFIX = settings["prefix"]
BOT_ERRORS_ID = settings["bot_errors_channel_id"]
ping_response = settings["ping_response"]
ALLOWED_CHANNELS_ID = settings["allowed_channels"]
modules = settings["modules"]

logger.info("Loaded settings")

bot = commands.Bot(command_prefix=PREFIX)

# bot event handling

@bot.event
async def on_command_error(ctx, error):
  if isinstance(error, commands.errors.CommandNotFound):
    return await ctx.send(f"Command not found. Try {PREFIX}help.")
  elif isinstance(error, commands.errors.MissingRequiredArgument):
    return await ctx.send(f"Missing required argument. Try {PREFIX}help {ctx.command.name}")
  elif isinstance(error, commands.errors.BadArgument):
    return await ctx.send(f"Bad argument. Try {PREFIX}help {ctx.command.name}")
  elif isinstance(error, commands.errors.NotOwner):
    msg = discord.Embed(title=":x:", description="You do not have permission to run this command.", color=0xFF0000)
    return await ctx.send(embed=msg)
  elif isinstance(error, commands.DisabledCommand):
    return await ctx.send("That command is currently disabled. Please try again later.")

  await ctx.send("I had an error :sob: Please try again later.")
  channel = bot.get_channel(BOT_ERRORS_ID)
  msg = discord.Embed(title="Command Error", description=str(type(error)), color=0xFF0000)
  msg.add_field(name="Command", value=ctx.message.content, inline=False)
  msg.add_field(name="Error", value=error, inline=False)
  await channel.send(content=f"<@{OWNER_ID}>", embed=msg)
  logger.debug(error)

@bot.event
async def on_voice_state_update(member, before, after):
  if after.channel is not None and after.channel.id == BIG_BRAIN_ID and (before.channel is None or not before.channel.id == BIG_BRAIN_ID):
    await add_to_text(member)
  elif after.channel is None or not after.channel.id == BIG_BRAIN_ID:
    await remove_from_text(member)

async def remove_from_text(user):
  channel = discord.utils.get(user.guild.channels, name="big-text")

  await channel.set_permissions(user, read_messages=False)

async def add_to_text(user):
  channel = discord.utils.get(user.guild.channels, name="big-text") 

  await channel.set_permissions(user, read_messages=True)

@bot.event
async def on_message(message):
  cmd, args = get_command(message)

  if message.author.bot: return
  if bot.user.mentioned_in(message) and (message.content.startswith(f'<@{bot.user.id}>') or message.content.startswith(f'<@!{bot.user.id}>')) and message.mention_everyone is False:
    await message.channel.send(f'{message.author.mention} {ping_response}')
  elif cmd is not None:
    await process_bot_command(message, cmd, args)
  elif message.channel.id in ALLOWED_CHANNELS_ID:
    await bot.process_commands(message)

def get_command(message):
  for cmd in bot_commands:
    cmd_name = f"{PREFIX}{cmd['name']}"
    if message.content.startswith(f"{cmd_name} ") or message.content == f"{cmd_name}":
      args = message.content.split(" ")[1:]

      return cmd, args

  return None, None

async def process_bot_command(message, command, args):
  if command is not None:
    ctx = await bot.get_context(message)
    ctx.command = command
    ctx.args = args

    if command["has_args"]:
      argc = len(ctx.args)
      
      try:
        num_args = command["num_args"]
        if argc != num_args:
          return await ctx.send("Incorrect number of arguments. Needs {0} argument{1}".format(num_args, "s" if num_args > 1 else ""))
      except KeyError as e:
        try:
          min_args = command["min_args"]
          max_args = command["max_args"]

          if argc < min_args:
            return await ctx.send("Not enough arguments. Needs at least {0} argument{1}".format(min_args, "s" if min_args > 1 else ""))
          elif argc > max_args:
            return await ctx.send("Too many arguments. Needs at most {0} argument{1}".format(max_args, "s" if max_args > 1 else ""))
        except KeyError as e:
          return logger.error("Command \"{0}\" not defined correctly. has_args is true, but no arg limit is defined.".format(command["name"]))

      valid_args = command["valid_args"]

      for arg in args:
        if arg not in valid_args:
          return await ctx.send("Invalid argument \"{0}\". Must be one of {1}".format(arg,valid_args))

    on_command_func = ctx.command["on_command"]

    await on_command_func(ctx)

@bot.event
async def on_ready():
  logger.info("Logged in as {0.name} ({0.id})".format(bot.user))
  await bot.change_presence(activity=discord.Game(name="0w0 what's this"))

def main():
  logger.info("Loading initial modules")
  
  for module in modules:
    try:
      if module["enabled"]:
        bot.load_extension(module["filepath"])
        logger.info(f'Loaded module {module["name"]}.')
      else:
        logger.info(f'Skipping loading module: {module["name"]}')
    except ModuleNotFoundError as e:
      logger.warning(f'Failed to load module {module["name"]}.')
      logger.debug(e)

  logger.info("Starting bot")
  bot.run(TOKEN)

if __name__ == "__main__":
  main()

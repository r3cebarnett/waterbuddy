import datetime
import discord
import glob
import logging
import os
import sys
import traceback

from db import model
from cogs import Util, Quirky, Water, Workout, Stats, Timer
from discord.ext import commands
from shared.settings import Settings

from sqlalchemy import create_engine

log = logging.getLogger('waterbuddy')
log.setLevel(logging.DEBUG)
log_sh = logging.StreamHandler(sys.stdout)
log_sh.setLevel(logging.DEBUG)
log_sh.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
log.addHandler(log_sh)
log.debug("waterbuddy (c) 2022 - Maurice Barnett - MIT License")

log.debug('Loading settings...')

settings = Settings('settings.json')
log.debug(f"settings: {settings.get_bulk_str()}")
if not settings.get('prefix'):
    log.debug(f'settings.get("prefix"): {settings.get("prefix")}')
    settings.set1('prefix', '.')
    log.debug('prefix not set in settings.json, setting to "."')
if not settings.get('io_channel'):
    settings.set1('io_channel', 'water')
    log.debug('io_channel not set in settings.json, setting to water')
if not settings.get('admin_role'):
    settings.set1('admin_role', 'r3ce')
    log.debug('admin_role not set in settings.json, setting to r3ce')
if not settings.get('client_token'):
    settings.set1('client_token', '')
    log.debug('client_token not set in settings.json, exiting early')
    settings.save()
    sys.exit(0)
if not settings.get('owner_id'):
    settings.set1('owner_id', '')
    log.debug('owner_id not set in settings.json, exiting early')
    settings.save()
    sys.exit(0)
settings.set1('close_on_purpose', False)

log.debug('Loading database...')

engine = create_engine('sqlite:///' + os.path.abspath('./db/waterbuddy.db')) # create engine in cwd
model.Base.metadata.create_all(engine)
model.Session.configure(bind=engine)

def get_prefix(bot, message):
    return settings.get('prefix')

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.owner_id = settings.get('owner_id')

@bot.event
async def on_ready():
    log.debug(f"We have logged in as {bot.user}")
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name='with 💦'))

@bot.event
async def on_disconnect():
    log.debug('Disconnected...')

@bot.event
async def on_connect():
    log.debug('Connected.')

@bot.event
async def on_error(event, *args, **kwargs):
    log.debug(f"Hit error: {traceback.format_exc()}")

@bot.event
async def setup_hook() -> None:
    log.debug('Loading cogs...')

    await bot.add_cog(Util.Util(bot, settings))
    await bot.add_cog(Quirky.Quirky(bot, settings))
    await bot.add_cog(Water.Water(bot, settings))
    await bot.add_cog(Workout.Workout(bot, settings))
    await bot.add_cog(Stats.Stats(bot, settings))
    await bot.add_cog(Timer.Timer(bot, settings))

    log.debug('Loading events...')

log.debug('Attempting to connect...')
bot.run(settings.get('client_token'))
log.debug('Exited from client.run()')

log.debug('Saving settings...')
settings.save()

if not settings.get('close_on_purpose'):
    log.debug('Attempting to start up bot again.')
    os.system("python main.py")

import datetime
import discord
import logging
import traceback

from cogs import Water
from db import model
from discord.ext import commands
from shared import auxfn

log = logging.getLogger('waterbuddy')

def pretty_print_dict(indict: dict):
    resp = "```\n"

    for key in indict:
        resp += f"{key}:\t"
        for subkey in indict[key]:
            resp += f"{subkey}: {indict[key][subkey]}\t"
        resp += "\n"

    resp += "```"
    return resp

class Stats(commands.Cog):
    def __init__(self, bot: commands.Bot, settings):
        self.bot = bot
        self.settings = settings
        self.name = 'Stats'
    
    async def cog_before_invoke(self, ctx: commands.Context):
        log.debug(f'[STAT] {ctx.command} command issued')

    @commands.command()
    async def daily(self, ctx: commands.Context):
        session = model.Session()
        date = datetime.date.today()
        
        pushup_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=model.WORKOUTS['pushup']).first()
        situp_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=model.WORKOUTS['situp']).first()
        pullup_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=model.WORKOUTS['pullup']).first()
        water_log = session.query(model.Water).filter_by(user_id=ctx.author.id, date=date).first()
        user_settings = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        
        resp = {}
        if water_log:
            resp['Water'] = {}
            resp['Water']['Value'] = Water.vol_print(float(water_log.amount))
            if user_settings and user_settings.water_goal:
                resp['Water']['Goal'] = Water.vol_print(float(user_settings.water_goal))
        if situp_log:
            resp['Situps'] = {}
            resp['Situps']['Value'] = situp_log.amount
            if user_settings and user_settings.situp_goal:
                resp['Situps']['Goal'] = user_settings.situp_goal
        if pullup_log:
            resp['Pullups'] = {}
            resp['Pullups']['Value'] = pullup_log.amount
            if user_settings and user_settings.pullup_goal:
                resp['Pullups']['Goal'] = user_settings.pullup_goal
        if pushup_log:
            resp['Pushups'] = {}
            resp['Pushups']['Value'] = pushup_log.amount
            if user_settings and user_settings.pushup_goal:
                resp['Pushups']['Goal'] = user_settings.pushup_goal

        await ctx.channel.send(f"Stats for {ctx.author.mention} for {date}\n{pretty_print_dict(resp)}")
import datetime
import discord
import logging
import traceback

from cogs import Water, Workout
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
        squat_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=model.WORKOUTS['squat']).first()
        jumpingjack_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=model.WORKOUTS['jumpingjack']).first()
        distance_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=model.WORKOUTS['jumpingjack']).first()
        water_log = session.query(model.Water).filter_by(user_id=ctx.author.id, date=date).first()
        user_settings = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()

        resp = {}
        setting = user_settings and user_settings.water_goal
        if water_log or setting:
            resp['Water'] = {}
            resp['Water']['Value'] = Water.vol_print(float(water_log.amount)) if water_log else 0
            if setting:
                resp['Water']['Goal'] = Water.vol_print(float(user_settings.water_goal))
        setting = user_settings and user_settings.situp_goal
        if situp_log or setting:
            resp['Situps'] = {}
            resp['Situps']['Value'] = situp_log.amount if situp_log else 0
            if setting:
                resp['Situps']['Goal'] = user_settings.situp_goal
        setting = user_settings and user_settings.pullup_goal
        if pullup_log or setting:
            resp['Pullups'] = {}
            resp['Pullups']['Value'] = pullup_log.amount if pullup_log else 0
            if setting:
                resp['Pullups']['Goal'] = user_settings.pullup_goal
        setting = user_settings and user_settings.pushup_goal
        if pushup_log or setting:
            resp['Pushups'] = {}
            resp['Pushups']['Value'] = pushup_log.amount if pushup_log else 0
            if setting:
                resp['Pushups']['Goal'] = user_settings.pushup_goal
        setting = user_settings and user_settings.squat_goal
        if squat_log or setting:
            resp['Squats'] = {}
            resp['Squats']['Value'] = squat_log.amount if squat_log else 0
            if setting:
                resp['Squats']['Goal'] = user_settings.squat_goal
        setting = user_settings and user_settings.jumpingjack_goal
        if jumpingjack_log or setting:
            resp['Jumping Jacks'] = {}
            resp['Jumping Jacks']['Value'] = jumpingjack_log.amount if jumpingjack_log else 0
            if setting:
                resp['Jumping Jacks']['Goal'] = user_settings.jumpingjack_goal
        setting = user_settings and user_settings.distance_goal
        if distance_log or setting:
            resp['Distance'] = {}
            resp['Distance']['Value'] = Workout.dst_print(float(distance_log.amount)) if distance_log else 0
            if setting:
                resp['Distance']['Goal'] = Workout.dst_print(float(user_settings.distance_goal))

        await ctx.channel.send(f"Stats for {ctx.author.mention} for {date}\n{pretty_print_dict(resp)}")
    
    @commands.command()
    async def waterboard(self, ctx: commands.Context):
        session = model.Session()
        date = datetime.date.today()
        results = []

        query = session.query(model.Water).filter_by(date=date)
        for entry in query:
            results.append({
                'User': self.bot.get_user(entry.user_id).name,
                'Value': float(entry.amount)
            })
        
        results = sorted(results, key=lambda res: res['Value'])[::-1]
        msg = f"Water leaderboard as of {datetime.datetime.now()}:\n"
        for place, res in zip(range(1, len(results) + 1), results):
            msg += f"\t{place}: {res['User']} with {Water.vol_print(res['Value'])}\n"
        
        await ctx.channel.send(msg)
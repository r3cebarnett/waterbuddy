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
        distance_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=model.WORKOUTS['distance']['id']).first()
        water_log = session.query(model.Water).filter_by(user_id=ctx.author.id, date=date).first()
        user_settings = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()

        resp = {}
        setting = user_settings and user_settings.water_goal
        if water_log or setting:
            resp['Water'] = {}
            resp['Water']['Value'] = Water.vol_print(float(water_log.amount)) if water_log else 0
            if setting:
                resp['Water']['Goal'] = Water.vol_print(float(user_settings.water_goal))

        for key in model.WORKOUTS:
            if key == 'distance':
                continue
            goal = Workout.get_goal_from_id(user_settings, key) if user_settings else None
            workout_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=model.WORKOUTS[key]['id']).first()
            if workout_log or goal:
                resp[model.WORKOUTS[key]['name']] = {}
                resp[model.WORKOUTS[key]['name']]['Value'] = workout_log.amount if workout_log else 0
                if goal:
                    resp[model.WORKOUTS[key]['name']]['Goal'] = goal

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
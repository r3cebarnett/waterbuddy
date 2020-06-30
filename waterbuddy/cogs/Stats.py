import datetime
import discord
import logging
import traceback

from cogs import Water, Workout
from db import model
from discord.ext import commands
from shared import auxfn

log = logging.getLogger('waterbuddy')

def daily_embed(user: discord.User, info: dict):
    embed = discord.Embed(title=f'Daily Stats for {user.name}')
    embed.set_image(url=user.avatar_url)

    for key in info:
        title = key + (" ✅" if info[key]['Achieved'] else "")
        value = f"Value: {info[key]['Value']}"
        if 'Goal' in info[key]:
            value += f"\nGoal: {info[key]['Goal']}"
        embed.add_field(name=title, value=value, inline=True)

    return embed

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
            resp['Water']['Achieved'] = False
            resp['Water']['Value'] = Water.vol_print(float(water_log.amount)) if water_log else 0
            if setting:
                if water_log and water_log.amount and float(water_log.amount) >= user_settings.water_goal:
                    resp['Water']['Achieved'] = True
                resp['Water']['Goal'] = Water.vol_print(float(user_settings.water_goal))

        for key in model.WORKOUTS:
            if key == 'distance':
                continue
            goal = Workout.get_goal_from_id(user_settings, key) if user_settings else None
            workout_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=model.WORKOUTS[key]['id']).first()
            if workout_log or goal:
                resp[model.WORKOUTS[key]['name']] = {}
                resp[model.WORKOUTS[key]['name']]['Achieved'] = False
                resp[model.WORKOUTS[key]['name']]['Value'] = workout_log.amount if workout_log else 0
                if goal:
                    if resp[model.WORKOUTS[key]['name']]['Value'] >= goal:
                        resp[model.WORKOUTS[key]['name']]['Achieved'] = True
                    resp[model.WORKOUTS[key]['name']]['Goal'] = goal

        setting = user_settings and user_settings.distance_goal
        if distance_log or setting:
            resp['Distance'] = {}
            resp['Distance']['Achieved'] = False
            resp['Distance']['Value'] = Workout.dst_print(float(distance_log.amount)) if distance_log else 0
            if setting:
                if distance_log and distance_log.amount and float(distance_log.amount) >= user_settings.distance_goal:
                    resp['Distance']['Achieved'] = True
                resp['Distance']['Goal'] = Workout.dst_print(float(user_settings.distance_goal))

        await ctx.channel.send(embed=daily_embed(ctx.author, resp))
    
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
    
    @commands.command()
    async def leaderboard(self, ctx: commands.Context, category=None):
        category = category.lower() if category else None
        if category == "water":
            await self.waterboard(ctx)
            return
        elif category == "run" or category == "walk":
            category = "distance"
        
        if category not in model.WORKOUTS:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} [{'/'.join(list(model.WORKOUTS.keys()))}]")
            return
       
        session = model.Session()
        date = datetime.date.today()
        results = []

        query = session.query(model.Workout).filter_by(date=date, workout_id=model.WORKOUTS[category]['id'])
        for entry in query:
            results.append({
                'User': self.bot.get_user(entry.user_id).name,
                'Value': float(entry.amount) if category == "water" else entry.amount
            })
        
        results = sorted(results, key=lambda res: res['Value'])[::-1]
        msg = f"{model.WORKOUTS[category]['name']} leaderboard as of {datetime.datetime.now()}:\n"
        for place, res in zip(range(1, len(results) + 1), results):
            msg += f"\t{place}: {res['User']} with {Workout.dst_print(res['Value']) if category == 'distance' else res['Value']}\n"
        
        await ctx.channel.send(msg)
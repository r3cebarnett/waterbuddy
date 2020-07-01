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

def get_dict_for_water(bot, date):
    session = model.Session()

    res = []
    water = session.query(model.Water).filter_by(date=date).filter(model.Water.amount > 0).order_by(model.Water.amount.desc())

    for entry, place in zip(water, range(1, water.count() + 1)):
        res.append({
            'Place': place,
            'Name': bot.get_user(entry.user_id).name,
            'Amount': Water.vol_print(float(entry.amount))
        })
    
    return res

def get_dict_for_workout(bot, date, workout_str):
    session = model.Session()

    res = []
    workout = session.query(model.Workout).filter_by(date=date, workout_id=model.WORKOUTS[workout_str]['id']).filter(model.Workout.amount > 0)\
                     .order_by(model.Workout.amount.desc())

    for entry, place in zip(workout, range(1, workout.count() + 1)):
        res.append({
            'Place': place,
            'Name': bot.get_user(entry.user_id).name,
            'Amount': entry.amount
        })

    return res

def make_embed_for_workout(bot, date, workout_str):
    ppl = get_dict_for_workout(bot, date, workout_str)
    if not len(ppl):
        msg = "No entries for this category today!"
    else:
        msg = ""
        for entry in ppl:
            msg += f"**{entry['Place']}.** *{entry['Name']}* with {entry['Amount']}\n"

    return discord.Embed(title=f"{model.WORKOUTS[workout_str]['name']} Leaderbord for {date}", description=msg)

def make_embed_for_distance(bot, date):
    ppl = get_dict_for_distance(bot, date)
    if not len(ppl):
        msg = "No entries for this category today!"
    else:
        msg = ""
        for entry in ppl:
            msg += f"**{entry['Place']}.** *{entry['Name']}* with {entry['Amount']}\n"

    return discord.Embed(title=f"Distance Leaderbord for {date}", description=msg)

def make_embed_for_water(bot, date):
    ppl = get_dict_for_water(bot, date)
    if not len(ppl):
        msg = "No entries for this category today!"
    else:
        msg = ""
        for entry in ppl:
            msg += f"**{entry['Place']}.** *{entry['Name']}* with {entry['Amount']}\n"

    return discord.Embed(title=f"Water Leaderbord for {date}", description=msg)

def get_dict_for_distance(bot, date):
    session = model.Session()

    res = []
    distance = session.query(model.Workout).filter_by(date=date, workout_id=model.WORKOUTS['distance']['id']).filter(model.Workout.amount > 0).order_by(model.Workout.amount.desc())

    for entry, place in zip(distance, range(1, distance.count() + 1)):
        res.append({
            'Place': place,
            'Name': bot.get_user(entry.user_id).name,
            'Amount': Workout.dst_print(float(entry.amount))
        })
    
    return res

def make_overall_leaderboard_embed(res, date):
    embed = discord.Embed(title=f"Overall Leaderboard for {date}")
    num_embeds = 0

    for key in res:
        msg = ""
        if not len(res[key]):
            msg += "No entries for category today!"
        else:
            for entry in res[key]:
                msg += f"**{entry['Place']}.** *{entry['Name']}* with {entry['Amount']}\n"
        embed.add_field(name=key, value=msg, inline=True)
        log.debug(f"Adding {key}")
        num_embeds += 1

        if num_embeds % 2 == 0:
            log.debug(f"Adding spacer")
            embed.add_field(name='\u200b', value='\u200b', inline=False)

    return embed

def make_overall_leaderboard_dict(bot: commands.Bot, date):
    session = model.Session()

    water = session.query(model.Water).filter_by(date=date).order_by(model.Water.amount.desc())
    distance = session.query(model.Workout).filter_by(date=date, workout_id=model.WORKOUTS['distance']['id']).order_by(model.Workout.amount.desc())

    res = {}

    res['Water'] = get_dict_for_water(bot, date)[:5]
    res['Distance'] = get_dict_for_distance(bot, date)[:5]
    
    for key in model.WORKOUTS:
        if key == 'distance':
            continue

        res[model.WORKOUTS[key]['name']] = get_dict_for_workout(bot, date, key)[:5]
    
    return res


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
        await ctx.channel.send(embed=make_embed_for_water(self.bot, datetime.date.today()))
    
    @commands.command()
    async def leaderboard(self, ctx: commands.Context, category=None, date=datetime.date.today()):
        category = category.lower() if category else None

        if category == "water":
            await self.waterboard(ctx)
            return
        elif category == "run" or category == "walk":
            category = "distance"
        
        if not category:
            resp = make_overall_leaderboard_dict(self.bot, date)
            embed = make_overall_leaderboard_embed(resp, date)
            await ctx.channel.send(embed=embed)
            return
        
        if category not in model.WORKOUTS:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} [{'/'.join(list(model.WORKOUTS.keys()))}]")
            return
        
        if category == "distance":
            await ctx.channel.send(embed=make_embed_for_distance(self.bot, date))
            return
        else:
            await ctx.channel.send(embed=make_embed_for_workout(self.bot, date, category))
            return
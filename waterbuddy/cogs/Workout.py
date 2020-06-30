import datetime
import discord
import logging
import traceback

from db import model
from discord.ext import commands
from shared import auxfn

log = logging.getLogger('waterbuddy')

KM_IN_MI = 1.60934
M_IN_KM = 1000

SUPPORTED_DST_UNITS = ['km', 'mi', 'm']

def x_to_km(val: float, unit: str):
    unit_comp = unit.lower()

    if unit_comp in ['km']:
        return val
    elif unit_comp in ['m']:
        return val / M_IN_KM
    elif unit_comp in ['mi']:
        return val * KM_IN_MI
    else:
        raise Exception(f"Type not found: {unit_comp}")

def km_to_mi(val):
    return val * 1.0 / KM_IN_MI

def dst_print(val):
    return f"{val:.1f} km ({km_to_mi(val):.1f} mi)"

def get_goal_from_id(user_settings, id):
    if id == 'pullup':
        return user_settings.pullup_goal
    elif id == 'pushup':
        return user_settings.pushup_goal
    elif id == 'situp':
        return user_settings.situp_goal
    elif id == 'squat':
        return user_settings.squat_goal
    elif id == 'jumpingjack':
        return user_settings.jumpingjack_goal
    elif id == 'distance':
        return float(user_settings.distance_goal)
    else:
        return None

class Workout(commands.Cog):
    def __init__(self, bot: commands.Bot, settings):
        self.bot = bot
        self.settings = settings
        self.name = 'Workout'
    
    async def cog_before_invoke(self, ctx: commands.Context):
        log.debug(f'[WRKT] {ctx.command} command issued')

    async def log_workout(self, ctx, typestr, amount):
        typeid = model.WORKOUTS[typestr]['id']

        try:
            val = int(amount)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} <int amount>")
            return
        
        type_out = (typestr + "s") if val > 0 else typestr
        
        session = model.Session()
        date = datetime.date.today()
        workout_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=typeid).first()
        
        if not workout_log:
            workout_log = model.workout_factory(ctx.author.id, date, typeid, val)
        else:
            workout_log.amount = workout_log.amount + val
        
        try:
            session.add(workout_log)
            session.commit()
        except:
            log.debug(f"[WRKT] Failed to commit change, rolling back...")
            log.debug(f"[WRKT] {traceback.format_exc()}")
            await ctx.channel.send(f"Failed to log {type_out}")
            session.rollback()
            return
        
        msg = f"Logged {val} {type_out} for {ctx.author.mention}. Today's total is now {workout_log.amount}."
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if user:
            goal = get_goal_from_id(user, typestr)
            if goal and goal <= workout_log.amount:
                msg = f"{msg}\nCongrats, you met your goal of {goal}!"
        
        await ctx.channel.send(msg)


    @commands.command()
    async def situp(self, ctx: commands.Context, amount=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        await self.log_workout(ctx, "situp", amount)

    
    @commands.command()
    async def pushup(self, ctx: commands.Context, amount=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return

        await self.log_workout(ctx, "pushup", amount)
    
    @commands.command()
    async def pullup(self, ctx: commands.Context, amount=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return

        await self.log_workout(ctx, "pullup", amount)
    
    @commands.command()
    async def squat(self, ctx: commands.Context, amount=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        await self.log_workout(ctx, "squat", amount)
    
    @commands.command(
        aliases=["jj","jumpingjacks"]
    )
    async def jumpingjack(self, ctx: commands.Context, amount=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        await self.log_workout(ctx, "jumpingjack", amount)
    
    @commands.command(
        aliases=["run","walk"]
    )
    async def distance(self, ctx: commands.Context, amount=None, unit=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        session = model.Session()
        val = 0

        try:
            val = x_to_km(float(amount), unit)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} <number> <{'/'.join(SUPPORTED_DST_UNITS)}>")
        
        date = datetime.date.today()
        dst_log = session.query(model.Workout).filter_by(user_id=ctx.author.id, date=date, workout_id=model.WORKOUTS['distance']['id']).first()
        if not dst_log:
            dst_log = model.workout_factory(ctx.author.id, date, model.WORKOUTS['distance']['id'], val)
        else:
            dst_log.amount = val + float(dst_log.amount)
        
        try:
            session.add(dst_log)
            session.commit()
        except:
            log.debug(f'[WRKT] Failed to commit change, rolling back...')
            log.debug(f'[WRKT] {traceback.format_exc()}')
            await ctx.channel.send(f"Failed to log distance.")
            session.rollback()
            return
        
        msg = f"Logged {dst_print(val)} for {ctx.author.mention}. Today's total is now {dst_print(float(dst_log.amount))}."
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if user and user.distance_goal and float(user.distance_goal) <= float(dst_log.amount):
            msg = f"{msg}\nCongrats, you met your goal of {dst_print(float(user.distance_goal))}!"
        
        await ctx.channel.send(msg)

    @commands.command()
    async def situpgoal(self, ctx: commands.Context, amount=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        try:
            val = int(amount)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} <number>")
            return
        
        session = model.Session()
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if not user:
            user = model.settings_factory(ctx.author.id, situp_goal=val)
        else:
            user.situp_goal = val
        
        try:
            session.add(user)
            session.commit()
        except:
            log.debug(f'[WRKT] Failed to commit change, rolling back...')
            log.debug(f'[WRKT] {traceback.format_exc()}')
            await ctx.channel.send(f"Failed to update situp goal.")
            session.rollback()
            return
        
        await ctx.channel.send(f"Updated situp goal for {ctx.author.mention} to {val}.")
    
    @commands.command()
    async def pushupgoal(self, ctx: commands.Context, amount=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        try:
            val = int(amount)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} <number>")
            return
        
        session = model.Session()
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if not user:
            user = model.settings_factory(ctx.author.id, pushup_goal=val)
        else:
            user.pushup_goal = val
        
        try:
            session.add(user)
            session.commit()
        except:
            log.debug(f'[WRKT] Failed to commit change, rolling back...')
            log.debug(f'[WRKT] {traceback.format_exc()}')
            await ctx.channel.send(f"Failed to update pushup goal.")
            session.rollback()
            return
        
        await ctx.channel.send(f"Updated pushup goal for {ctx.author.mention} to {val}.")
    
    @commands.command()
    async def pullupgoal(self, ctx: commands.Context, amount=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        try:
            val = int(amount)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} <number>")
            return
        
        session = model.Session()
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if not user:
            user = model.settings_factory(ctx.author.id, pullup_goal=val)
        else:
            user.pullup_goal = val
        
        try:
            session.add(user)
            session.commit()
        except:
            log.debug(f'[WRKT] Failed to commit change, rolling back...')
            log.debug(f'[WRKT] {traceback.format_exc()}')
            await ctx.channel.send(f"Failed to update pullup goal.")
            session.rollback()
            return
        
        await ctx.channel.send(f"Updated pullup goal for {ctx.author.mention} to {val}.")
    
    @commands.command()
    async def squatgoal(self, ctx: commands.Context, amount=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        try:
            val = int(amount)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.commands} <number>")
            return
        
        session = model.Session()
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if not user:
            user = model.settings_factor(ctx.author_id, squat_goal=val)
        else:
            user.squat_goal = val
        
        try:
            session.add(user)
            session.commit()
        except:
            log.debug(f'[WRKT] Failed to commit change, rolling back...')
            log.debug(f'[WRKT] {traceback.format_exc()}')
            await ctx.channel.send(f"Failed to update squat goal.")
            session.rollback()
            return
        
        await ctx.channel.send(f"Updated squat goal for {ctx.author.mention} to {val}.")
    
    @commands.command(
        aliases=["jjgoal"]
    )
    async def jumpingjackgoal(self, ctx: commands.Context, amount=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        try:
            val = int(amount)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.commands} <number>")
            return
        
        session = model.Session()
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if not user:
            user = model.settings_factor(ctx.author_id, jumpingjack_goal=val)
        else:
            user.jumpingjack_goal = val
        
        try:
            session.add(user)
            session.commit()
        except:
            log.debug(f'[WRKT] Failed to commit change, rolling back...')
            log.debug(f'[WRKT] {traceback.format_exc()}')
            await ctx.channel.send(f"Failed to update jumping jack goal.")
            session.rollback()
            return
        
        await ctx.channel.send(f"Updated jumping jack goal for {ctx.author.mention} to {val}.")
    
    @commands.command(
        aliases=["rungoal","walkgoal"]
    )
    async def distancegoal(self, ctx, amount=None, unit=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        try:
            val = x_to_km(float(amount), unit)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} <number> <{'/'.join(SUPPORTED_DST_UNITS)}>")
            return
        
        session = model.Session()
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if not user:
            user = model.settings_factory(ctx.author.id, distance_goal=val)
        else:
            user.distance_goal = val
        
        try:
            session.add(user)
            session.commit()
        except:
            log.debug(f'[WRKT] Failed to commit change, rolling back...')
            log.debug(f'[WRKT] {traceback.format_exc()}')
            await ctx.channel.send(f"Failed to update distance goal.")
            session.rollback()
            return
        
        await ctx.channel.send(f"Updated distance goal for {ctx.author.mention} to {dst_print(val)}.")
import datetime
import discord
import logging
import traceback

from db import model
from discord.ext import commands
from shared import auxfn

log = logging.getLogger('waterbuddy')

def get_goal_from_id(user_settings, id):
    if id == 'pullup':
        return user_settings.pullup_goal
    elif id == 'pushup':
        return user_settings.pushup_goal
    elif id == 'situp':
        return user_settings.situp_goal
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
        typeid = model.WORKOUTS[typestr]

        try:
            val = int(amount)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('io_channel')}{ctx.command} <int amount>")
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
                msg = f"{msg} Congrats, you met your goal of {goal}!"
        
        await ctx.channel.send(msg)


    @commands.command()
    async def situp(self, ctx: commands.Context, amount: int = None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        await self.log_workout(ctx, "situp", amount)

    
    @commands.command()
    async def pushup(self, ctx: commands.Context, amount: int = None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return

        await self.log_workout(ctx, "pushup", amount)
    
    @commands.command()
    async def pullup(self, ctx: commands.Context, amount: int = None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return

        await self.log_workout(ctx, "pullup", amount)

    @commands.command()
    async def situpgoal(self, ctx: commands.Context, amount: int = None):
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
    async def pushupgoal(self, ctx: commands.Context, amount: int = None):
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
    async def pullupgoal(self, ctx: commands.Context, amount: int = None):
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
import datetime
import discord
import logging
import traceback

from db import model
from discord.ext import commands
from shared import auxfn

log = logging.getLogger('waterbuddy')

ML_IN_L = 1000
ML_IN_OZ = 29.5735
ML_IN_C = ML_IN_OZ * 8
ML_IN_P = ML_IN_C * 2
ML_IN_Q = ML_IN_P * 2
ML_IN_G = ML_IN_Q * 4

SUPPORTED_UNITS = ['l', 'ml', 'oz', 'c', 'p', 'q', 'g']

def x_to_l(val: float, unit: str):
    unit_comp = unit.lower()

    if unit_comp in ['l']:
        return val
    elif unit_comp in ['ml']: #, 'milliliter', 'milliliters']:
        return val / ML_IN_L
    elif unit_comp in ['oz']:
        return val * ML_IN_OZ / ML_IN_L
    elif unit_comp in ['c']:
        return val * ML_IN_C / ML_IN_L
    elif unit_comp in ['p']:
        return val * ML_IN_P / ML_IN_L
    elif unit_comp in ['q']:
        return val * ML_IN_Q / ML_IN_L
    elif unit_comp in ['g']:
        return val * ML_IN_G / ML_IN_L
    else:
        raise Exception(f"Type not found: {unit_comp}")

def l_to_oz(val):
    return val * 1.0 * ML_IN_L / ML_IN_OZ

def vol_print(val):
    return f"{val:.3f} L ({l_to_oz(val):.1f} oz)"

class Water(commands.Cog):
    def __init__(self, bot, settings):
        self.bot = bot
        self.settings = settings
        self.name = 'Water'
    
    async def cog_before_invoke(self, ctx: commands.Context):
        log.debug(f'[WATR] {ctx.command} command issued')

    @commands.command(
        description="Update default water increment size when `drink` is called."
    )
    async def watersize(self, ctx, amount=None, unit=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return

        try:
            val = x_to_l(float(amount), unit)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} <number> <{'/'.join(SUPPORTED_UNITS)}>")
            return
        
        session = model.Session()
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if not user:
            user = model.settings_factory(ctx.author.id, default_water_size=val)
        else:
            user.default_water_measure = val
        
        try:
            session.add(user)
            session.commit()
        except:
            log.debug(f'[WATR] Failed to commit change, rolling back...')
            log.debug(f'[WATR] {traceback.format_exc()}')
            await ctx.channel.send(f"Failed to update default water size.")
            session.rollback()
            return
        
        await ctx.channel.send(f"Updated default water size for {ctx.author.mention} to {vol_print(val)}.")
    
    @commands.command(
        description="Get default water increment size for your account."
    )
    async def getwatersize(self, ctx):
        if ctx.channel.name != self.settings.get('io_channel'):
            return

        session = model.Session()
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if not user:
            await ctx.channel.send(f"No settings information saved for {ctx.author.mention}")
            return
        if not user.default_water_measure:
            await ctx.channel.send(f"No default water increment size saved for {ctx.author.mention}")
            return
        
        val = float(user.default_water_measure)
        await ctx.channel.send(f"Default water increment size for {ctx.author.mention} is {vol_print(val)}.")
    
    @commands.command()
    async def drink(self, ctx, amount=None, unit=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return

        session = model.Session()
        val = 0

        # Get value to add by
        if not amount and not unit:
            user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
            if not user or not user.default_water_measure:
                await ctx.channel.send(f"No default water increment size saved for {ctx.author.mention}.")
                return
            else:
                val = float(user.default_water_measure)
        else:
            try:
                val = x_to_l(float(amount), unit)
            except:
                await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} <number> <{'/'.join(SUPPORTED_UNITS)}>")
                return
        
        # Get today's entry
        date = datetime.date.today()
        water_log = session.query(model.Water).filter_by(user_id=ctx.author.id, date=date).first()
        if not water_log:
            water_log = model.water_factory(ctx.author.id, date, val)
        else:
            water_log.amount = val + float(water_log.amount)
        
        try:
            session.add(water_log)
            session.commit()
        except:
            log.debug(f'[WATR] Failed to commit change, rolling back...')
            log.debug(f'[WATR] {traceback.format_exc()}')
            await ctx.channel.send(f"Failed to add water log.")
            session.rollback()
            return

        msg = f"Logged {vol_print(val)} of water for {ctx.author.mention}. Today's total is now {vol_print(float(water_log.amount))}."
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if user and user.water_goal and float(user.water_goal) <= float(water_log.amount):
            msg = f"{msg} Congrats, you met your goal of {vol_print(float(user.water_goal))}!"
        
        await ctx.channel.send(msg)
    
    @commands.command()
    async def drank(self, ctx, user=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return

        session = model.Session()

        if user:
            try:
                target = self.bot.get_user(int(user[3:-1]))
            except:
                target = ctx.author
        else:
            target = ctx.author

        water_log = session.query(model.Water).filter_by(user_id=target.id, date=datetime.date.today()).first()
        if not water_log:
            msg = f"{target.mention}"
            if target == ctx.author:
                await ctx.channel.send(f"{target.mention}, you have not logged any water today. Get drinking!")
            else:
                await ctx.channel.send(f"{target.mention} has not logged water today.")
            return
        
        val = float(water_log.amount)
        if target == ctx.author:
            await ctx.channel.send(f"{target.mention}, you have logged {vol_print(val)} of water today.")
        else:
            await ctx.channel.send(f"{target.mention} has logged {vol_print(val)} of water today.")
    
    @commands.command()
    async def drunk(self, ctx):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        await ctx.channel.send(auxfn.get_emoji_by_name(ctx.guild, "pushypenguin"))
    
    @commands.command()
    async def watergoal(self, ctx, amount=None, unit=None):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        
        try:
            val = x_to_l(float(amount), unit)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} <number> <{'/'.join(SUPPORTED_UNITS)}>")
            return
        
        session = model.Session()
        user = session.query(model.Settings).filter_by(user_id=ctx.author.id).first()
        if not user:
            user = model.settings_factory(ctx.author.id, water_goal=val)
        else:
            user.water_goal = val
        
        try:
            session.add(user)
            session.commit()
        except:
            log.debug(f'[WATR] Failed to commit change, rolling back...')
            log.debug(f'[WATR] {traceback.format_exc()}')
            await ctx.channel.send(f"Failed to update water goal.")
            session.rollback()
            return
        
        await ctx.channel.send(f"Updated water goal for {ctx.author.mention} to {vol_print(val)}.")
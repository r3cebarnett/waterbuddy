import datetime
import discord
import logging
import traceback

from cogs import Stats
from db import model
from discord.ext import commands, tasks
from pytimeparse.timeparse import timeparse
from shared import auxfn

log = logging.getLogger('waterbuddy')

def bind(num, peak):
    if num > peak:
        return 0
    else:
        return num

def get_channel_from_name(bot, channel_name):
    for channel in bot.get_all_channels():
        if channel.name == channel_name:
            return channel

class Timer(commands.Cog):
    def __init__(self, bot: commands.Bot, settings):
        self.bot = bot
        self.settings = settings
        self.name = 'Timer'
        self.timer_handler.start()
        self.hourly_handler.start()
        
    async def cog_before_invoke(self, ctx: commands.Context):
        log.debug(f'[TIMR] {ctx.command} command issued')

    @tasks.loop(seconds=1)
    async def timer_handler(self):
        time = datetime.datetime.now()
        session = model.Session()
        
        query = session.query(model.Timer).filter(model.Timer.time < time)
        for timer in query:
            msg = f"Reminder for {self.bot.get_user(timer.user_id).mention}!"
            if timer.message:
                msg = f"{msg} {timer.message}"
            
            channel = get_channel_from_name(self.bot, self.settings.get('io_channel'))
            log.debug(f'[TIMR] Responding to ID: {timer}')
            
            try:
                await channel.send(msg)
                session.delete(timer)
            except:
                log.debug(f"[TIMR] Failed to send timer message. Going to try again later.")
                session.rollback()
        
        session.commit()
    
    @tasks.loop(hours=1)
    async def hourly_handler(self):
        time = datetime.datetime.now()
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        channel = get_channel_from_name(self.bot, self.settings.get('io_channel'))
        if time.hour == 0:
            res = Stats.make_overall_leaderboard_dict(self.bot, yesterday)
            embed = Stats.make_overall_leaderboard_embed(res, yesterday)
            await channel.send(f"Official overall leaderboard for {yesterday}", embed=embed)
    
    @timer_handler.before_loop
    async def before_timer_handler(self):
        await self.bot.wait_until_ready()
    
    @hourly_handler.before_loop
    async def before_hourly_handler(self):
        await self.bot.wait_until_ready()

    @commands.command(
        aliases=['timer']
    )
    async def remind(self, ctx: commands.Context, amount=None, *msg):
        if not amount:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} [time without spaces (e.g. 1d, 3h30m, 45s, etc.)] [msg (optional)]")
            return
        else:
            amount = timeparse(amount)
        if len(msg) > 0:
            msg = ' '.join(msg)
        else:
            msg = None
        
        try:
            remind_time = datetime.datetime.now() + datetime.timedelta(seconds=amount)
        except:
            await ctx.channel.send(f"Usage: {self.settings.get('prefix')}{ctx.command} [time without spaces (e.g. 1d, 3h30m, 45s, etc.)] [msg (optional)]")
            return
        
        session = model.Session()
        reminder = model.timer_factory(ctx.author.id, message=msg, time=remind_time)
        
        try:
            session.add(reminder)
            session.commit()
        except:
            log.debug(f"[TIMR] Failed to commit change, rolling back...")
            log.debug(f"[TIMR] {traceback.format_exc()}")
            await ctx.channel.send(f"Failed to add timer.")
            session.rollback()
            return
        
        await ctx.channel.send(f"{ctx.author.mention}, successfully added timer for {remind_time}.")
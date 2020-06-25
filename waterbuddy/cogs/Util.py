import discord
import logging

from discord.ext import commands
from shared import auxfn

log = logging.getLogger('waterbuddy')

class Util(commands.Cog):
    def __init__(self, bot: commands.Bot, settings):
        self.bot = bot
        self.settings = settings
        self.name = 'Util'
    
    async def cog_before_invoke(self, ctx: commands.Context):
        log.debug(f'[UTIL] {ctx.command} command issued')

    @commands.command()
    async def ping(self, ctx: commands.Context):
        if ctx.channel.name != self.settings.get('io_channel'):
            return

        await ctx.channel.send(f'Pong! ({self.bot.latency * 1000:.0f} ms)')
    
    @commands.command()
    async def quit(self, ctx: commands.Context):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        if not auxfn.member_has_role(ctx.message.author, self.settings.get('admin_role')):
            return

        self.settings.set1('close_on_purpose', True)
        await self.bot.close()
    
    @commands.command()
    async def restart(self, ctx: commands.Context):
        if ctx.channel.name != self.settings.get('io_channel'):
            return
        if not auxfn.member_has_role(ctx.message.author, self.settings.get('admin_role')):
            return

        await self.bot.close()

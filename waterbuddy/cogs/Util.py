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
    
    @commands.command()
    async def ping(self, ctx: commands.Context):
        if ctx.message.channel.name != self.settings.get('io_channel'):
            return

        log.debug('[UTIL] ping command issued')
        await ctx.message.channel.send(f'Pong! ({self.bot.latency * 1000:.0f} ms)')
    
    @commands.command()
    async def quit(self, ctx: commands.Context):
        if ctx.message.channel.name != self.settings.get('io_channel'):
            return
        if not auxfn.member_has_role(ctx.message.author, self.settings.get('admin_role')):
            return
        
        log.debug('[UTIL] quit command issued')
        self.settings.set1('close_on_purpose', True)
        await self.bot.close()
    
    @commands.command()
    async def restart(self, ctx: commands.Context):
        if ctx.message.channel.name != self.settings.get('io_channel'):
            return
        if not auxfn.member_has_role(ctx.message.author, self.settings.get('admin_role')):
            return
        
        log.debug('[UTIL] restart command issued')
        await self.bot.close()

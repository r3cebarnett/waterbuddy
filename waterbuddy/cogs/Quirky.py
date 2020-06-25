import datetime
import discord
import logging
import random

from discord.ext import commands

log = logging.getLogger('waterbuddy')

class Quirky(commands.Cog):
    def __init__(self, bot: commands.Bot, settings):
        self.bot = bot
        self.settings = settings
        self.name = 'Quirky'
    
    async def cog_before_invoke(self, ctx: commands.Context):
        log.debug(f'[QWRK] {ctx.command} command issued')

    @commands.command(
        name='8ball',
        description='Call to get the result of a Magic 8 Ball!'
    )
    async def eightball(self, ctx: commands.Context):
        #if ctx.channel.name != settings.get('channel_io'):
        #    return
        random.seed(datetime.datetime.now())
        responses = [
            "it is certain.",
            "it is decidedly so.",
            "without a doubt.",
            "yes - definitely.",
            "you may rely on it.",
            "as I see it, yes.",
            "most likely.",
            "outlook good.",
            "yes.",
            "signs point to yes.",
            "reply hazy, try again.",
            "ask again later.",
            "better not tell you now.",
            "cannot predict now.",
            "concentrate and ask again.",
            "don't count on it.",
            "my reply is no.",
            "my sources say no.",
            "outlook not so good.",
            "very doubtful."
        ]

        resp = responses[random.randint(0, len(responses) - 1)]
        await ctx.channel.send(f"{ctx.author.mention}, {resp}")
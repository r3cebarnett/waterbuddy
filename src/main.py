import constants
import discord
import token

from datetime import datetime

client = discord.Client()

@client.event
async def on_ready():
    print(f"We have logged in as {client.user}")

@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    
    if message.content.startswith('!help'):
        await message.channel.send('Not implemented yet! :D')
    
    if message.content.startswith('!ping'):
        await message.channel.send(f'pong! ({(datetime.now() - message.created_at).total_seconds() * constants.S_TO_MS} ms)')


client.run(token.CLIENT_TOKEN)

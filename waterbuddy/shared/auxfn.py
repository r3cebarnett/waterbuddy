import discord

def member_has_role(member: discord.Member, role: str) -> bool :
    return role in [x.name for x in member.roles]

def get_emoji_by_name(server: discord.Guild, emoji_str: str) -> discord.Emoji:
    emoji_list = server.emojis
    for emoji in emoji_list:
        if emoji.name == emoji_str:
            return emoji
    return None
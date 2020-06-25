import discord

def member_has_role(member: discord.Member, role: str) -> bool :
    return role in [x.name for x in member.roles]
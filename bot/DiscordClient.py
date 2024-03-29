import dbm
import discord
import commands.role_menu as rm

class DiscordClient(discord.Client):
  def __init__(self, role_menu_channel_id):
    intents = discord.Intents(messages=True, guilds=True, members=True, reactions=True, message_content=True)
    super().__init__(intents= intents)
    self.rm_channel_id = role_menu_channel_id
    self.members = dict()

  def get_member(self, user_id, guild_id):
    if guild_id in self.members and user_id in self.members[guild_id]:
      return self.members[guild_id][user_id]
    else:
      return None
    
  async def on_raw_reaction_add(self, payload):
    await rm.on_raw_reaction_add(self, payload, self.rm_channel_id)

  async def on_raw_reaction_remove(self, payload):
    await rm.on_raw_reaction_remove(self, payload, self.rm_channel_id)

  async def update_members(self, guild):
    guild_members = dict()
    async for member in guild.fetch_members(limit=None):
      guild_members[member.id] = member
    self.members[guild.id] = guild_members
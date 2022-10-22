import dbm
import discord
from db.manager import dbManager
import commands.role_menu as rm

class DicordClient(discord.Client):
  def __init__(self, role_menu_channel_id, redis_url):
    intents = discord.Intents(messages=True, guilds=True, members=True)
    super().__init__(intents= intents)
    self.db = dbManager(redis_url)
    self.rm_channel_id = role_menu_channel_id


  async def on_raw_reaction_add(self, payload):
    await rm.on_raw_reaction_add(self, payload, self.rm_channel_id)

  async def on_raw_reaction_remove(self, payload):
    await rm.on_raw_reaction_remove(self, payload, self.rm_channel_id)
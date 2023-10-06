from discord import ChannelType
import json
from DiscordClient import DiscordClient

class DiscordDB:
  def __init__(self, category_id, client: DiscordClient):
    self.client = client
    self.db = dict()
    self.category_id = category_id
    

  async def sync(self):
    self.category = await self.client.fetch_channel(self.category_id)
    if self.category.type != ChannelType.category:
      self.category = None
    else:
      for textChannel in self.category.text_channels:
        data = []
        async for message in textChannel.history(limit=100):
          data = data + message.content.split('\n')
        self.db[textChannel.name] = data

  async def get(self, key):
    if key in self.db:
      return self.db[key]
    else:
      return None
  
  async def set(self, key, data: str):
    if key in self.db:
      await self.clear(key)
    
    text_channel = await self.category.create_text_channel(key)
    
    if len(data) >= 2000:
      raise Exception('data too large')
    
    await text_channel.send(data)
    self.db[key] = [data]

  async def clear(self, key):
    if key not in self.db:
      return
    text_channel = [x for x in self.category.text_channels if x.name == key][0]
    await text_channel.delete()
    del(self.db[key])

  async def remove(self, key, dataPoint):
    if key not in self.db or dataPoint not in self.db[key]:
      return
    data = self.db[key]
    if data is not None and dataPoint in data:
        text_channel = [x for x in self.category.text_channels if x.name == key][0]
        async for message in text_channel.history(limit=100):
          fragment_data = message.content.split("\n")
          if dataPoint in fragment_data:
            start = message.content.find(dataPoint)
            #start + len(dataPoint) + 1 includes \n at the end of the entry
            last = start + len(dataPoint) == len(message.content)
            newContent = message.content[:start] + ("" if last else message.content[start + len(dataPoint) + 1:])
            self.db[key] = [x for x in self.db[key] if x != dataPoint]
            if newContent == "":
              await message.delete()
            else:
              await message.edit(content=newContent)
            if self.db[key] == []:
              del(self.db[key])
              await text_channel.delete()
            break
        
  async def append(self, key, dataPoint):
    data = self.db.get(key)
    if data is None or data == []:
      await self.set(key, dataPoint)
    else:
      if dataPoint in data:
        return
      text_channel = [x for x in self.category.text_channels if x.name == key][0]
      async for message in text_channel.history(limit=1):
        if len(message.content) + len(dataPoint) + 1 >= 2000:
          await text_channel.send(dataPoint + '\n')
        else:
          await message.edit(content=message.content + '\n' + dataPoint)
      self.db[key] += [dataPoint]


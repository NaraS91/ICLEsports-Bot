import redis
import json

class dbManager:
  def __init__(self, url):
    self.url = url
    self.db = redis.from_url(self.url)

  async def get(self, key):
    data = self.db.get(key)
    return json.loads(data) if data is not None else None
  
  async def set(self, key, data):
    self.db.set(key, json.dumps(data))

  async def clear(self, key):
    self.db.set(key, json.dumps(list()))

  async def remove(self, key, dataPoint):
    data = self.db.get(key)
    if data is not None:
      data = json.loads(data)

      if dataPoint in data:
        data.remove(dataPoint)
        self.db.set(key, json.dumps(data))
    

  async def append(self, key, dataPoint):
    data = self.db.get(key)
    if data is None:
      data = list()
    else:
      data = json.loads(data)
    
    if dataPoint not in data:
      data.append(dataPoint)
      self.db.set(key, json.dumps(data))


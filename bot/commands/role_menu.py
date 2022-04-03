from json import load
import os
import discord

async def on_raw_reaction_add(client, payload, role_menu_channel_id):
  channel_id = payload.channel_id
  message_id = payload.message_id
  if channel_id != role_menu_channel_id:
    return
  role_menus = role_menu_channels[channel_id]
  if message_id in role_menus:
    role_menu = role_menus[message_id]
    guild = await client.fetch_guild(payload.guild_id)
    user = await guild.fetch_member(payload.user_id)
    roles = []
    if payload.emoji.id == None:
      roles = role_menu[payload.emoji.name]
    else:
      emoji = await guild.fetch_emoji(payload.emoji.id)
      roles = role_menu[f'<:{emoji.name}:{emoji.id}>']
    for role_mention in roles:
      role_id = int(role_mention[3:-1])
      role = discord.utils.get(guild.roles, id=role_id)
      if role == None or user == None:
        return
      await user.add_roles(role)

async def on_raw_reaction_remove(client, payload, role_menu_channel_id):
  channel_id = payload.channel_id
  message_id = payload.message_id
  if channel_id != role_menu_channel_id:
      return
  role_menus = role_menu_channels[channel_id]
  if message_id in role_menus:
      role_menu = role_menus[message_id]
      guild = await client.fetch_guild(payload.guild_id)
      user = await guild.fetch_member(payload.user_id)
      roles = []
      if payload.emoji.id == None:
          roles = role_menu[payload.emoji.name]
      else:
          emoji = await guild.fetch_emoji(payload.emoji.id)
          roles = role_menu[f'<:{emoji.name}:{emoji.id}>']
      for role_mention in roles:
          role_id = int(role_mention[3:-1])
          role = discord.utils.get(guild.roles, id=role_id)
          if role == None or user == None:
              return
          await user.remove_roles(role)

async def create_role_menu(args, message, role_menu_channel_id):
  lines = message.content.splitlines()[1:]
  
  if message.channel.id != role_menu_channel_id:
      await message.channel.send("this is not the role menu channel")
      return

  role_menus = role_menu_channels[message.channel.id]
  description = ""
  rolesIndex = 0

  if lines[0].startswith("\"\"\""):
      for i in range(len(lines) - 1):
          if lines[i+1].startswith("\"\"\""):
              rolesIndex = i + 2
              break
          description += lines[i+1] + "\n"
  
  if rolesIndex >= len(lines):
      await message.channel.send("wrong format. Either description quotes \"\"\" are missing or no roles where ")
      return

  role_menu = {}
  roles_response = ""
  for line in lines[rolesIndex:]:
      words = line.split()
      if len(words) == 0:
          continue

      if len(words) < 2:
          await message.channel.send("roles were not specified.")
          return

      role_menu[words[0]] = words [1:]
      roles_response += words[0] + ": " + ' '.join(words[1:]) + '\n'

  response = "ROLE MENU" + '\n' + description + roles_response
  message = await message.channel.send(response)

  role_menus[message.id] = role_menu

  for emote in role_menu:
      await message.add_reaction(emote)

async def load_role_menus(client, role_menu_channel_id):
  channel = await client.fetch_channel(role_menu_channel_id)
  async for message in channel.history():
      if message.author == client.user:
          if message.content.startswith("ROLE MENU"):
              load_role_menu(message)
        
def load_role_menu(message):
  id = message.id
  lines = message.content.splitlines()
  role_menu = {}

  for line in lines:
      words = line.split()
      if len(words) < 2:
          continue
      if words[0][-1] == ':':
          emoji = words[0][:-1]
          role_menu[emoji] = words[1:]
  
  if message.channel.id not in role_menu_channels:
    role_menu_channels[message.channel.id] = dict()

  role_menu_channels[message.channel.id][message.id] = role_menu


role_menu_channels = dict()
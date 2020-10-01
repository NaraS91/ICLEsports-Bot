#ICLBot.py

import os
import discord
import random
import asyncio
import time
import giphy_client
import requests
from discord.utils import get
from discord import Member
from giphy_client.rest import ApiException
from pprint import pprint
from datetime import datetime
from datetime import timezone
from dotenv import load_dotenv

load_dotenv()

client = discord.Client()

default_prefix = '!'
prefixes = {}

TOKEN = os.getenv('DISCORD_TOKEN')
LOL_COMMUNITY_GAMES_ID = os.getenv('LOL_COMMUNITY_GAMES_ID')
LOL1 = os.getenv("LOL1")
LOL2 = os.getenv("LOL2")
LOL3 = os.getenv("LOL3")
SOCIETY_API_KEY = os.getenv("SOCIETY_API_KEY")
UNION_API_ENDPOINT = os.getenv("UNION_API_ENDPOINT")
CENTRE_CODE = os.getenv("CENTRE_CODE")
MEMBERSHIP_ROLE_ID = os.getenv("MEMBERSHIP_ROLE_ID")
MAIN_GUILD_ID = os.getenv("MAIN_GUILD_ID")

#gify settings
api_instance = giphy_client.DefaultApi()
api_key = os.getenv("GIFY_KEY")
tag = 'anime'
rating = 'g' # str | Filters results by specified rating. (optional)
fmt = 'json' # str | Used to indicate the expected response format. Default is Json. (optional) (default to json)

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.type == discord.MessageType.default:
        prefix = default_prefix

        if message.channel.type is discord.ChannelType.private:
            await check_dm(message.content, message)
            return

        if message.guild in prefixes:
            prefix = prefixes[message.guild]
        
        if message.content.startswith(prefix):
            await check_command(message.content[1:], message)

#argument is a message without the prefix
async def check_command(message_content, message):
    if (message_content.split()[0] in commands):
        await commands[message_content.split()[0]](message_content.split()[1:], message)

async def check_dm(message_content, message):
    if (message_content.split()[0] in dm_commands):
        await dm_commands[message_content.split()[0]](message_content.split()[1:], message)


#expects array of strings    
async def help(args, message):
    await message.channel.send('implemented methods: \n' + ', '.join(commands.keys()))


#expects array of strings
async def roll_roles(args, message):
    roles = ['top', 'jungle', 'mid', 'adc', 'supp']
    random.shuffle(roles)

    answer = ''

    if (len(args) < 5):
       await message.channel.send('not enough players')
    else:
        for i in range(5):
            answer += f'{args[i]}: {roles[i]}\n'
        await message.channel.send(answer[:-1])

async def anime(args, message):
    try: 
        # Search Endpoint
        api_response = api_instance.gifs_random_get(api_key, tag = "anime", rating='g', fmt=fmt)
        await message.channel.send(api_response.data.url)
    except ApiException as e:
        print("Exception when calling DefaultApi->gifs_random_get: %s\n" % e)

async def remind():
    await client.wait_until_ready()
    while True:
        now = datetime.now(timezone.utc)
        time_str = now.strftime('%H:%M')
        weekday = now.weekday()
        if weekday == 4:
            if time_str == '10:00':
                channel = client.get_channel(int(LOL_COMMUNITY_GAMES_ID))
                await channel.send(f'<@{int(LOL1)}> <@{int(LOL2)}> <@{int(LOL3)}>'
                                   + '\n IT\'S FRIDAY :)')
        await asyncio.sleep(58)

async def register(args, message):
    await message.author.send("To get the membership role please writea message in format:\
                              \nregister yourShortcodeHere \n i.e register nkm2020" )
        

async def dm_register(args, message):
    if len(args) > 0:
        await check_membership(args[0], message)
    else:
        await message.author.send("please use the correct format of answear")


async def check_membership(shortcode, message):
    resp = requests.get(f'{UNION_API_ENDPOINT}/CSP/{CENTRE_CODE}/reports/members',
    auth=(SOCIETY_API_KEY, SOCIETY_API_KEY))

    role_assigned = False
    
    if resp.status_code == 200:
        for member in resp.json():
            if member['Login'] == shortcode:
                role_assigned = True
                await give_role(message)
        if role_assigned:
            await message.author.send("role was assigned successfully")
        else:
            await message.author.send("could not find your membership, it's available to buy here: https://www.imperialcollegeunion.org/activities/a-to-z/esports \
                                    \nif you have already bought the membership try again later or contact any committee member")
    else:
        print(resp.status_code)

async def give_role(message):
    main_guild = client.get_guild(int(MAIN_GUILD_ID))
    mem_role = main_guild.get_role(int(MEMBERSHIP_ROLE_ID))
    member = main_guild.get_member(message.author.id)
    await member.add_roles(mem_role)




commands = {'help': help, 'roll_roles': roll_roles, 'anime': anime, 'register': register}
dm_commands = {'register': dm_register}

client.loop.create_task(remind())
client.run(TOKEN)
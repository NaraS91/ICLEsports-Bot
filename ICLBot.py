#ICLBot.py

import os
import discord
import random
import asyncio
from datetime import datetime
from datetime import timezone
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
LOL_COMMUNITY_GAMES_ID = os.getenv('LOL_COMMUNITY_GAMES_ID')
LOL1 = os.getenv("LOL1")
LOL2 = os.getenv("LOL2")
LOL3 = os.getenv("LOL3")

client = discord.Client()

default_prefix = '!'
prefixes = {}

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.type == discord.MessageType.default:
        prefix = default_prefix

        if message.guild in prefixes:
            prefix = prefixes[message.guild]
        
        if message.content.startswith(prefix):
            await check_command(message.content[1:], message.channel)

#argument is a message without the prefix
async def check_command(message, text_channel):
    if (message.split()[0] in commands):
        await commands[message.split()[0]](message.split()[1:], text_channel)

#expects array of strings    
async def help(args, text_channel):
    await text_channel.send('implemented methods: \n' + ', '.join(commands.keys()))


#expects array of strings
async def roll_roles(args, text_channel):
    roles = ['top', 'jungle', 'mid', 'adc', 'supp']
    random.shuffle(roles)

    message = ''

    if (len(args) < 5):
       await text_channel.send('not enough players')
    else:
        for i in range(5):
            message += f'{args[i]}: {roles[i]}\n'
        await text_channel.send(message[:-1])

async def remind():
    await client.wait_until_ready()
    while True:
        now = datetime.now(timezone.utc)
        time_str = now.strftime('%H:%M')
        weekday = now.weekday()
        print(weekday)
        print(time_str)
        if weekday == 4:
            if time_str == '10:00':
                channel = client.get_channel(int(LOL_COMMUNITY_GAMES_ID))
                await channel.send(f'<@{int(LOL1)}> <@{int(LOL2)}> <@{int(LOL3)}>'
                                   + '\n IT\'S FRIDAY :)')
        await asyncio.sleep(58)


commands = {'help': help, 'roll_roles': roll_roles}

client.loop.create_task(remind())
client.run(TOKEN)
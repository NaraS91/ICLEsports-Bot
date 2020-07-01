#ICLBot.py

import os
import discord
import random
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
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
            message += f'{args[i]}: {roles[i]}, '
        await text_channel.send(message[:-2])
        
commands = {'help': help, 'roll_roles': roll_roles}

client.run(TOKEN)
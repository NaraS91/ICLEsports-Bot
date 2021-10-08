# ICLBot.py

import os
import discord
import random
import asyncio
import time
import giphy_client
import re
import requests
import tweepy
from utils.league_utils import extract_champions
from discord.utils import get
from discord import Member
from giphy_client.rest import ApiException
from pprint import pprint
from datetime import datetime
from datetime import timezone
from dotenv import load_dotenv

class StreamListener(tweepy.StreamListener):
    def __init__(self, channel):
        super(StreamListener, self).__init__()
        self.channel = channel

    def on_status(self, tweet):
        client.loop.create_task(tweet_to_discord(tweet, self.channel))

    def on_error(self, status_code):
        if status_code == 420:
            return False

client = discord.Client()

default_prefix = '!'
prefixes = {}

load_dotenv()

TOKEN = os.environ.get('DISCORD_TOKEN')
SOCIETY_API_KEY = os.environ.get("SOCIETY_API_KEY")
SOCIETY_API_KEY2 = os.environ.get("SOCIETY_API_KEY2")
UNION_API_ENDPOINT = os.environ.get("UNION_API_ENDPOINT")
CENTRE_CODE = os.environ.get("CENTRE_CODE")
CENTRE_CODE2 = os.environ.get("CENTRE_CODE2")
MEMBERSHIP_ROLE_ID = os.environ.get("MEMBERSHIP_ROLE_ID")
MAIN_GUILD_ID = os.environ.get("MAIN_GUILD_ID")
TWEET_CHAT_ID = os.environ.get("TWEET_CHAT_ID")
TWITTER_APP_KEY = os.environ.get("TWITTER_APP_KEY")
TWITTER_APP_SECRET = os.environ.get("TWITTER_APP_SECRET")
TWITTER_KEY = os.environ.get("TWITTER_KEY")
TWITTER_SECRET = os.environ.get("TWITTER_SECRET")
TWITTER_TO_FOLLOW = os.environ.get("TWITTER_TO_FOLLOW")
ROLE_MENU_CHANNEL = int(os.environ.get("ROLE_MENU_CHANNEL"))

intents = discord.Intents(messages=True, guilds=True, members=True)

# gify settings
api_instance = giphy_client.DefaultApi()
api_key = os.environ.get("GIFY_KEY")
tag = 'anime'
rating = 'g'  # age raiting of gify searcg
fmt = 'json'  # response format

league_champions = list()


@client.event
async def on_ready():
    league_champions = extract_champions()
    channel = client.get_channel(int(TWEET_CHAT_ID))
    twitter_listener = StreamListener(channel)
    stream = tweepy.Stream(auth=twitter_api.auth, listener=twitter_listener)
    stream.filter(follow=[TWITTER_TO_FOLLOW], is_async=True)
    await load_role_menus()
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.type == discord.MessageType.default:
        prefix = default_prefix

        # dm messages
        if message.channel.type is discord.ChannelType.private:
            await check_dm(message.content, message)
            return

        if message.guild in prefixes:
            prefix = prefixes[message.guild]

        if message.content.startswith(prefix):
            await check_command(message.content[1:], message)

@client.event
async def on_raw_reaction_add(payload):
    print(role_menu_channels)
    print(payload)
    channel_id = payload.channel_id
    message_id = payload.message_id
    if channel_id != ROLE_MENU_CHANNEL:
        return
    role_menus = role_menu_channels[channel_id]
    if message_id in role_menus:
        role_menu = role_menus[message_id]
        roles = role_menu[payload.emoji.name]
        guild = await client.fetch_guild(payload.guild_id)
        user = await guild.fetch_member(payload.user_id)
        for role_mention in roles:
            role_id = int(role_mention[3:-1])
            role = discord.utils.get(guild.roles, id=role_id)
            if role == None or user == None:
                return
            await user.add_roles(role)

@client.event
async def on_raw_reaction_remove(payload):
    channel_id = payload.channel_id
    message_id = payload.message_id
    if channel_id != ROLE_MENU_CHANNEL:
        return
    role_menus = role_menu_channels[channel_id]
    if message_id in role_menus:
        role_menu = role_menus[message_id]
        roles = role_menu[payload.emoji.name]
        guild = await client.fetch_guild(payload.guild_id)
        user = await guild.fetch_member(payload.user_id)
        for role_mention in roles:
            role_id = int(role_mention[3:-1])
            role = discord.utils.get(guild.roles, id=role_id)
            if role == None or user == None:
                return
            await user.remove_roles(role)

async def load_role_menus():
    channel = await client.fetch_channel(ROLE_MENU_CHANNEL)
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
    
    role_menu_channels[message.channel.id][message.id] = role_menu

# argument is a message without the prefix
async def check_command(message_content, message):
    if (message_content.split()[0] in commands):
        await commands[message_content.split()[0]](message_content.split()[1:], message)


async def check_dm(message_content, message):
    if (message_content.split()[0] in dm_commands):
        await dm_commands[message_content.split()[0]](message_content.split()[1:], message)


# expects array of strings
async def help(args, message):
    await message.channel.send('implemented methods: \n' + ', '.join(commands.keys()))


# expects array of strings
# randomly assigns league roles to given players (5 first strings from args)
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

# role one fo the league roles for you


async def roll_role(args, message):
    roles = ['top', 'jungle', 'mid', 'adc', 'supp']
    random.shuffle(roles)

    await message.channel.send(f'your role is {roles[0]}!')


async def random_champions(args, message):
    renew_champions()
    if not args[0].isnumeric():
        await message.channel.send(f'first argument must be a number indicating number of random champions')
        return

    num = int(args[0])

    if num > len(league_champions):
        await message.channel.send(f'there aren\'t that many champions in league ._.')
        return

    if num < 1:
        await message.channel.send(f'._.')
        return

    await message.channel.send(random.sample(league_champions, num))


async def create_teams(args, message):
    if (len(args) % 2 == 1):
        await message.channel.send('number of players has to be even.')
        return

    if (len(args) == 0):
        await message.channel.send('teams cannot be empty, write some nicks after the command')

    random.shuffle(args)
    response = 'Team 1: '

    for i in range(len(args) // 2):
        response += f'{args[i]} '

    response += '\nTeam 2: '

    for i in range(len(args) // 2, len(args)):
        response += f'{args[i]} '

    await message.channel.send(response)


async def create_teams_vc(args, message):
    authorsVCState = message.author.voice

    if authorsVCState == None:
        await message.channel.send("Join a voice chat to use this command :)")
        return

    voiceChat = authorsVCState.channel

    if authorsVCState == None:
        await message.channel.send("Join a voice chat to use this command :)")
        return

    voiceMembersIds = voiceChat.voice_states.keys()
    voiceMembersNicks = []
    for memberId in voiceMembersIds:
        member = await client.fetch_user(memberId)
        voiceMembersNicks.append(member.name)
    await create_teams(voiceMembersNicks, message)

# flips coin and send the result to chat
async def flip_coin(args, message):
    flip_result = "head!" if random.randint(0, 1) == 0 else "tail!"
    await message.channel.send(flip_result)

# sends a random anime giff from gify
async def anime(args, message):
    try:
        # Search Endpoint
        api_response = api_instance.gifs_random_get(
            api_key, tag="anime", rating='g', fmt=fmt)
        await message.channel.send(api_response.data.url)
    except ApiException as e:
        print("Exception when calling DefaultApi->gifs_random_get: %s\n" % e)

# creates a poll
async def create_poll(args, message):
    args = message.content.splitlines()[1:]
    for i in range(len(args)):
      args[i] = find_roles(message.guild, args[i])
      
    if len(args) > 10 or len(args) < 2:
        await message.channel.send("wrong number of argumetns")
        return

    response = [args[0]]
    numbers = ["one", "two", "three", "four",
               "five", "six", "seven", "eight", "nine"]
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    for i in range(0, len(args) - 1):
        response.append(f':{numbers[i]}: {args[i+1]}')

    message = await message.channel.send('\n'.join(response))
    for i in range(0, len(args) - 1):
        await message.add_reaction(emojis[i])

async def create_role_menu(args, message):
    lines = message.content.splitlines()[1:]
    
    if message.channel.id != ROLE_MENU_CHANNEL:
        await message.channel.send("this is not the role menu channel.")
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
        

# reminds about certain dates periodically
async def remind():
    await client.wait_until_ready()
    while True:
        now = datetime.now(timezone.utc)
        # times_str is a string in format HH:MM
        time_str = now.strftime('%H:%M')
        weekday = now.weekday()
        await asyncio.sleep(58)


async def dm_help(args, message):
    await message.author.send("To get the membership role please write a message in format:\
                              \nregister yourShortcodeHere \ni.e register nkm2021")

# dms message author with further instructions
async def register(args, message):
    await message.author.send("To get the membership role please write a message in format:\
                              \nregister yourShortcodeHere \ni.e register nkm2020")

# checks if message has at least one argument and forwards it to check_membership
async def dm_register(args, message):
    if len(args) > 0:
        await check_membership(args[0], message)
    else:
        await message.author.send("Wrong format. Try:registre your-shortcode-goes-here")


# gives membership role to a student (shortcode) with valid membership
async def check_membership(shortcode, message):
    # response contains all students with a valid membership
    resp = requests.get(f'{UNION_API_ENDPOINT}/CSP/{CENTRE_CODE}/reports/members',
                        auth=(SOCIETY_API_KEY, SOCIETY_API_KEY))

    # 2nd society members
    resp2 = requests.get(f'{UNION_API_ENDPOINT}/CSP/{CENTRE_CODE2}/reports/members',
                         auth=(SOCIETY_API_KEY2, SOCIETY_API_KEY2))

    role_assigned = False

    # checks if API response is without error
    if resp.status_code == 200:
        for member in resp.json():
            if member['Login'] == shortcode:
                role_assigned = True
                await give_role(message)

    if (not role_assigned) and resp2.status_code == 200:
        for member in resp2.json():
            if member['Login'] == shortcode:
                role_assigned = True
                await give_role(message)

    if role_assigned:
        await message.author.send("role was assigned successfully")
    else:
        await message.author.send("Could not find your membership, it's available to buy here: https://www.imperialcollegeunion.org/activities/a-to-z/esports \
                                \nIf you have already bought the membership try again later or contact any committee member")


# gives message author role coresponding to MEMBERSHIP_ROLE_ID
async def give_role(message):
    main_guild = client.get_guild(int(MAIN_GUILD_ID))
    mem_role = main_guild.get_role(int(MEMBERSHIP_ROLE_ID))
    member = await main_guild.fetch_member(message.author.id)
    await member.add_roles(mem_role)

async def tweet_to_discord(tweet, channel):
    if tweet.user.id == int(TWITTER_TO_FOLLOW):
        await channel.send(f'https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}')


def renew_champions():
    global league_champions
    champs = extract_champions()
    if len(champs) > len(league_champions):
        league_champions = champs

def find_roles(guild, text):
  p = re.compile(r'{[^}]*}')
  roles_iter = p.finditer(text)

  new_text = text

  for match in roles_iter:
    pot_role = text[match.span()[0] + 1 : match.span()[1] - 1]
    role = discord.utils.get(guild.roles, name=pot_role)
    if role != None:
      new_text = re.sub('{' + pot_role + '}', role.mention, new_text)
  
  return new_text


commands = {'help': help, 'roll_roles': roll_roles, 'anime': anime, 'register': register,
            'flip': flip_coin, "roll_role": roll_role, 'create_teams': create_teams,
            "create_teams_vc": create_teams_vc, 'poll': create_poll, 'random_champions': random_champions,
            'role_menu': create_role_menu}
dm_commands = {'register': dm_register, 'help': dm_help}
role_menu_channels = {ROLE_MENU_CHANNEL: {}}

twitter_auth = tweepy.OAuthHandler(TWITTER_APP_KEY, TWITTER_APP_SECRET)
twitter_auth.set_access_token(TWITTER_KEY, TWITTER_SECRET)
twitter_api = tweepy.API(twitter_auth)

client.loop.create_task(remind())
client.run(TOKEN)

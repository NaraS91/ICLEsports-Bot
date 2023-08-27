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
import commands.role_menu as rm
import DiscordClient
from utils.league_utils import extract_champions
from discord.utils import get
from discord import Member
from giphy_client.rest import ApiException
from pprint import pprint
from datetime import datetime, timedelta
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

default_prefix = '!'
prefixes = {}

load_dotenv()

CENTRE_CODE = os.environ.get("CENTRE_CODE")
CENTRE_CODE2 = os.environ.get("CENTRE_CODE2")
MEMBERSHIP_ROLE_ID = os.environ.get("MEMBERSHIP_ROLE_ID")
MAIN_GUILD_ID = os.environ.get("MAIN_GUILD_ID")
QUARANTINE_CHANNEL_ID = int(os.environ.get("QUARANTINE_CHANNEL_ID"))
ROLE_MENU_CHANNEL = int(os.environ.get("ROLE_MENU_CHANNEL"))
REDIS_URL = os.environ.get("REDIS_URL")
SELF_PROMO = os.environ.get("SELF_PROMO")
SOCIETY_API_KEY = os.environ.get("SOCIETY_API_KEY")
SOCIETY_API_KEY2 = os.environ.get("SOCIETY_API_KEY2")
TOKEN = os.environ.get('DISCORD_TOKEN')
TWEET_CHAT_ID = os.environ.get("TWEET_CHAT_ID")
TWITTER_APP_KEY = os.environ.get("TWITTER_APP_KEY")
TWITTER_APP_SECRET = os.environ.get("TWITTER_APP_SECRET")
TWITTER_KEY = os.environ.get("TWITTER_KEY")
TWITTER_SECRET = os.environ.get("TWITTER_SECRET")
TWITTER_TO_FOLLOW = os.environ.get("TWITTER_TO_FOLLOW")
UNION_API_ENDPOINT = os.environ.get("UNION_API_ENDPOINT")

client = DiscordClient.DicordClient(ROLE_MENU_CHANNEL, REDIS_URL)

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
    await rm.load_role_menus(client, ROLE_MENU_CHANNEL)
    print(f'{client.user} has connected to Discord!')


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.type == discord.MessageType.default:
        prefix = default_prefix

        # dm messages
        if message.channel.type is discord.ChannelType.private:
            await check_dm(message.content, message)
            return

        if message.channel.id in special_channels:
            await special_channels[message.channel.id](message.content, message)
            return

        if await filter_message(message):
            return

        if message.guild in prefixes:
            prefix = prefixes[message.guild]

        if message.content.startswith(prefix):
            await check_command(message.content[1:], message)

# argument is a message without the prefix
async def check_command(message_content, message):
    if (message_content.split()[0] in commands):
        await commands[message_content.split()[0]](fetch_arguments(message_content), message)
    elif (message_content.split()[0] in admin_commands):
        guild = message.guild
        if message.author.guild_permissions.administrator:
            if message_content.split()[0] == "add_role":
                await admin_commands[message_content.split()[0]](fetch_arguments(message_content), message, client)
            else:
                await admin_commands[message_content.split()[0]](fetch_arguments(message_content), message)
        else:
            await message.channel.send("You have no power in here")

def fetch_arguments(message_content):
    quote_split = message_content.split('"')
    
    args = quote_split[0].split()[1:]
    for i in range(1, len(quote_split)):
        if i % 2 == 0:
            if quote_split[i].strip() != "":
                args.extend(quote_split[i].split())
        else:
            args.append(quote_split[i])

    return args

        

async def check_dm(message_content, message):
    if (message_content.split()[0] in dm_commands):
        await dm_commands[message_content.split()[0]](message_content.split()[1:], message)


# expects array of strings
async def help(args, message):
    await message.channel.send('available commands: \n' + ', '.join(commands.keys()))


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

async def create_raffle(args, message):
    if len(args) < 2:
        await message.channel.send("please specife the raffle id and emote!")
        return

    lines = message.content.splitlines()[1:]

    if len(lines) > 0 and lines[0].startswith("\"\"\""):
        response = await message.channel.send(f'RAFFLE {args[0]}\n' + '\n'.join(lines[1:-1]))
    else:
        response = await message.channel.send(f"RAFFLE {args[0]}")
    
    await response.add_reaction(args[1])


async def end_raffle(args, message, is_exclusive = False):
    channel = message.channel

    if len(args) < 2 or not args[1].isnumeric():
        await channel.send("Number of winners or raffle id was not specified! (first id then number of winners)")
        return

    async for message in channel.history(limit=50):
        if message.author == client.user:
            if message.content.startswith(f"RAFFLE {args[0]}\n"):
                await announce_raffle_winners(message, int(args[1]), is_exclusive)
                return
    
    await channel.send(f"No raffle with \"{args[0]}\" id was found")

async def exclusive_raffle(args, message):
    await end_raffle(args, message, True)

async def announce_raffle_winners(raffle_message, no_winners, is_exclusive):
    if len(raffle_message.reactions) < 1:
        await raffle_message.channel.send("No participants detected")
        return
    
    raffle_reaction = raffle_message.reactions[0]
    for reaction in raffle_message.reactions[1:]:
        raffle_users = await raffle_reaction.users().flatten()
        possible_users = await reaction.users().flatten()
        if len(possible_users) > len(raffle_users):
            raffle_reaction = reaction

    await raffle_reaction.remove(client.user)
    candidates: list = await raffle_reaction.users().flatten()
    if is_exclusive:
        guild_members = dict()
        async for member in raffle_message.guild.fetch_members(limit= None):
            guild_members[member.id] = member
        candidates = list(filter(lambda x: x.id in guild_members and int(MEMBERSHIP_ROLE_ID) in map(lambda role: role.id, guild_members[x.id].roles), candidates))
    winners = random.sample(candidates, min(no_winners, len(candidates)))

    if len(winners) == 0:
        await raffle_message.channel.send("No eligble participants detected")
        return

    await raffle_message.channel.send("Raffle winners are: " + ' '.join(map(lambda w:  w.mention, winners)) + "!!!!")

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

async def create_team_category(args, message):
    if len(args) < 2:
        await message.channel.send("wrong number of arguments")
        return
    guild = message.guild

    role_id = int(args[1][3:-1])
    role = discord.utils.get(guild.roles, id=role_id)
    if role == None:
        await message.channel.send(f"role with {role_id} id does not exist")
        return
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        role: discord.PermissionOverwrite(read_messages=True),
    }
    
    category = await guild.create_category(args[0], overwrites=overwrites)
    await category.create_text_channel("general")
    await category.create_text_channel("resources")
    await category.create_text_channel("clips")
    await category.create_voice_channel("voice")
    await message.channel.send(f"Category is ready")

async def remove_categories(args, message):
    if len(args) < 1:
        await message.channel.send("specify at least 1 id of a category to delete")
        return
    
    for arg in args:
        if not arg.isdigit():
            await message.channel.send(f"{arg} does not represent a valid id")
        else:
            category = client.get_channel(int(arg))
            if not isinstance(category, discord.CategoryChannel):
                await message.channel.send(f"{arg} does not represent a valid category id")
            else:
                for text_channel in category.text_channels:
                    await text_channel.delete()
                for voice_channel in category.voice_channels:
                    await voice_channel.delete()
                
                await category.delete()
                await message.channel.send(f"category with {arg} id was deleted successfully")
    
    await message.channel.send("finished deleteing categories")



async def give_promotions_permission(args, message):
    if len(args) < 1:
        await message.channel.send("wrong number of arguments")
        return
    
    if not args[0].isdigit():
        return

    await client.db.append("allowed", args[0])
    await send_dm(int(args[0]), "Permission given. You can post in the promotion channel now")
    await message.channel.send("permission given")

async def remove_promotions_permission(args, message):
    if len(args) < 1:
        await message.channel.send("wrong number of arguments")
        return
    
    await client.db.remove("allowed", args[0])
    await message.channel.send("permission removed")

async def clear_promotions_permissions(args, message):
    await client.db.clear("allowed")
    await message.channel.send("cleared permissions")

async def show_promotions_permissions(args, message):
    perms = await client.db.get("allowed")
    await message.channel.send(perms)

async def create_roles(args, message):
    guild = message.guild
    
    for arg in args:
        await guild.create_role(name=arg)
    await message.channel.send(f"Roles have been created successfully")        

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

async def send_dm(id, message):
    user = await client.fetch_user(id)
    if user:
        await user.send(message)

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

async def self_promo_commands(content, message):
    author = message.author
    allowed = await client.db.get("allowed")

    if allowed != None and str(author.id) in allowed:
        await message.add_reaction('\N{THUMBS UP SIGN}')
        return
    
    if not isinstance(author, discord.Member) or \
       not ((allowed != None and str(author.id) in allowed) or \
            int(MEMBERSHIP_ROLE_ID) in list(map(lambda role: role.id, author.roles))):
        await message.delete()
        await author.send("Looks like you don't have permission to most in the self promotion channel, please contact one of the admins if you'd like to get permission")
    else:
        await message.add_reaction('\N{THUMBS UP SIGN}')

async def filter_message(message):
    author = client.get_member(message.author.id, message.guild.id)
    if author == None:
        await client.update_members(message.guild)
    author = client.get_member(message.author.id, message.guild.id)
    joinDate = author.joined_at
    delta = datetime.now() - joinDate
    if (delta < timedelta(hours=2) and (len(message.attachments) > 0 or len(message.embeds) or "http" in message.content)):
        channel = client.get_channel(QUARANTINE_CHANNEL_ID)
        await channel.send(content=f'author id: {author.id} \n author name: {author.name} \n message:\n {message.content}')
        if len(message.embeds) > 0:
            await channel.send(embed= message.embeds[0])
        if len(message.attachments) > 0:
            await channel.send(file=await message.attachments[0].to_file())
        await message.delete()
        try:
            await author.send("New users cannot post messages with images and/or link. If the message does not contain them please contact the webmaster.")
        finally:
            return True
    return False





commands = {'help': help, 'roll_roles': roll_roles, 'anime': anime, 'register': register,
            'flip': flip_coin, "roll_role": roll_role, 'create_teams': create_teams,
            "create_teams_vc": create_teams_vc, 'poll': create_poll, 'random_champions': random_champions,
             'raffle': create_raffle, 'raffle_result': end_raffle, 'members_raffle_result': exclusive_raffle}
dm_commands = {'register': dm_register, 'help': dm_help}
admin_commands = {'create_team_category': create_team_category, 'remove_categories': remove_categories, "create_roles": create_roles,
                   "give_perms": give_promotions_permission, "remove_perms": remove_promotions_permission,
                   "clear_perms": clear_promotions_permissions, "show_perms": show_promotions_permissions,
                   'role_menu': rm.create_role_menu, 'add_role': rm.add_role}

special_channels = {int(SELF_PROMO): self_promo_commands}

twitter_auth = tweepy.OAuthHandler(TWITTER_APP_KEY, TWITTER_APP_SECRET)
twitter_auth.set_access_token(TWITTER_KEY, TWITTER_SECRET)
twitter_api = tweepy.API(twitter_auth)

client.loop.create_task(remind())
client.run(TOKEN)

# ICLBot.py

import os
import discord
import random
import asyncio
import time
import giphy_client
import re
import requests
import commands.role_menu as rm
from DiscordClient import DiscordClient
from db.DiscordDB import DiscordDB
from utils.league_utils import extract_champions
from discord.utils import get
from discord import Member, app_commands
from giphy_client.rest import ApiException
from pprint import pprint
from datetime import datetime, timedelta
from datetime import timezone
from dotenv import load_dotenv

default_prefix = '!'
prefixes = {}

load_dotenv()

CENTRE_CODE = os.environ.get("CENTRE_CODE")
CENTRE_CODE2 = os.environ.get("CENTRE_CODE2")
MEMBERSHIP_ROLE_ID = os.environ.get("MEMBERSHIP_ROLE_ID")
MAIN_GUILD_ID = int(os.environ.get("MAIN_GUILD_ID"))
QUARANTINE_CHANNEL_ID = int(os.environ.get("QUARANTINE_CHANNEL_ID"))
ROLE_MENU_CHANNEL = int(os.environ.get("ROLE_MENU_CHANNEL"))
REDIS_URL = os.environ.get("REDIS_URL")
DB_ID = os.environ.get("DB_ID")
SELF_PROMO = os.environ.get("SELF_PROMO")
SOCIETY_API_KEY = os.environ.get("SOCIETY_API_KEY")
SOCIETY_API_KEY2 = os.environ.get("SOCIETY_API_KEY2")
TOKEN = os.environ.get('DISCORD_TOKEN')
UNION_API_ENDPOINT = os.environ.get("UNION_API_ENDPOINT")

command_guilds = [discord.Object(id = MAIN_GUILD_ID)]

client = DiscordClient(ROLE_MENU_CHANNEL)
admin_tree_commands = []

# gify settings
api_instance = giphy_client.DefaultApi()
api_key = os.environ.get("GIFY_KEY")
tag = 'anime'
rating = 'g'  # age raiting of gify searcg
fmt = 'json'  # response format

league_champions = list()
tree = app_commands.CommandTree(client)
db = DiscordDB(DB_ID, client)

@client.event
async def on_ready():
    league_champions = extract_champions()
    await db.sync()
    await rm.load_role_menus(client, ROLE_MENU_CHANNEL)
    await tree.sync(guild = discord.Object(id = MAIN_GUILD_ID))
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
@tree.command(name = "roll_roles", description="Bot will randomly assign league of legends positions to the given players", guilds=command_guilds)
async def roll_roles(interaction, user1:str, user2:str, user3:str, user4:str, user5:str):
    roles = ['top', 'jungle', 'mid', 'adc', 'supp']
    random.shuffle(roles)

    answer = '\n'.join((f'{user1}: {roles[0]}',
                        f'{user2}: {roles[1]}',
                        f'{user3}: {roles[2]}',
                        f'{user4}: {roles[3]}',
                        f'{user5}: {roles[4]}'))

    await interaction.response.send_message(answer)

# role one fo the league roles for you
@tree.command(name = "roll_role", description="Bot will randomly give you a league position", guilds=command_guilds)
async def roll_role(interaction):
    roles = ['top', 'jungle', 'mid', 'adc', 'supp']
    random.shuffle(roles)

    await interaction.response.send_message(f'your role is {roles[0]}!')

@tree.command(name = "random_champions", description="Bot will randomly respond with n random league champions", guilds=command_guilds)
async def random_champions(interaction, num:int):
    renew_champions()

    if num > len(league_champions):
        await interaction.response.send_message(f'there aren\'t that many champions in league ._.')
        return

    if num < 1:
        await interaction.response.send_message(f'._.')
        return

    await interaction.response.send_message(random.sample(league_champions, num))

@tree.command(name = "create_teams", description="creates teams from player names divided with space", guilds=command_guilds)
async def create_teams(interaction, players:str):
    players = players.split[' ']
    if (len(players) % 2 == 1):
        await interaction.response.send_message('number of players has to be even.')
        return

    if (len(players) == 0):
        await interaction.response.send_message('teams cannot be empty, write some nicks after the command')

    random.shuffle(players)
    response = 'Team 1: '

    for i in range(len(players) // 2):
        response += f'{players[i]} '

    response += '\nTeam 2: '

    for i in range(len(players) // 2, len(players)):
        response += f'{players[i]} '

    await interaction.response.send_message(response)


async def create_teams_vc_depricated(args, message):
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

@tree.command(name = "flip_coin", description="flips a coin", guilds=command_guilds)
async def flip_coin(interaction):
    flip_result = "head!" if random.randint(0, 1) == 0 else "tail!"
    await interaction.response.send_message(flip_result)

@tree.command(name = "anime_giff", description="sends a random anime giff", guilds=command_guilds)
async def anime(interaction):
    try:
        # Search Endpoint
        api_response = api_instance.gifs_random_get(
            api_key, tag="anime", rating='g', fmt=fmt)
        await interaction.response.send_message(api_response.data.url)
    except ApiException as e:
        print("Exception when calling DefaultApi->gifs_random_get: %s\n" % e)

async def create_raffle(args, message):
    if len(args) < 2:
        await message.channel.send("please specify the raffle id and emote!")
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
@tree.command(name = "create_poll", description="creates a poll with max 9 options, options should be separated with a comma (,)", guilds=command_guilds)
async def create_poll(interaction: discord.Interaction, message: str, options:str):
    options = list(map(lambda s : s.strip(), options.split(',')))
      
    if len(options) > 10 or len(options) < 1:
        await interaction.response.send_message("wrong number of options, need to be in set 1-9.")
        return

    response = [message]
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    for i in range(len(options)):
        response.append(f'{emojis[i]} {options[i]}')

    message = await interaction.channel.send('\n'.join(response))
    for i in range(len(options)):
        await message.add_reaction(emojis[i])



#@tree.command(name = "create_team_category", description="creats a nule/nse team category", guilds=command_guilds)
async def create_team_category(interaction: discord.Interaction, category_name: str, team_role:str):
    guild = interaction.guild

    role_id = int(team_role[3:-1])
    role = discord.utils.get(guild.roles, id=role_id)
    if role == None:
        await interaction.response.send_message(f"role with {role_id} id does not exist")
        return
    
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        role: discord.PermissionOverwrite(read_messages=True),
    }
    
    try:
        category = await guild.create_category(category_name, overwrites=overwrites)
    except:
        await interaction.response.send_message(f"Something went wrong during category creation. Make sure the category name is valid.")
        return
    await category.create_text_channel("general")
    await category.create_text_channel("resources")
    await category.create_text_channel("clips")
    await category.create_voice_channel("voice")
    await interaction.response.send_message(f"Category is ready")

create_team_category_command = discord.app_commands.Command(name = "create_team_category", description="creats a nule/nse team category", callback=create_team_category)
create_team_category_command.default_permissions = discord.Permissions()
create_team_category_command.guild_only = True
tree.add_command(create_team_category_command, guilds=command_guilds)

async def remove_categories(interaction: discord.Interaction, category_ids: str):    
    for arg in list(map(lambda s : s.strip(), category_ids.split(' '))):
        if not arg.isdigit():
            await interaction.channel.send(f"{arg} does not represent a valid id")
        else:
            category = client.get_channel(int(arg))
            if not isinstance(category, discord.CategoryChannel):
                await interaction.channel.send(f"{arg} does not represent a valid category id")
            else:
                for text_channel in category.text_channels:
                    await text_channel.delete()
                for voice_channel in category.voice_channels:
                    await voice_channel.delete()
                
                await category.delete()
    
    await interaction.response.send_message("finished deleteing categories")
admin_tree_commands.append(discord.app_commands.Command(name = "remove_team_categories", description="removes nule/nse team categories, ids should be separated with a single space", callback=remove_categories))


async def give_promotions_permission(interaction: discord.Interaction, id: str):
    if not id.isdigit():
        await interaction.response.send_message("id should be a number")
        return

    await db.append("allowed", id)
    await interaction.response.send_message("permission given")
admin_tree_commands.append(discord.app_commands.Command(name = "give_promo_permission", description="allows the user to post in self-promotion", callback=give_promotions_permission))
  


async def remove_promotions_permission(interaction: discord.Interaction, id: str):
    if not id.isdigit():
        await interaction.response.send_message("id should be a number")
        return
    
    await db.remove("allowed", id)
    await interaction.response.send_message("permission removed")
admin_tree_commands.append(discord.app_commands.Command(name = "remove_promo_permission", description="removes the user's privillage to post in self-promotion", callback=remove_promotions_permission))


async def clear_promotions_permissions(interaction: discord.Interaction):
    await db.clear("allowed")
    await interaction.response.send_message("cleared permissions")
admin_tree_commands.append(discord.app_commands.Command(name = "clear_promo_permissions", description="removes all given permissions to post in the self-promo.", callback=clear_promotions_permissions))


async def show_promotions_permissions(interaction: discord.Interaction):
    perms = await db.get("allowed")
    await interaction.response.send_message(perms if perms != None else "No perms")
admin_tree_commands.append(discord.app_commands.Command(name = "show_promo_permissions", description="show all users with explicit permission given to post in self promo", callback=show_promotions_permissions))

def quote_args_to_array(args):
    return [arg.strip() for arg in args.split('"') if arg.strip() != '']

async def create_roles(interaction: discord.Interaction, role_names:str):
    guild = interaction.guild
    
    for arg in quote_args_to_array(role_names):
        await guild.create_role(name=arg)
    await interaction.response.send_message(f"Roles have been created successfully")        
admin_tree_commands.append(discord.app_commands.Command(name = "create_roles", description="create roles with given names. Roles should be in a format: '\"role 1\" \"role 2\" \"role 3\"' ", callback=create_roles))


# dms message author with further instructions
@tree.command(name = "register", description="register to get a membership role using your uni shortcode", guilds=command_guilds)
async def register(interaction: discord.Interaction, shortcode: str):
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
                await give_role(interaction.user.id)

    if (not role_assigned) and resp2.status_code == 200:
        for member in resp2.json():
            if member['Login'] == shortcode:
                role_assigned = True
                await give_role(interaction.user.id)

    if role_assigned:
        await interaction.response.send_message("role was assigned successfully", ephemeral=True)
    else:
        await interaction.response.send_message("Could not find your membership, it's available to buy here: https://www.imperialcollegeunion.org/activities/a-to-z/gaming-and-esports \
                                \nIf you have already bought the membership try again later or contact any committee member", ephemeral=True)


# gives message author role coresponding to MEMBERSHIP_ROLE_ID
async def give_role(id):
    main_guild = client.get_guild(MAIN_GUILD_ID)
    mem_role = main_guild.get_role(int(MEMBERSHIP_ROLE_ID))
    member = await main_guild.fetch_member(id)
    await member.add_roles(mem_role)

async def send_dm(id, message):
    user = await client.fetch_user(id)
    if user:
        await user.send(message)

def renew_champions():
    global league_champions
    champs = extract_champions()
    if len(champs) > len(league_champions):
        league_champions = champs

async def self_promo_commands(content, message):
    author = message.author
    allowed = await db.get("allowed")
    if allowed != None and str(author.id) in allowed:
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
    delta = datetime.now(timezone.utc) - joinDate
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





commands = {'poll': create_poll, 'raffle': create_raffle, 'raffle_result': end_raffle, 'members_raffle_result': exclusive_raffle}
admin_commands = {'role_menu': rm.create_role_menu, 'add_role': rm.add_role}

special_channels = {int(SELF_PROMO): self_promo_commands}

for command in admin_tree_commands:
    command.default_permissions = discord.Permissions()
    command.guild_only = True
    tree.add_command(command, guilds=command_guilds)

client.run(TOKEN)

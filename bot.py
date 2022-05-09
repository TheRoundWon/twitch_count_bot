#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__      = "Avik (TheRoundWon) Chowdhury"
__copyright__   = "Copyright 2022, Twitch RoundWon_Bot"
__credits__     = ["NinjaBunny9000: https://github.com/NinjaBunny9000/barebones-twitch-bot", "k0nze: https://github.com/k0nze/twitch_count_bot"]

__license__     = "BSD 3-Clause License"
__version__     = "0.1"

from email.mime import base
import os
import json

from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship, Session, aliased
from pathlib import Path
from os.path import join, dirname
from twitchio.ext import commands
import requests
import json
from BotMaster import *
from StreamMaster import *
import asyncio
import pandas as pd


# credentials
TMI_TOKEN = os.environ.get('TMI_TOKEN')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
BOT_NICK = os.environ.get('BOT_NICK')
BOT_PREFIX = os.environ.get('BOT_PREFIX')
CHANNEL = os.environ.get('CHANNEL')

JSON_FILE = str(os.path.dirname(os.path.realpath(__file__))) + '/data.json'

url = "https://api.chucknorris.io/jokes/random"

bot = commands.Bot(
    irc_token=TMI_TOKEN,
    client_id=CLIENT_ID,
    nick=BOT_NICK,
    prefix=BOT_PREFIX,
    initial_channels=[CHANNEL]
)


@bot.event
async def event_ready():
    """ Runs once the bot has established a connection with Twitch """
    print(f"{BOT_NICK} is online!")
    update_count(0)


@bot.event
async def event_message(ctx):
    """ 
    Runs every time a message is sent to the Twitch chat and relays it to the 
    command callbacks 
    """

    # the bot should not react to itself
    if ctx.author.name.lower() == BOT_NICK.lower():
        return

    # relay message to command callbacks
    await bot.handle_commands(ctx)
    count = get_count()
    if count == 10:
        ctx.content = "!joke"
        await bot.handle_commands(ctx)
        count += 1
    elif count >= 20:
        ctx.content = "!poll-available"
        await bot.hanndle_commands(ctx)
        count = 0
    else:
        count += 1
    update_count(count)

# @bot.event
# async def joke_monitor(ctx):
#     if ctx.author.name.lower() == BOT_NICK.lower():
#         return
#     count = get_count()
#     if count >= 3:
#         joke = get_joke()
#         await bot.handle_commands('joke')
#         count = 0
#     else:
#         count += 1
#     update_count(count)
#     print(count)

@bot.command(name='counts')
async def on_count(ctx):
    """
    Runs when the count command was issued in the Twitch chat and sends the 
    current count to the chat
    """
    count = get_count()
    await ctx.send(f'current count {count}')

@bot.command(name='help')
async def on_help(ctx):
    """
    Runs when the help command was issued in the Twitch chat and sends the available commands
    """
    await ctx.send("""The current available commands are !rules, !joke (mods only), !counts, !sub (reduce msg counts by a number - mods only), !add (add msg counbs by a number - mods only) and !help """)

@bot.command(name="rules")
async def on_rules(ctx):
    """
    Runs on rules command, returns rules for the chat
    """
    await ctx.send("""- Welcoming all with good intentions, we're here to have fun!\n
- Respect Privacy!\n
- Racism, Sexual Harassment and any Behaviour / Language deemed inappropriate by this channel's moderators will result in consequences ranging from a timeout to a ban.\n
- Don't spam adverts for other channels or services for me to get users - spamming will usually result in timeouts to a ban!

    """)

def get_joke():
    """_summary_

    Returns:
        dict: json convereted to dictionary
    """
    r = requests.get(url)
    return json.loads(r.text)

@bot.command(name="joke")
async def on_joke(ctx):
    if(ctx.author.is_mod):
        joke = get_joke()
        await ctx.send(joke['value'])

@bot.command(name="add-game")
async def on_add_game(ctx, engine=engine):
    command_string = ctx.message.content
    command_string = command_string.replace('!add-game', '').strip()

    try: 
        value = int(command_string)
    except:
        await ctx.send("Invalid Entry, Please ask a mod to use the !available command to find the twitch game_ids of the available games")
        return 0
    with Session(engine) as session:
        if bool(session.query(Game_Meta.game_name, Game_Meta.game_id).where(Game_Meta.downloaded == True).where(Game_Meta.game_id == value).all()):
            ctx.send("done!")

@bot.command(name='add')
async def on_add(ctx):
    """
    Runs when the add command was issued in the Twitch chat and adds to the 
    count
    """
    # check if user who issued the command is a mod
    if(ctx.author.is_mod):

        # parse add command
        command_string = ctx.message.content
        # remove '!add' and white space
        command_string = command_string.replace('!add', '').strip()
        # parse int
        value = 0

        try:
            value = int(command_string) 
        except ValueError:
            value = 0

        if value > 0:
            # add to count
            count = get_count()
            count = count + value
            update_count(count)
            await ctx.send(f'updated count to {count}')

@bot.command(name='close')
async def on_close(ctx):
    if (ctx.author.name == os.environ['CHANNEL']):
        await ctx.send(f"{BOT_NICK} going to sleep now!")
        await quit()

@bot.command(name='available')
async def on_available(ctx, engine=engine):
    if (ctx.author.is_mod):
        with Session(engine) as session:
            await ctx.send(f"The available games are...")
            for game_name, game_id in session.query(Game_Meta.game_name, Game_Meta.game_id).where(Game_Meta.downloaded == True).all():
                await ctx.send(f"{game_name} : Game ID: {game_id}")



@bot.command(name='sub')
async def on_sub(ctx):
    """
    Runs when the add command was issued in the Twitch chat and subtracts from 
    the count
    """
    # check if user who issued the command is a mod
    if(ctx.author.is_mod):

        # parse add command
        command_string = ctx.message.content
        # remove '!sub' and white space
        command_string = command_string.replace('!sub', '').strip()
        # parse int
        value = 0

        try:
            value = int(command_string) 
        except ValueError:
            value = 0

        if value > 0:
            # subtract from count
            count = get_count()
            count = count - value
            update_count(count)
            await ctx.send(f'updated count to {count}')



@bot.command(name="poll-game")
async def on_poll(ctx, engine=engine):
    if (ctx.author.name == os.environ['CHANNEL']):
        with Session(engine) as session:
            options = [option[0] for option in session.query(Game_Meta.game_name).select_from(join(TopGames, Game_Meta)).order_by(TopGames.count.desc()).all()]
            nextDate, dur_mode, duration, game_name = session.query(TwitchSchedule.target_time, TwitchSchedule.duration_mode, TwitchSchedule.target_duration, Game_Meta.game_name).select_from(join(TwitchSchedule, Game_Meta)).order_by(TwitchSchedule.target_time).where(TwitchSchedule.polled == False).first()
            options = [option for option in options if option != game_name]
            channel = os.environ['CHANNEL']
            dateString = nextDate.strftime('%b %d')
            time_mapper = {'m': "minutes", "h": "hours", "s": "seconds"}
            poll_results = create_poll("Decide the Next Game to Play!", options[:2], os.environ['CHANNEL'], dateString, duration, time_mapper[dur_mode.name], game_name )
            try:
                url = poll_results['url']
                session.add(StrawPolls(url=url, created_at=datetime.now()))
                session.execute(update(TwitchSchedule).where(TwitchSchedule.target_time == nextDate).values({'polled': True}))
                session.commit()
                await ctx.send(f"New poll available to vote for the next game! Please check it out!{url}")
            except Exception as e:
                print(poll_results)
                print(e)

@bot.command(name="poll-available")
async def on_poll_available(ctx, engine=engine):
    base_url = "https://api.strawpoll.com/v3/polls"
    if (ctx.author.is_mod == True):
        with Session(engine) as session:
            await ctx.send(f"The Currently available polls to vote on are:")
            for url in session.query(StrawPolls.url).all():                    
                await ctx.send(f"Check Poll: {url[0]}")
                await ctx.send(f"The current results are:")
                url_components = url[0].split("/")
                r = requests.get(os.path.join(base_url, url_components[-1], "results"), headers={ 'X-API-KEY': os.environ['STRAWPOLL'] })
                output = json.loads(r.text)
                try:
                    for option in output['poll_options']:
                        await ctx.send(f"{option['value']}, total votes: {option['vote_count']}")
                    await asyncio.sleep(2)
                except:
                    print(output)



@bot.command(name="poll-announce")
async def on_poll_anounce(ctx):
    base_url = "https://api.strawpoll.com/v3/polls"
    if (ctx.author.name == os.environ['CHANNEL']):
        # parse add command
        command_string = ctx.message.content
        # remove '!sub' and white space
        command_string = command_string.replace('!poll-announce', '').strip()
        try:
            value = int(command_string)
        except:
            await ctx.send(f"Please use the format !poll_announce <int> so we know how many times to repeat the messge every 30 minutes")
            return 0
        for i in range(value):
            with Session(engine) as session:
                await ctx.send(f"The Currently available polls to vote on are:")
                for url in session.query(StrawPolls.url).all():
                    await ctx.send(f"There are {value - i } reminders remaining to vote, after these annoucements the results will be locked in!")
                    await ctx.send(f"Check Poll: {url[0]}")
            await asyncio.sleep(60*30)
        
        with Session(engine) as session:
            for url, schedule_id in session.query(StrawPolls.url, StrawPolls.schedule_id).all():
                url_components = url.split("/")
                r = requests.get(os.path.join(base_url, url_components[-1], "results"), headers={ 'X-API-KEY': os.environ['STRAWPOLL'] })
                output = json.loads(r.text)
                df_input = {'Game': [], 'Count': []}
                for output in output['poll_options']:
                    df_input['Game'].append(output['value'])
                    df_input['Count'].append(output['vote_count'])

                df = pd.DataFrame(df_input)
                if len(df.loc[df.Count == df.Count.max()].loc[df.Game.str.contains('Keep it')]) > 0:
                    await ctx.send("Schedule remains unchanged!")
                elif len(df.loc[df.Count == df.Count.max()]) > 0:
                    game_id, game_name = session.query(TopGames.game_id, Game_Meta.game_name).select_from(join(Game_Meta, TopGames)).where(or_(*[Game_Meta.game_name.ilike(f'%{name}%') for name in df.loc[df.Count == df.Count.max()]['Game'].values])).order_by(TopGames.count.desc()).first()
                    session.execute(update(TwitchSchedule).where(TwitchSchedule.id == schedule_id).values({'target_game': game_id}))
                    session.commit()
                    await ctx.send("Schedule Changed for {url} , new game is {game_name}")
                else:
                    await ctx.send("Schedule remains unchanged!")
                
                requests.delete(os.path.join(base_url, url_components[-1], headers={ 'X-API-KEY': os.environ['STRAWPOLL'] }))




                #     if df.loc[df.Count == df.Count.max() & (df.Game.str.contains('Keeep it'))]



def create_poll(title: str, options, channel: str, dateString :str, duration, mode, game_name, _type: str = "multiple_choice", media = None, duplication = "ip", is_private = True, force_appearance=None, allow_comments = True, is_multiple = False, multi_choice_min = None, multi_choice_max = None,randomize = False, require_voter = False, deadline=None, num_winners = 1):
    url = "https://api.strawpoll.com/v3"
    description= f"The following is to decide what {channel} will play at {dateString} for {duration} {mode}.\nCurrently choice is {game_name} "
    payload = {
	"title": title,
	"media": media,
	"poll_options": [{"type": "text", "value": option} for option in options] + [{"type": "text", "value": f"Keep it {game_name}!"}],
	"poll_config": {
		"vote_type": "default",
		"allow_comments": allow_comments,
		"allow_indeterminate": False,
		"allow_other_option": False,
		"custom_design_colors": None,
		"deadline_at": deadline,
		"duplication_checking": duplication,
		"edit_vote_permissions": "nobody",
		"force_appearance": force_appearance,
		"hide_participants": is_private,
		"is_multiple_choice": is_multiple,
		"multiple_choice_min": multi_choice_min,
		"multiple_choice_max": multi_choice_max,
		"number_of_winners": num_winners,
		"randomize_options": randomize,
		"require_voter_names": require_voter,
		"results_visibility": "always",
		"use_custom_design": False
	},
	"poll_meta": {
		"description": description,
		"location": None,
	},
	"type": _type,
	}
    try:
        response = requests.post(url + '/polls', json = payload, headers = { 'X-API-KEY': os.environ['STRAWPOLL'] })
    except Exception as e:
        print(payload, e)
    return json.loads(response.text)

def get_count():
    """ Reads the count from the JSON file and returns it """
    with open(JSON_FILE) as json_file:
        data = json.load(json_file)
        return data['count']


def update_count(count):
    """ Updates the JSON file with count given """
    data = None

    with open(JSON_FILE) as json_file:
        data = json.load(json_file)

    if data is not None:
        data['count'] = count

    with open(JSON_FILE, 'w') as json_file:
        json.dump(data, json_file, sort_keys=True, indent=4)


if __name__ == "__main__":
    # launch bot
    bot.run()

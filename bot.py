#!/usr/bin/env python
# -*- coding: utf-8 -*-


__author__      = "Avik (TheRoundWon) Chowdhury"
__copyright__   = "Copyright 2022, Twitch RoundWon_Bot"
__credits__     = ["NinjaBunny9000: https://github.com/NinjaBunny9000/barebones-twitch-bot", "k0nze: https://github.com/k0nze/twitch_count_bot"]

__license__     = "BSD 3-Clause License"
__version__     = "0.1"


from pathlib import Path
from os.path import join, dirname
from twitchio.ext import commands


from StreamMaster import *

import asyncio

from BotFunctions import *


# credentials
TMI_TOKEN = os.environ.get('TMI_TOKEN')
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
BOT_NICK = os.environ.get('BOT_NICK')
BOT_PREFIX = os.environ.get('BOT_PREFIX')
CHANNEL = os.environ.get('CHANNEL')



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
    update_chat_count(0)


@bot.event
async def event_message(ctx):
    """ 
    Runs every time a message is sent to the Twitch chat and relays it to the 
    command callbacks 
    """

    # the bot should not react to itself
    author_name = ctx.author.name
    if author_name.lower() == BOT_NICK.lower():
        return

    # relay message to command callbacks
    try:
        await bot.handle_commands(ctx)
    except commands.errors.CommandNotFound:
        ctx.content = ""
        await bot.handle_commands(ctx)
    count = get_count()
    if count == 10:
        ctx.content = "!joke"
        await bot.handle_commands(ctx)
        count += 1
    elif count == 20:
        ctx.content = "!game-count"
        await bot.handle_commands(ctx)
        count += 1
    elif count == 30:
        ctx.content = "!final-count"
        await bot.handle_commands(ctx)
        count += 1
     


    elif count >= 40:
        ctx.content = "!poll-available"
        await bot.handle_commands(ctx)
        count = 0
    else:
        count += 1
    update_chat_count(count)
    
    author_id = update_viewer_count(engine, author_name)
    spam_time = monitor_spam(engine, author_id)
    if bool(spam_time):
        await ctx.send(f"User {author_name} has been identified for spamming and will be timed out for ")



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
    await ctx.send("""The Basic available commands for everyone are !rules, !add-game and !help """)
    await ctx.send(f"The following commands are available to followers, subscribers and mods. !poll-available (shows available polls in StrawPoll), !game-count(current counts by game from !add-games), !final-count (Final Count to be used in next poll), !available(Shows which Games {os.environ['CHANNEL']}) has downloaded, !my-stats (see how many points each your votes adds) ")
    await ctx.send(f"The commands for mods only are !joke (random chuck norris joke), !counts(shows message counts), !sub (reduce msg counts by a number), !add (add msg counts by a number")

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
    """ Generates a Chuck Norris command on command
    """
    if(ctx.author.is_mod):
        joke = get_joke()
        await ctx.send(joke['value'])

@bot.command(name="add-game")
async def on_add_game(ctx):
    command_string = ctx.message.content
    command_string = command_string.replace('!add-game', '').strip()
    wait_time = 3

    try: 
        value = int(command_string)
    except:
        await ctx.send("Invalid Entry, Please ask a mod to use the !available command to find the twitch game_ids of the available games. We think you meant to say one of the following:")
        with Session(engine) as session:
            for game_name, game_id in session.query(Game_Meta.game_name, Game_Meta.game_id).where(Game_Meta.game_name.ilike(f"%{command_string}%")).all():
                await ctx.send(f"{game_name} : {game_id}")
            return 0
    with Session(engine) as session:
        if bool(session.query(GameRequest.author).where(GameRequest.author == ctx.author.name).all()):
            for author, create_time in session.query(GameRequest.author, func.max(GameRequest.created_at)).group_by(GameRequest.author).having(GameRequest.author == ctx.author.name).all():
                target_time = create_time + timedelta(minutes=wait_time)
                if (datetime.now() > target_time):
                    for game_name, game_id in session.query(Game_Meta.game_name, Game_Meta.game_id).where(Game_Meta.downloaded == True).where(Game_Meta.game_id == value).all():
                        session.add(GameRequest(author = ctx.author.name, game_id = game_id, created_at = datetime.now()))
                        session.commit()
                        await ctx.send(f"{game_name} added for {ctx.author.name}! Next Submission at {(datetime.now() + timedelta(minutes=wait_time)).strftime('%H:%M:%S')} PST")
                else:
                    
                    await ctx.send(f"{author} must wait {wait_time} min before each submission, next submission possible in {(target_time-datetime.now()).seconds//60} min {(target_time-datetime.now()).seconds%60} ")
        else:
            for game_name, game_id in session.query(Game_Meta.game_name, Game_Meta.game_id).where(Game_Meta.downloaded == True).where(Game_Meta.game_id == value).all():
                session.add(GameRequest(author = ctx.author.name, game_id = game_id, created_at = datetime.now()))
                session.commit()
                await ctx.send(f"{game_name} added for {ctx.author.name}! Next Submission at {(datetime.now() + timedelta(minutes=3)).strftime('%H:%M:%S')} PST")

@bot.command(name="game-count")
async def on_game_count(ctx):
    with Session(engine) as session:
        if bool(session.query(Viewer).where(or_(Viewer.follower==True, Viewer.mod == True, Viewer.subscription == True)).where(Viewer.user_login == ctx.author.name).all()) or bool(ctx.author.is_mod):
            await ctx.send("The Current counts of requests made through !add-game are:")
            for game_name, game_id, count in session.query(Game_Meta.game_name, GameRequest.game_id, func.count(GameRequest.created_at)).select_from(join(GameRequest, Game_Meta)).group_by(GameRequest.game_id).all():
                await ctx.send(f"{game_name}, Game ID: {game_id}, count: {count}")
            await ctx.send("The counts will be finalized at 1am PST every day and added to Final Count going into the next poll. Mods use !final-count to see what's going into the next poll!")

@bot.command(name="final-count")
async def on_final_count(ctx):
    with Session(engine) as session:
        if bool(session.query(Viewer).where(or_(Viewer.follower==True, Viewer.mod == True, Viewer.subscription == True)).where(Viewer.user_login == ctx.author.name).all()) or bool(ctx.author.is_mod):
            await ctx.send("These are the final numbers going into the next vote, next update 1am PST. The Top 2 are used as options in the Straw Poll")
            with Session(engine) as session:
                for i, row in enumerate(session.query(Game_Meta.game_name, TopGames.game_id, TopGames.count).select_from(join(Game_Meta, TopGames)).order_by(TopGames.count.desc()).all()):
                    await ctx.send(f"{i+1} {row[0]} Game ID: {row[1]} Count: {row[2]}")

@bot.command(name="my-stats")
async def on_my_stats(ctx):
    with Session(engine) as session:
        if bool(session.query(Viewer).where(or_(Viewer.follower==True, Viewer.mod == True, Viewer.subscription == True)).where(Viewer.user_login == ctx.author.name).all()) or bool(ctx.author.is_mod):
            await ctx.send(f"Welcome back {ctx.author.name}, your stats are:")
            for momentum, follower, mod, sub in  session.query(PowerViewer.count, Viewer.follower, Viewer.mod, Viewer.subscription).select_from(join(PowerViewer, Viewer, PowerViewer.user_login==Viewer.user_login)).where(Viewer.user_login == ctx.author.name).all():
                await ctx.send(f"Point additions for Momentum: {momentum}, follower: {int(follower)}, mod: {int(mod)}, Subscription: {int(sub)}")




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
            update_chat_count(count)
            await ctx.send(f'updated count to {count}')

@bot.command(name='close')
async def on_close(ctx):
    if (ctx.author.name == os.environ['CHANNEL']):
        await ctx.send(f"{BOT_NICK} going to sleep now!")
        bot._websocket.close()
        await quit()

@bot.command(name='available')
async def on_available(ctx):
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
            update_chat_count(count)
            await ctx.send(f'updated count to {count}')



@bot.command(name="poll-game")
async def on_poll(ctx):
    if (ctx.author.name == os.environ['CHANNEL']):
        with Session(engine) as session:
            options = [option[0] for option in session.query(Game_Meta.game_name).select_from(join(TopGames, Game_Meta)).order_by(TopGames.count.desc()).all()]
            schedule_id, nextDate, dur_mode, duration, game_name = session.query(TwitchSchedule.id, TwitchSchedule.target_time, TwitchSchedule.duration_mode, TwitchSchedule.target_duration, Game_Meta.game_name).select_from(join(TwitchSchedule, Game_Meta)).order_by(TwitchSchedule.target_time).where(TwitchSchedule.polled == False).first()
            options = [option for option in options if option != game_name]
            channel = os.environ['CHANNEL']
            dateString = nextDate.strftime('%b %d at %H:%M')
            time_mapper = {'m': "minutes", "h": "hours", "s": "seconds"}
            poll_results = create_poll("Decide the Next Game to Play!", options[:2]+ ["Keep it {game_name}!"], os.environ['CHANNEL'], dateString, duration, time_mapper[dur_mode.name], game_name )
            try:
                url = poll_results['url']
                session.add(StrawPolls(url=url, created_at=datetime.now(), schedule_id= schedule_id, closed=False))
                session.execute(update(TwitchSchedule).where(TwitchSchedule.id == schedule_id).values({'polled': True}))
                session.commit()
                await ctx.send(f"New poll available to vote for the next game! Please check it out! {url}")
            except Exception as e:
                print(poll_results)
                print(e)

@bot.command(name="poll-create")
async def on_poll_create(ctx):
    if (ctx.author.name == os.environ['CHANNEL']):
        # parse add command
        command_string = ctx.message.content
        # remove '!sub' and white space
        command_string = command_string.replace('!create-poll', '').split("/")
        poll_results = simple_poll(command_string[0], os.environ['CHANNEL'], command_string[1:])
        url  = update_straw_polls(engine, poll_results)
        if isinstance(url, str):
            await ctx.send(f"A new poll created by {os.environ['CHANNEL']}! Please check it out! {url}")
        else:
            await ctx.send(f"Something went wrong with the URL creation, please check logs")

        

@bot.command(name="poll-available")
async def on_poll_available(ctx):
    base_url = "https://api.strawpoll.com/v3/polls"
    with Session(engine) as session:
        # if bool(ctx.author.is_mod):

        if bool(session.query(Viewer).where(or_(Viewer.follower==True, Viewer.mod == True, Viewer.subscription == True)).where(Viewer.user_login == ctx.author.name).all()):
            await ctx.send(f"The Currently available polls to vote on are:")
            for url in session.query(StrawPolls.url).where(StrawPolls.closed == False).all():                    
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
        command_string = command_string.replace('!poll-announce', '').strip().split('/')
        versions = {'a': True, 'b': False}
        try:
            if len(command_string) == 2:
                value = int(command_string[0])
                try:
                    version = versions[command_string[1]]
                except:
                    await ctx.send("incorrect input, 'a' used to capture non scheduled")
                    version = True

                interval = 30
            elif len(command_string) == 3:
                value = int(command_string[0])
                try:
                    version = versions[command_string[1]]
                except:
                    await ctx.send("incorrect input, 'a'  used to capture non scheduled")
                    version = True

                interval = int(command_string[0])
            else:
                value = int(command_string[0])
                version = 'a'
                interval = 30
        except:
            await ctx.send(f"Please use the format !poll_announce <int> so we know how many times to repeat the messge every 30 minutes")
            return 0
        for i in range(value):
            with Session(engine) as session:
                await ctx.send(f"The Currently available polls to vote on are:")
                if bool(version):
                    for url in session.query(StrawPolls.url).where(StrawPolls.closed==False).where(StrawPolls.schedule_id != None).all():
                        await ctx.send(f"There are {value - i } reminders remaining to vote, after these annoucements the results will be locked in!")
                        await ctx.send(f"Check Poll: {url[0]}")
                else:
                    for url in session.query(StrawPolls.url).where(StrawPolls.closed==False).where(StrawPolls.schedule_id == None).all():
                        await ctx.send(f"There are {value - i } reminders remaining to vote, after these annoucements the results will be locked in!")
                        await ctx.send(f"Check Poll: {url[0]}")

            await asyncio.sleep(60*interval)
        
        with Session(engine) as session:
            for s_id, url, schedule_id in session.query(StrawPolls.id, StrawPolls.url, StrawPolls.schedule_id).where(StrawPolls.closed == False).all():
                url_components = url.split("/")
                r = requests.get(os.path.join(base_url, url_components[-1], "results"), headers={ 'X-API-KEY': os.environ['STRAWPOLL'] })
                await asyncio.sleep(1)
                r2 = requests.get(os.path.join(base_url, url_components[-1]), headers={ 'X-API-KEY': os.environ['STRAWPOLL'] })
                output = json.loads(r.text)
                output2 = json.loads(r2.text)
                df_input = {'Game': [], 'Count': []}
                for output in output['poll_options']:
                    df_input['Game'].append(output['value'])
                    df_input['Count'].append(output['vote_count'])
                if bool(schedule_id):
                    df = pd.DataFrame(df_input)
                    if len(df.loc[df.Count == df.Count.max()].loc[df.Game.str.contains('Keep it')]) > 0:
                        await ctx.send("Schedule remains unchanged!")
                    elif len(df.loc[df.Count == df.Count.max()]) > 0:
                        game_id, game_name = session.query(TopGames.game_id, Game_Meta.game_name).select_from(join(Game_Meta, TopGames)).where(or_(*[Game_Meta.game_name.ilike(f'%{name}%') for name in df.loc[df.Count == df.Count.max()]['Game'].values])).order_by(TopGames.count.desc()).first()
                        session.execute(update(TwitchSchedule).where(TwitchSchedule.id == schedule_id).values({'target_game': game_id}))
                        session.commit()
                        await ctx.send(f"Schedule Changed for {url} , new game is {game_name}")
                    else:
                        await ctx.send("Schedule remains unchanged!")
                else:
                    await ctx.send(f"These are the final results of the Poll: {output2['title']}")
                    df = pd.DataFrame(df_input)
                    for ix in df.sort_values(by="Count", ascending=False).index:
                        await ctx.send(f"{df.loc[ix,'Game']}: {df.loc[ix,'Count']}")
                    if len(df.loc[df.Count == df.Count.max()]) == 1:
                        await ctx.send(f"The winner is {df.loc[df.Count == df.Count.max(),'Game'].values[0]}")
                    else:
                        await ctx.send(f"Could not determine a winner!")

                
                session.execute(update(StrawPolls).where(StrawPolls.id == s_id).values({'closed': True}))
                session.commit()

                requests.delete(os.path.join(base_url, url_components[-1]), headers={ 'X-API-KEY': os.environ['STRAWPOLL'] })




                #     if df.loc[df.Count == df.Count.max() & (df.Game.str.contains('Keeep it'))]




if __name__ == "__main__":
    # launch bot
    bot.run()

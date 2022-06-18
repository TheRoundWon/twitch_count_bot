from email.mime import base
import os
import json
from venv import create

from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship, Session, aliased
import requests
import json
import pandas as pd
import time
from datetime import date, datetime, timedelta
from BotMaster import *

JSON_FILE = str(os.path.dirname(os.path.realpath(__file__))) + '/data.json'

url = "https://api.chucknorris.io/jokes/random"

def simple_poll(title: str, channel: str, options, _type: str = "multiple_choice", media = None, duplication = "ip", is_private = True, force_appearance=None, allow_comments = True, is_multiple = False, multi_choice_min = None, multi_choice_max = None,randomize = False, require_voter = False, deadline=None, num_winners = 1):
    
    url = "https://api.strawpoll.com/v3"
    description= f"This is a quick poll from {channel}"
    payload = {
	"title": title,
	"media": media,
	"poll_options": [{"type": "text", "value": option} for option in options],
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

def create_poll(title: str, options, channel: str, dateString :str, duration, mode, game_name, _type: str = "multiple_choice", media = None, duplication = "ip", is_private = True, force_appearance=None, allow_comments = True, is_multiple = False, multi_choice_min = None, multi_choice_max = None,randomize = False, require_voter = False, deadline=None, num_winners = 1):
    url = "https://api.strawpoll.com/v3"
    description= f"The following is to decide what {channel} will play at {dateString} for {duration} {mode}.\nCurrently choice is {game_name} "
    payload = {
	"title": title,
	"media": media,
	"poll_options": [{"type": "text", "value": option} for option in options],
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


def update_chat_count(count):
    """ Updates the JSON file with count given """
    data = None

    with open(JSON_FILE) as json_file:
        data = json.load(json_file)

    if data is not None:
        data['count'] = count

    with open(JSON_FILE, 'w') as json_file:
        json.dump(data, json_file, sort_keys=True, indent=4)

def update_viewer_count(engine, author_name):
    with Session(engine) as session:
        today = datetime.today().date()
        if not bool(session.query(PowerViewer).where(PowerViewer.user_login == ctx.author.name).all()):
            session.add(PowerViewer(user_login = ctx.author.name, count = 1, last_date = datetime.today().date()))
            session.commit()
            # if not bool(session.query(Viewer).where(Viewer.user_login == ctx.author.name).all()):
            #     session.add()
        else:
            for author, last_date, count in session.query(PowerViewer.user_login, PowerViewer.last_date, PowerViewer.count).where(PowerViewer.user_login == ctx.author.name).all():
                if last_date != today and count < 7:
                    count += 1
                    session.execute(update(PowerViewer).where(PowerViewer.user_login == ctx.author.name).values({'count': count, 'last_date': today}))
                    session.commit()

def monitor_spam(engine, author_id):
    pass



def update_straw_polls(engine, poll_results):
    with Session(engine) as session:
        try:
            url = poll_results['url']
            session.add(StrawPolls(url=url, created_at=datetime.now(), closed=False))
            session.commit()
            return url
            
        except Exception as e:
            print(poll_results)
            print(e)
            return poll_results

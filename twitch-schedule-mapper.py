from BotMaster  import *
from sqlalchemy.orm import declarative_base, relationship, Session, aliased
from twitchAPI.twitch import Twitch
import argparse
twitch = Twitch(os.environ['TWITCH_APP_ID'], os.environ['TWITCH_APP_SECRET'])
# target_scope = [AuthScope.CHANNEL_MANAGE_SCHEDULE]
# auth = UserAuthenticator(twitch, target_scope, force_verify = False)
# token, refresh_token = auth.authenticate()
# twitch.set_user_authentication(token, target_scope, refresh_token)

parser = argparse.ArgumentParser()

parser.add_argument("segments", type=int, nargs = "?", const=1, default=7, help="number of segments to add to schedule to upload")
parser.add_argument("td", type=int,  nargs = "?", const=1, default=7, help="timezone adjustment from Twitch GMT to PST")
args = parser.parse_args()

def main(twitch, engine, segments, td):
    output = twitch.get_channel_stream_schedule(os.environ['TWITCH_CHANNEL_ID'])
    with Session(engine) as session:
        for segment in output['data']['segments'][:segments]:
            start_time = datetime.fromisoformat(segment['start_time'][:-1])
            end_time = datetime.fromisoformat(segment['end_time'][:-1])
            if (end_time - start_time).seconds%3600 == 0:
                mode = Timing.h
                duration = (end_time - start_time).seconds//60 //60
            else:
                mode = Timing.m
                duration = (end_time - start_time).seconds//60 + (end_time - start_time).seconds%60
            if not bool(session.query(TwitchSchedule).where(TwitchSchedule.twitch_ref == segment['id']).all()):
                session.add(TwitchSchedule(twitch_ref = segment['id'], target_time = start_time - timedelta(hours=td), target_duration=duration, duration_mode=mode, target_game = segment['category']['id'], polled=False))
                session.commit()
            else:
                session.execute(update(TwitchSchedule).where(TwitchSchedule.twitch_ref == segment['id']).values({
                    'target_time': start_time - timedelta(hours=td), "target_duration": duration,
                    "duration_mode": mode, "target_game" : segment['category']['id']
                    }
                ))
                session.commit()



if __name__ == "__main__":
    try:
        main(twitch, engine, args.segments, args.td)
        print('All Done!')
    except Exception as e:
        print(e)


from BotMaster import *
import requests

from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope

def main( engine):
    twitch = Twitch(os.environ['TWITCH_APP_ID'], os.environ['TWITCH_APP_SECRET'])
    base_url = "https://api.strawpoll.com/v3/polls"

    target_scope = [AuthScope.CHANNEL_MANAGE_SCHEDULE]
    auth = UserAuthenticator(twitch, target_scope, force_verify = False)
    token, refresh_token = auth.authenticate()
    twitch.set_user_authentication(token, target_scope, refresh_token)
    with Session(engine) as session:
        for twitch_ref, target_game in session.query(TwitchSchedule.twitch_ref, TwitchSchedule.target_game).select_from(join(TwitchSchedule, StrawPolls)).where(StrawPolls.closed == True).where(TwitchSchedule.polled == True).all():
            twitch.update_channel_stream_schedule_segment(os.environ['TWITCH_CHANNEL_ID'], twitch_ref, category_id = target_game)
        for schedule_id in session.query(TwitchSchedule.id).where(TwitchSchedule.target_time < datetime.now()).all():
            for url in session.query(StrawPolls.url).where(StrawPolls.schedule_id == schedule_id[0]).all():
                url_components = url[0].split("/")
                requests.delete(os.path.join(base_url, url_components[-1]), headers={ 'X-API-KEY': os.environ['STRAWPOLL'] })
            session.query(StrawPolls).where(StrawPolls.schedule_id == schedule_id[0]).update({'closed': True})
            session.commit()
        session.query(StrawPolls).where(StrawPolls.closed == True).delete()
        session.query(TwitchSchedule).where(TwitchSchedule.target_time < datetime.now()).delete()
        session.commit()

if __name__ == "__main__":
    main(engine)
    print('All Done')
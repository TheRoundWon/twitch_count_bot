from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship, Session, aliased
from BotMaster import *
import time
from twitchAPI.twitch import Twitch
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.types import AuthScope

twitch = Twitch(os.environ['TWITCH_APP_ID'], os.environ['TWITCH_APP_SECRET'])

target_scope = [AuthScope.CHANNEL_MANAGE_SCHEDULE, AuthScope.MODERATION_READ, AuthScope.CHANNEL_READ_SUBSCRIPTIONS]
auth = UserAuthenticator(twitch, target_scope, force_verify = False)
token, refresh_token = auth.authenticate()
twitch.set_user_authentication(token, target_scope, refresh_token)

def main(twitch, engine):

    
    with Session(engine) as session: # Loop for first page
        seed = twitch.get_users_follows(to_id=os.environ['TWITCH_CHANNEL_ID'])
        for item in seed['data']:
            if not bool(session.query(Viewer).where(Viewer.id==item['from_id']).all()):
                session.add(Viewer(id=item['from_id'], user_login=item['from_login'] , user_name = item['from_name'], follower = True))
                session.commit()
            else:
                session.execute(update(Viewer).where(Viewer.id==item['from_id']).values({'follower': True, 'user_login': item['from_login'], 'user_name' : item['from_name']}))
                session.commit()
        while bool(seed['pagination']): # Loop for remaining pages
            nextPage = seed['pagination']['cursor']
            seed = twitch.get_users_follows(to_id=os.environ['TWITCH_CHANNEL_ID'], after=nextPage)

            for item in seed['data']:
                if not bool(session.query(Viewer).where(Viewer.id==item['from_id']).all()):
                    session.add(Viewer(id=item['from_id'], user_login=item['from_login'] , user_name = item['from_name'], follower = True))
                    session.commit()
                else:
                    session.execute(update(Viewer).where(Viewer.id==item['from_id']).values({'follower': True}))
                    session.commit()
                
            time.sleep(.5)

        seed = twitch.get_moderators(os.environ['TWITCH_CHANNEL_ID'])

        for item in seed['data']:
            if not bool(session.query(Viewer).where(Viewer.id==item['user_id']).all()):
                session.add(Viewer(id=item['user_id'], user_login=item['user_login'] , user_name = item['user_name'], mod = True))
                session.commit()
            else:
                session.execute(update(Viewer).where(Viewer.id==item['user_id']).values({'mod': True}))
                session.commit()
        while bool(seed['pagination']): # Loop for remaining pages
            nextPage = seed['pagination']['cursor']
            seed = twitch.get_moderators(to_id=os.environ['TWITCH_CHANNEL_ID'], after=nextPage)

            for item in seed['data']:
                if not bool(session.query(Viewer).where(Viewer.id==item['from_id']).all()):
                    session.add(Viewer(id=item['user_id'], user_login=item['user_login'] , user_name = item['user_name'], mod = True))
                    session.commit()
                else:
                    session.execute(update(Viewer).where(Viewer.id==item['user_id']).values({'mod': True}))
                    session.commit()
                
            time.sleep(.5)


if __name__ == "__main__":
    main(twitch, engine)
    print("All Done!")
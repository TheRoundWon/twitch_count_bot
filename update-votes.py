from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship, Session, aliased
from BotMaster import *




def main(engine):
    with Session(engine) as session:
        gameR = select(GameRequest.author, GameRequest.game_id, func.count(GameRequest.created_at).label('count')).group_by(GameRequest.author, GameRequest.game_id).alias()
        points = select(PowerViewer.count, Viewer.user_login, Viewer.follower, Viewer.mod, Viewer.subscription).select_from(join(PowerViewer, Viewer, PowerViewer.user_login==Viewer.user_login)).alias()
        for game_id, count in session.query(gameR.c.game_id, gameR.c.count + points.c.count + points.c.follower.cast(Integer) + points.c.mod.cast(Integer) + points.c.subscription.cast(Integer)).select_from(join(gameR, points, gameR.c.author == points.c.user_login)).group_by(gameR.c.game_id).all():
            orig_count = session.query(TopGames.count).where(TopGames.game_id == game_id).first()
            if bool(orig_count):
                newCount = orig_count[0] + count
            else:
                newCount = count
            session.execute(update(TopGames).where(TopGames.game_id == game_id).values({'count': newCount}))
            session.commit()
        session.query(GameRequest).delete()
        session.commit()



if __name__ == "__main__":
    main(engine)
        # session.query(Game_Meta.game_name, GameRequest.game_id, func.count(GameRequest.created_at)).select_from(join(GameRequest, Game_Meta)).group_by(GameRequest.game_id)
from sqlalchemy import *
from sqlalchemy.orm import declarative_base, relationship, Session, aliased
from datetime import datetime, timedelta, date
import enum
import sys
import os
from StreamMaster import *






class Timing(enum.Enum):
    s = 0
    m = 1
    h = 2

class TwitchSchedule(Base):
    __tablename__ = "twitch_schedule"
    id = Column(Integer, primary_key= True)
    twitch_ref = Column(String(255))
    target_time = Column(DateTime)
    target_duration = Column(Integer)
    duration_mode = Column(Enum(Timing))
    target_game = Column(Integer, ForeignKey('game_meta.game_id'))
    polled = Column(Boolean)

class TopGames(Base):
    __tablename__ = "top_games"
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('game_meta.game_id'))
    count = Column(Integer)

class GameRequest(Base):
    __tablename__ = "game_requests"
    id = Column(Integer, primary_key=True)
    author = Column(String(255))
    game_id = Column(Integer, ForeignKey('game_meta.game_id'))
    created_at = Column(DateTime)

class SpamMonitor(Base):
    __tablename__ = "spam_monitor"
    id = Column(Integer, primary_key=True)
    author_name = Column(String(255))
    message = Column(String(500))
    created_at = Column(DateTime)
    message_count = Column(Integer)

class StrawPolls(Base):
    __tablename__ = "strawpoll_monitor"
    id = Column(Integer, primary_key=True)
    url = Column(String(255))
    created_at = Column(DateTime)
    schedule_id = Column(Integer, ForeignKey('twitch_schedule.id'))
    closed = Column(BOOLEAN)

class Viewer(Base):
    __tablename__ = "twitch_viewers"
    id = Column(Integer, primary_key=True)
    user_login = Column(String(255))
    user_name = Column(String(255))
    follower = Column(BOOLEAN)
    mod = Column(BOOLEAN)
    subscription = Column(BOOLEAN)

class PowerViewer(Base):
    __tablename__ = "power_viewer"
    user_login = Column(String(255), primary_key=True)
    count = Column(Integer)
    last_date = Column(Date)

class ViewerStats(Base):
    __tablename__ = 'viewer_stats'
    viewer_id = Column(Integer, ForeignKey('twitch_viewers.id'))
    count = Column(Integer)
    merits = Column(Integer)
    strikes = Column(Integer)
    last_date = Column(Date)

class Actions(enum.Enum):
    s = 0
    m = 1


class Meritocracy(Base):
    __tablename__ = 'meritocracy'
    action = Column(Enum(Actions))
    action_date = Column(DateTime)
    viewer_id = Column(Integer, ForeignKey('twitch_viewers.id'))


if __name__ == "__main__":
    Base.metadata.create_all(engine)


import datetime

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy_utils import database_exists, create_database

from .data import Base, Friend, Hangout

class FriendTrackerDb():
    def __init__(self, path=''):
        self.engine = create_engine(f'sqlite:///{path}')

        if not database_exists(self.engine.url): # Checks for the first time  
            create_database(self.engine.url)     # Create new DB    
            print("Database initialized at "+database_exists(self.engine.url)) # Verifies if database is there or not.
        else:
            print("Database Already Exists")
        
        # create tables if they don't exist
        Base.metadata.create_all(self.engine, checkfirst=True)

        @event.listens_for(self.engine, "connect")
        def do_connect(dbapi_connection, connection_record):
            # disable pysqlite's emitting of the BEGIN statement entirely.
            # also stops it from emitting COMMIT before any DDL.
            dbapi_connection.isolation_level = None

        @event.listens_for(self.engine, "begin")
        def do_begin(conn):
            # emit our own BEGIN
            conn.exec_driver_sql("BEGIN")

    def get_hangouts(self, start: datetime.date=None, end: datetime.date=None) -> list:
        with Session(self.engine) as session:
            return (
                session.query(Hangout)
                .filter(not start or Hangout.date >= start)
                .filter(not end or Hangout.date <= end)
            ).all()

    def get_friends(self, friends: list=None) -> list:
        with Session(self.engine) as session:
            query = session.query(Friend).filter(not friends or Friend.name in friends)
            return query.all()

    def add_hangout(self, date: datetime.date, description: str, friends: list):
        existing_friends = self.get_friends()
        friend_exists = lambda friend_name: any(friend_name == friend.name for friend in existing_friends)
        to_create = (friend for friend in friends if not friend_exists(friend))

        with Session(self.engine) as session:
            for friend in to_create:
                session.add(Friend(name=friend))
            friend_refs = session.query(Friend).filter(Friend.name in friends).all()
            hang = Hangout(date=date, description=description, friends=friend_refs)
            session.add(hang)
            session.commit()

    def update_friend(self, friend: str, frequency: int=None):
        exists = self.get_friends([friend])
        with Session(self.engine) as session:
            if exists:
                (    
                    session.query(Friend)
                    .filter(Friend.name == friend)
                    .update({'frequency': frequency})
                )
            else:
                print("adding", friend, frequency)
                session.add(Friend(name=friend, frequency=frequency))
            session.commit()

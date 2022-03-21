import datetime

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, contains_eager, joinedload, lazyload, subqueryload
from sqlalchemy_utils import database_exists, create_database

from .data import Base, Friend, Hangout
import logging


class FriendTrackerDb:
    def __init__(self, path=""):
        self.engine = create_engine(f"sqlite:///{path}")

        if not database_exists(self.engine.url):  # Checks for the first time
            create_database(self.engine.url)  # Create new DB
            print(
                "Database initialized at " + database_exists(self.engine.url)
            )  # Verifies if database is there or not.
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

    def get_hangouts(
        self,
        start: datetime.date = None,
        end: datetime.date = None,
        friend: str = None,
    ) -> list:
        with Session(self.engine) as session:
            return (
                session.query(Hangout)
                .options(joinedload(Hangout.friends, innerjoin=True))
                .filter(not start or Hangout.date >= start)
                .filter(not end or Hangout.date <= end)
                .filter(not friend or Hangout.friends.any(name=friend))
            ).all()

    def get_friends(self, friends=()) -> list:
        with Session(self.engine) as session:
            if friends:
                return session.query(Friend).filter(Friend.name.in_(friends)).all()
            else:
                return session.query(Friend).all()

    def add_hangout(self, date: datetime.date, description: str, friends: list):
        with Session(self.engine) as session:
            hang = Hangout(date=date, description=description, friends=friends)
            session.add(hang)
            session.commit()

    def update_friend(self, friend: str, frequency: int = None) -> Friend:
        with Session(self.engine) as session:
            if session.query(Friend).filter(Friend.name == friend).all():
                logging.info("updating %s frequency to %d", friend, frequency)
                (
                    session.query(Friend)
                    .filter(Friend.name == friend)
                    .update({"frequency": frequency})
                )
            else:
                logging.info("adding friend %s with frequency %d", friend, frequency)
                session.add(Friend(name=friend, frequency=frequency))
            session.commit()
            return session.query(Friend).filter(Friend.name == friend).one()

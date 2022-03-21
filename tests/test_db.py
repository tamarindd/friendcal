import datetime

import sqlalchemy
import pytest
from friendtracker.db import FriendTrackerDb
from friendtracker.data import Friend


def test_init():
    engine = FriendTrackerDb()
    assert engine


def test_update_friend():
    engine = FriendTrackerDb()
    engine.update_friend("a", 2)
    engine.update_friend("a", 3)
    engine.update_friend("b")
    friends = {friend.name: friend.frequency for friend in engine.get_friends()}
    assert friends == {"a": 3, "b": None}


def test_add_hangout():
    engine = FriendTrackerDb()
    friends = [
        engine.update_friend("a", 2),
        engine.update_friend("b"),
    ]
    engine.add_hangout(datetime.date(2000, 10, 10), "park beers", friends)
    hangouts = engine.get_hangouts()
    assert len(hangouts) == 1
    assert hangouts[0].description == "park beers"
    assert hangouts[0].date == datetime.date(2000, 10, 10)
    friends = {friend.name: friend.frequency for friend in hangouts[0].friends}
    assert friends == {"a": 2, "b": None}


def test_get_hangouts():
    engine = FriendTrackerDb()
    a = engine.update_friend("a")
    b = engine.update_friend("b")
    c = engine.update_friend("c")
    engine.add_hangout(datetime.date(2000, 10, 10), "park beers", [a, b])
    engine.add_hangout(datetime.date(2000, 10, 12), "skiing", [a, c])
    assert len(engine.get_hangouts(friend="c")) == 1
    assert len(engine.get_hangouts(friend="a")) == 2


def test_get_friends():
    engine = FriendTrackerDb()
    engine.update_friend("a", 2)
    engine.update_friend("b", 3)
    assert len(engine.get_friends()) == 2
    assert len(engine.get_friends(["a", "c"])) == 1


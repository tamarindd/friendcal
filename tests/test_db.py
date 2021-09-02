import pytest
import datetime

from friendtracker.db import FriendTrackerDb

def test_init():
    engine = FriendTrackerDb()
    assert engine


def test_update_friend():
    engine = FriendTrackerDb()
    engine.update_friend('remy', 2)
    engine.update_friend('karina')
    friends = engine.get_friends()
    assert len(friends) == 2
    assert friends[0].name == 'remy'
    assert friends[0].frequency == 2
    assert friends[1].name == 'karina'
    assert friends[1].frequency is None


def test_add_hangout():
    engine = FriendTrackerDb()
    engine.update_friend('remy', 2)
    engine.add_hangout(datetime.date(2000, 10, 10), 'park beers', ['remy', 'karina'])
    hangouts = engine.get_hangouts()
    assert len(hangouts) == 1
    assert hangouts[0].description == 'park beers'
    assert hangouts[0].date == datetime.date(2000, 10, 10)
    friends = engine.get_friends()
    assert len(friends) == 2
    assert friends[0].name == 'remy'
    assert friends[0].frequency == 2
    assert friends[1].name == 'karina'
    assert friends[1].frequency is None

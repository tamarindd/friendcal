import argparse
import json
from collections import defaultdict
import datetime

import dateparser

from .db import FriendTrackerDb
from .data import Friend, Hangout


def add_hangout(db: FriendTrackerDb, friends: list, date: str, description: str):
    date = dateparser.parse(date).date()
    friend_refs = {friend.name: friend for friend in db.get_friends(friends)}
    for friend in friends:
        if friend not in friend_refs:
            friend_refs[friend] = db.update_friend(friend)
    db.add_hangout(date, description, friend_refs.values())


def update_friend(db: FriendTrackerDb, friend: str, frequency: int):
    db.update_friend(friend, frequency)


def remove_friend(db, friend: str):
    return  # TODO


def get_hangs(db: FriendTrackerDb, start_date: datetime.date):
    return db.get_hangouts(start_date)


def get_recent_hangs(
    db: FriendTrackerDb, friend_filter: str, start_date: datetime.date
) -> dict:
    return db.get_hangouts(db, start_date, friend_filter)


def get_upcoming_hangs(db: FriendTrackerDb, friend_filter: str, end: datetime.date):
    upcoming_hangs = defaultdict(list)
    overdue_hangs = defaultdict(list)

    today = datetime.now().date()

    if friend_filter:
        friend_filter = [friend_filter]

    for friend in db.get_friends(friend_filter):
        if not friend.frequency:
            continue

        friend_hangs = db.get_hangouts(friend=friend)
        if not friend_hangs:
            upcoming_hangs[today.isoformat()].append(friend.name)
            continue

        last_hang_date = sorted(hang.date for hang in friend_hangs)[-1]
        next_hang_date = last_hang_date + datetime.timedelta(days=friend.frequency)
        if next_hang_date > end:
            continue

        if next_hang_date < today:
            overdue_hangs[next_hang_date.isoformat()].append(friend.name)
        else:
            upcoming_hangs[next_hang_date.isoformat()].append(friend.name)

    return overdue_hangs, upcoming_hangs


def get_calendar(db: FriendTrackerDb, friend_filter: str):
    data = load_data()

    if friend_filter:
        start = dateparser.parse(
            sorted(data[friend_filter].hangs.keys())[-3:][0]
        ).date()
        end = dateparser.parse(f"in {data[friend_filter].frequency} days").date()
    else:
        start = dateparser.parse("7 days ago").date()
        end = dateparser.parse("in 7 days").date()

    recent_hangs = sorted(get_recent_hangs(data, friend_filter, start).items())
    if recent_hangs:
        yield "Past:"
        for hang, friends in recent_hangs:
            date, description = hang
            yield f"\t{date} - {description}: {', '.join(friends)}"

    overdue, upcoming = get_upcoming_hangs(data, friend_filter, end)

    if overdue:
        yield "Overdue:"
        for date, friends in overdue.items():
            yield f"\t{date} - {', '.join(friends)}"

    if upcoming:
        yield "Upcoming:"
        for date, friends in upcoming.items():
            yield f"\t{date} - {', '.join(friends)}"


def initialize_database(json_path, db_path):
    db = FriendTrackerDb(db_path)
    with open(json_path) as f:
        data = json.load(f)

    hangouts = {}
    for friend, friend_data in data.items():
        db.update_friend(friend, friend_data["frequency"])
        for date, description in friend_data["hangs"].items():
            hangout = (date, description)
            if hangout not in hangouts:
                hangouts[hangout] = []
            hangouts[hangout].append(friend)

    for (date, description), friends in hangouts.items():
        db.add_hangout(dateparser.parse(date).date(), description, friends)


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.set_defaults(cmd=None)

    subparsers = parser.add_subparsers(help="sub-command help")

    update_parser = subparsers.add_parser("update", help="update a hangout frquency")
    update_parser.set_defaults(cmd="update")
    update_parser.add_argument("friend", type=str)
    update_parser.add_argument("frequency", type=int)

    remove_parser = subparsers.add_parser("remove", help="delete friend")
    remove_parser.set_defaults(cmd="remove")
    remove_parser.add_argument("friend", type=str)

    hangout_parser = subparsers.add_parser("hangout", help="add a recent/future event")
    hangout_parser.set_defaults(cmd="hangout")
    hangout_parser.add_argument("date")
    hangout_parser.add_argument("description")
    hangout_parser.add_argument("friends", nargs="+")

    calendar_parser = subparsers.add_parser("calendar", help="check calendar +- 1 week")
    calendar_parser.set_defaults(cmd="calendar")
    calendar_parser.add_argument("--friend")

    args = parser.parse_args(args)

    db = FriendTrackerDb()

    if args.cmd == "hangout":
        add_hangout(db, args.friends, args.date, args.description)
    elif args.cmd == "update":
        update_friend(db, args.friend, args.frequency)
    elif args.cmd == "remove":
        remove_friend(db, args.friend)
    elif args.cmd == "calendar":
        for output_line in get_calendar(db, args.friend):
            print(output_line)
    else:
        parser.print_help()

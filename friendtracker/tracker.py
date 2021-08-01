import argparse
import dataclasses
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

import dateparser


@dataclass
class Friend:
    hangs: dict
    frequency: int = None


class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)


def load_data() -> dict:
    try:
        with open('/home/arielle/friendtracker.json') as f:
            return {
                friend: Friend(**data)
                for friend, data in json.load(f).items()
            }
    except FileNotFoundError:
        return {}


def save_data(data: dict):
    saved = json.dumps(data, cls=EnhancedJSONEncoder)
    with open('/home/arielle/friendtracker.json', 'w') as f:
        f.write(saved)


def add_hangout(friends: list, date: str, notes: str):
    data = load_data()
    date = dateparser.parse(date).date().isoformat()
    for friend in friends:
        friend_data = data.setdefault(friend, Friend({}))
        friend_data.hangs[date] = notes
    save_data(data)


def update_friend(friend: str, frequency: int):
    data = load_data()
    data.setdefault(friend, Friend({})).frequency = frequency
    save_data(data)


def remove_friend(friend: str):
    data = load_data()
    data.pop(friend)
    save_data(data)


def get_hangs(friend_data: dict, lower_date_boundary: datetime):
    for date, notes in sorted(friend_data.hangs.items()):
        if dateparser.parse(date).date() >= lower_date_boundary:
            yield date, notes


def get_recent_hangs(data, friend_filter=None, since='7 days ago') -> dict:
    recent_hangs = defaultdict(list)
    for friend in data:
        for hang in get_hangs(data[friend], dateparser.parse(since).date()):
            recent_hangs[hang].append(friend)
    if friend_filter:
        recent_hangs = {
            hang: friends
            for hang, friends in recent_hangs.items()
            if friend_filter in friends
        }
    return recent_hangs


def get_upcoming_hangs(data: dict, friend_filter: str, end: str):
    upcoming_hangs = defaultdict(list)
    overdue_hangs = defaultdict(list)

    today = datetime.now().date()

    if friend_filter:
        data = {
            friend_filter: data[friend_filter]
        }

    for friend, friend_data in data.items():
        if not friend_data.frequency:
            continue
        if not friend_data.hangs:
            upcoming_hangs[today.isoformat()].append(friend)
            continue
        last_hang = dateparser.parse(sorted(friend_data.hangs.keys())[-1]).date()
        next_hang = last_hang + timedelta(days=friend_data.frequency)
        if next_hang > dateparser.parse(end).date():
            continue

        if next_hang < today:
            overdue_hangs[next_hang.isoformat()].append(friend)
        else:
            upcoming_hangs[next_hang.isoformat()].append(friend)

    return overdue_hangs, upcoming_hangs


def get_calendar(friend_filter=None):
    data = load_data()

    if friend_filter:
        start = sorted(data[friend_filter].hangs.keys())[-3:][0]
        end = f'in {data[friend_filter].frequency} days'
    else:
        start = '7 days ago'
        end = 'in 7 days'

    recent_hangs = sorted(get_recent_hangs(data, friend_filter, start).items())
    if recent_hangs:
        yield "Past:"
    for hang, friends in recent_hangs:
        date, description = hang
        yield f"{date}: {description}"
        for friend in friends:
            yield f"\t{friend}"
    
    overdue, upcoming = get_upcoming_hangs(data, friend_filter, end)

    if overdue:
        yield "Overdue:"
        for date, friends in overdue.items():
            yield f"{date}: {', '.join(friends)}"
    
    if upcoming:
        yield "Upcoming:"
        for date, friends in upcoming.items():
            yield f"{date}: {', '.join(friends)}"


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.set_defaults(cmd = None)

    subparsers = parser.add_subparsers(help='sub-command help')

    update_parser = subparsers.add_parser('update', help='update a hangout frquency')
    update_parser.set_defaults(cmd = 'update')
    update_parser.add_argument('friend', type=str)
    update_parser.add_argument('frequency', type=int)

    remove_parser = subparsers.add_parser('remove', help='delete friend')
    remove_parser.set_defaults(cmd = 'remove')
    remove_parser.add_argument('friend', type=str)

    hangout_parser = subparsers.add_parser('hangout', help='add a recent/future event')
    hangout_parser.set_defaults(cmd = 'hangout')
    hangout_parser.add_argument('date')
    hangout_parser.add_argument('description')
    hangout_parser.add_argument('friends', nargs='+')

    calendar_parser = subparsers.add_parser('calendar', help='check calendar +- 1 week')
    calendar_parser.set_defaults(cmd = 'calendar')
    calendar_parser.add_argument('--friend')

    args = parser.parse_args(args)

    if args.cmd == 'hangout':
        add_hangout(args.friends, args.date, args.description)
    elif args.cmd == 'update':
        update_friend(args.friend, args.frequency)
    elif args.cmd == 'remove':
        remove_friend(args.friend)
    elif args.cmd == 'calendar':
        for output_line in get_calendar(args.friend):
            print(output_line)
    else:
        parser.print_help()

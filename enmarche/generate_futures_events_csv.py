# -*- coding: utf-8 -*-

import dateutil.parser
import datetime
import requests
import json

events = requests.get("https://en-marche.fr/api/event").json()


def filter_future_event(event):
    date = dateutil.parser.parse(event['date'].split('T')[0]).replace(minute=0, second=0, microsecond=0).date()
    event['date'] = date.isoformat()
    return date > datetime.date.today()

data = [event for event in events if filter_future_event(event)]

json.dump(data, open('future_events.json', 'w'))



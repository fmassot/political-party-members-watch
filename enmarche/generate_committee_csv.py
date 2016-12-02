# -*- coding: utf-8 -*-

from operator import itemgetter
import dateutil.parser
import requests
from itertools import groupby
import csv

data = requests.get("https://en-marche.fr/api/committee").json()

for committee in data:
    committee['create_datetime'] = dateutil.parser.parse(committee['createdAt'].split('T')[0]).replace(minute=0, second=0, microsecond=0).date()

data = sorted(data, key=itemgetter('create_datetime'))

with open('committee_count.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['date', 'count'])

    for key, group in groupby(data, key=itemgetter('create_datetime')):
        committee_count = len(list(group))
        writer.writerow([key.isoformat(), committee_count])

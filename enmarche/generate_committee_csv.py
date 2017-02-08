# -*- coding: utf-8 -*-

import requests
import csv


def get_committee(id):
    print("download committee with id " + str(id))

    try_count = 0
    while try_count < 5:
        try:
            return requests.get("https://en-marche.fr/api/committee/" + str(id)).json()
        except Exception as e:
            try_count += 1
            print("error", e)

    raise Exception("cannot download committe with id " + str(id))

data = requests.get("https://en-marche.fr/api/committee").json()
committees = (get_committee(committee['id']) for committee in data)

with open('data/macron-committee.csv', 'w') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['id', 'name', 'city', 'zipcode', 'membersCount', 'lat', 'lng'])

    for committee in committees:
        writer.writerow([committee['id'], committee['name'], committee['city'], committee['zipcode'], committee['membersCount'], committee['lat'], committee['lng']])

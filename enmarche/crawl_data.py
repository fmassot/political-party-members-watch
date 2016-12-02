# -*- coding: utf-8 -*-

import datetime
import requests

data = requests.get("https://en-marche.fr/api/stats").json()
data['date'] = datetime.datetime.today().replace(microsecond=0).isoformat()

print('{date},Macron,{userCount},{committeeCount},{eventCount}'.format(**data))
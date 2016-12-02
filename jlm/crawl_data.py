# -*- coding: utf-8 -*-

import datetime
import requests
import re
from bs4 import BeautifulSoup

content = requests.get("http://www.jlm2017.fr/").content
soup = BeautifulSoup(content)

data = {
    'date': datetime.datetime.today().replace(microsecond=0).isoformat(),
    'user_count': re.sub("[^0-9]", "", soup.find(class_="lead").text)
}

print('{date},Mélenchon,{user_count},,'.format(**data))
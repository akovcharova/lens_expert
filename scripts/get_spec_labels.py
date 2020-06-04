#! /usr/bin/env python3
from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup

import time, random, glob
import re
import csv

files = glob.glob('data/lenses/html/*spec.html')

specs = set()
for file in files:
  bs = BeautifulSoup(open(file).read(), 'html.parser')

  rows = bs.find_all('th',{'class':'label'})
  for row in rows:
    specs.add(row.contents[0].lower().strip().replace('/','').replace(' ','_'))

for spec in specs:
  print(spec)
print(len(specs))
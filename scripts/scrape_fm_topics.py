#! /usr/bin/env python3

from urllib.request import urlopen
import requests
import time, random
import os

headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:76.0) Gecko/20100101 Firefox/76.0', 
          'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
session = requests.Session()
base_url = 'https://www.fredmiranda.com'

idfile = open('data/topics.csv')
next(idfile)

for iline, line in enumerate(idfile):
  print('Scraping topic: '+str(iline))
  topic = line.split(',')[0]

  outfile = os.path.join(os.environ.get('RAW_HTML'),'fm/topic_'+topic+'.html')

  if os.path.exists(outfile) and os.stat(outfile).st_size>0:
    print('Topic already retrieved. Skipping...')
    continue

  html = session.get(base_url+'/forum/topic/'+topic, headers=headers) 
  with open(outfile,'w') as f:
    f.write(html.text)
  time.sleep(8*random.uniform(0,1))

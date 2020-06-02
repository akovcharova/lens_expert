#! /usr/bin/env python3

from urllib.request import urlopen
import requests
from bs4 import BeautifulSoup

import time, random
import re
import csv

headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:76.0) Gecko/20100101 Firefox/76.0', 
          'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
session = requests.Session()
base_url = 'https://www.fredmiranda.com'

outfile = open('data/topics.csv','w')
writer = csv.writer(outfile)
writer.writerow(('topic_id','user','title'))

for iboard in range(133): # there are currently pages numbered from 0 to 133
  html = session.get(base_url+'/forum/board/10/'+str(iboard), headers=headers) 
  bs = BeautifulSoup(html.text, 'html.parser')
  time.sleep(2*random.uniform(0,1))

  try: 
    usernames = []
    topic_ids = []
    titles = []
    # get the urls
    urllist = bs.find_all('td', {'onclick':re.compile(r'/forum/topic/*')})
    for url in urllist:
      topic_ids.append(url['onclick'].replace("/forum/topic/",'').replace("'",'').replace(';',''))
      titles.append(url.get_text().replace('\n',''))

    # get user names
    userlist = bs.find_all('a',{'class':{'linkgray'}, 'target':'_blank'})
    for user in userlist:
      usernames.append(user['href'].split('&username=')[1])

    if len(topic_ids) != len(usernames):
      print('ERROR: Mismatch between number of users and topic titles')
      raise
    else:
      for irow in range(len(topic_ids)):
        writer.writerow((topic_ids[irow], usernames[irow], '"'+titles[irow].replace('"','')+'"'))
  except:
    with open('data/board_'+str(iboard)+'.html','w') as f:
      f.write(html.text)

outfile.close()
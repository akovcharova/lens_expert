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
base_url = 'https://www.dpreview.com/products/lenses/all?view=list&page='

outdir = os.path.join(os.environ.get('RAW_HTML'),'specs')

for ipage in range(1,23):
  html = session.get(base_url+str(ipage+1), headers=headers) 
  bs = BeautifulSoup(html.text, 'html.parser')

  products = bs.find('table', {'class':'productList'})
  for row in products.find_all('tr',{'class':'product'}):
    product = row.td.div.a['href'].split('/')[-1]
    print('Retrieving '+product)

    lens_info = session.get(row.td.div.a['href']+'/overview', headers=headers) 
    bs_info = BeautifulSoup(lens_info.text, 'html.parser')
    with open(os.path.join(outdir, product+'_info.html'),'wb') as f:
      f.write(bs_info.prettify('utf-8'))

    lens_spec = session.get(row.td.div.a['href']+'/specifications', headers=headers) 
    bs_spec = BeautifulSoup(lens_spec.text, 'html.parser')
    with open(os.path.join(outdir, product+'_spec.html'),'wb') as f:
      f.write(bs_spec.prettify('utf-8'))

  time.sleep(2*random.uniform(0,1))

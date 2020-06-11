#! /usr/bin/env python3
from bs4 import BeautifulSoup
from collections import OrderedDict
import utils, glob, os, sys, pprint
from termcolor import cprint
import pandas as pd
import psycopg2

debug = False
topic = -1

if topic>0:
  files = glob.glob(os.environ.get('RAW_HTML')+'/fm/topic_'+str(topic)+'.html')
else:
  files = glob.glob(os.environ.get('RAW_HTML')+'/fm/topic_*.html')
print(f'Found {len(files)} files')

fields = [
  'topic_id',
  'lens_id', # matched to spec sheet
  'price',
  'first_date',
  'last_date',
  'item', # original string
  # for debugging
  # 'flen_min_true',
  'flen_min',
  # 'flen_max_true',
  'flen_max',
  # 'f_min_true',
  'f_min',
  # 'condition',
  # 'notes'
  'brand',
  'original_price',
  'announce_date'
]

sql_query = """SELECT * FROM specs_clean"""

con = None
con = psycopg2.connect(database='lens_db', user='ana', host='localhost', password='nonsense')
df = pd.read_sql_query(sql_query,con)
print(df.head())

brands = df['brand'].unique()

def save_lens(slim_df, ilens):
  irow['lens_id'] = slim_df['lens_id'].iloc[ilens]
  irow['brand'] = slim_df['brand'].iloc[ilens]
  irow['original_price'] = slim_df['original_price'].iloc[ilens]
  irow['announce_date'] = slim_df['announce_date'].iloc[ilens]
  irow['flen_max'] = slim_df['flen_max'].iloc[ilens]
  irow['flen_min'] = slim_df['flen_min'].iloc[ilens]
  irow['f_min'] = slim_df['f_min'].iloc[ilens]
  return

df_rows = []
for ifile, file in enumerate(files):
  if debug:
    print(f'---> Processing file {ifile}: {file}')
  else:
    if ifile%100==0:
      print(f'---> Processing file {ifile}.')


  with open(file) as f:
    # print('-'*100)
    bs = BeautifulSoup(f.read(), 'html.parser')

    # grab dates of the posts in the thread
    dates = bs.find_all('td',{'width':'200','nowrap':'','align':'left'})

    # go through all items listed to the thread
    tables = bs.find_all('table',{'bgcolor':'#626262','border':'0','cellspacing':'5','cellpadding':'10'})
    for itab in range(0,len(tables),2):
      # there are a bunch of sections, i.e. spans, for each item
      span = [i.get_text().strip().lower() for i in tables[itab].find_all('span')]
      if debug: 
        pprint.pprint(span)

      if len(span) < 3: # need to at least have the item name and price
        continue

      # go through easy fields first to save parsing time if these don't pass
      # Span 0: Item title
      # Span 1: Available/Sold/Withdrawn/Bought...
      if ('adapter' in span[0]) or ('mount' in span[0]) or ('card' in span[0]) or ('novoflex' in span[0]):
        continue
      if 'sold' not in span[1]:
        continue

      irow = OrderedDict(zip(fields, [None]*len(fields)))
      irow['topic_id'] = file.strip('.html').split('topic_')[1]

      # save dates
      irow['first_date'] = dates[0].get_text()
      irow['last_date'] = dates[-1].get_text()

      # Span 2: Price
      try:
        span[2] = span[2].replace('price:','').replace('$','').replace(',','')
        irow['price'] = float(span[2])
      except:
        continue
        print('----> ERROR:: Could not parse the price.')

      # brand name
      irow['item'] = span[0]
      item = span[0].split(' for ')[0] # to avoid the camera brand also being in the name
      found_brand = False
      # first take care of some composite name possibilities
      if 'fuji' in item:                                brand, found_brand = 'fujifilm', True
      elif 'oly' in item:                               brand, found_brand = 'olympus', True
      elif ('zeiss' in item) and ('sony' in item):      brand, found_brand = 'sony', True
      elif ('rokinon' in item) and ('fuji' in item):    brand, found_brand = 'rokinon', True
      elif ('tamron' in item) and ('sony' in item):     brand, found_brand = 'tamron', True
      elif ('sigma' in item) and ('sony' in item):      brand, found_brand = 'sigma', True
      else:
        for ibrand in brands:
          if ibrand in item:
            if not found_brand:
              brand, found_brand = ibrand, True
            else:
              print(f'MULTI-BRAND:: {irow["topic_id"]} - Found multiple brands in item {itab} title: {span[0]}')
      if not found_brand:
        cprint(f'NO BRAND FOUND:: {irow["topic_id"]} - item {itab} title: {span[0]}','red')
        continue

      slim_df = df[df['brand']==brand]
      ilens = utils.match_lens(slim_df, item)
      if (ilens!=-1):
        save_lens(slim_df, ilens)
      else:
        continue

      # Span 3: Payment method -> skip
      # Span 4: Condition -> not mandatory, since probably all are very good or like new
      irow['condition'] = -1
      try:
        for char in span[4]:
          if char.isdigit():
            irow['condition'] = int(char)
            break
      except:
        print('----> ERROR:: Could not parse condition.')
      
      # Span 5: shipping info -> skip
      # Span 6: notes -> consider: looking at notes
      # if len(span)>6:
      #   irow['notes'] = '"'+span[6].replace('\n','')+'"'

      if debug:
        pprint.pprint(irow)
      # if we made it here, save item for analysis
      df_rows.append(irow)

  # if ifile>1000: 
  #   break


df = pd.DataFrame(df_rows)
df.to_csv('data/sales.csv', index=False)
print(f'Wrote {len(df_rows)} rows to sales.csv')
      


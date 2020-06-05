#! /usr/bin/env python3
from bs4 import BeautifulSoup
from collections import OrderedDict
import pandas as pd
import os, pprint, sys
import glob

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
  'flen_min_reco',
  # 'flen_max_true',
  'flen_max_reco',
  # 'f_min_true',
  'f_min_reco',
  # 'condition',
  # 'notes'
]

df = pd.read_csv('data/lens_specs.csv')
brands = df['brand'].unique()

def match(ref, i):
  return (ref<(i+0.01) and ref>(i-0.01))

def get_str(ival):
  return str(int(ival) if ival%1==0 else float(ival))

def save_lens(slim_df, ilens, flen_min, flen_max, f_min):
  irow['lens_id'] = slim_df['lens_id'].iloc[ilens]
  # irow['flen_max_true'] = slim_df['flen_max'].iloc[ilens]
  # irow['flen_min_true'] = slim_df['flen_min'].iloc[ilens]
  # irow['f_min_true'] = slim_df['f_min'].iloc[ilens]
  irow['flen_max_reco'] = flen_max
  irow['flen_min_reco'] = flen_min
  irow['f_min_reco'] = f_min
  return

df_rows = []
for ifile, file in enumerate(files):
  if debug:
    print(f'---> Processing file {ifile}: {file}')
  else:
    if ifile%100==0:
      print(f'---> Processing file {ifile}.')


  with open(file) as f:
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
      if 'fuji' in item:                             brand, found_brand = 'fujifilm', True
      elif 'oly' in item:                            brand, found_brand = 'olympus', True
      elif ('zeiss' in item) and ('sony' in item):   brand, found_brand = 'sony', True
      elif ('rokinon' in item) and ('fuji' in item): brand, found_brand = 'rokinon', True
      elif ('tamron' in item) and ('sony' in item):  brand, found_brand = 'tamron', True
      elif ('sigma' in item) and ('sony' in item):   brand, found_brand = 'sigma', True
      else:
        for ibrand in brands:
          if ibrand in item:
            if not found_brand:
              brand, found_brand = ibrand, True
            else:
              print(f'MULTI-BRAND:: {irow["topic_id"]} - Found multiple brands in item {itab} title: {span[0]}')
      if not found_brand:
        continue

      slim_df = df[df['brand']==brand]
      irow['lens_id'] == ''
      matches = []
      for ilens in range(len(slim_df)):
        iflen_min = get_str(slim_df['flen_min'].iloc[ilens])
        iflen_max = get_str(slim_df['flen_max'].iloc[ilens])
        if iflen_max!=-1:
          strings_to_try = [iflen_min+'-'+iflen_max, iflen_min+' - '+iflen_max, iflen_min+' '+iflen_max]
          for istr in strings_to_try:
            if istr in item:
              if debug: print('Found match: ', slim_df['lens_id'].iloc[ilens], iflen_min, iflen_max, item)
              matches.append(ilens)
        else:
          strings_to_try = [iflen_min+'mm', iflen_min+' mm', ' '+iflen_min+' ']
          for istr in strings_to_try:
            if istr in item:
              matches.append(ilens)

      if len(matches)==0:
        continue
      elif len(matches)==1:
        ilens = matches[0]
        save_lens(slim_df, ilens, slim_df['flen_min'].iloc[ilens], slim_df['flen_max'].iloc[ilens], slim_df['f_min'].iloc[ilens])
      else:
        fmatches = []
        for ilens in matches:
          if_min = get_str(slim_df['f_min'].iloc[ilens])
          strings_to_try = ['f'+if_min, 'f/'+if_min, 'f '+if_min, ' '+if_min]
          for istr in strings_to_try:
            if istr in item:
              fmatches.append(ilens)
        if len(fmatches)>=1:
          ilens = fmatches[0]
          save_lens(slim_df, ilens, slim_df['flen_min'].iloc[ilens], slim_df['flen_max'].iloc[ilens], slim_df['f_min'].iloc[ilens])
        else: # save even if only matched focal length and not aperture
          ilens = matches[0]
          save_lens(slim_df, ilens, slim_df['flen_min'].iloc[ilens], slim_df['flen_max'].iloc[ilens], slim_df['f_min'].iloc[ilens])

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

  if debug and ifile>1000: 
    break


df = pd.DataFrame(df_rows)
df.to_csv('sales.csv')
print(f'Wrote {len(df_rows)} rows to sales.csv')
      


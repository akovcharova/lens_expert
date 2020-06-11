#! /usr/bin/env python3
import utils, csv, glob, os, sys, pprint
from termcolor import cprint
import pandas as pd
import psycopg2

debug = False

# sql_query = """SELECT * FROM specs_clean"""
# con = psycopg2.connect(database='lens_db', user='ana', host='localhost', password='nonsense')
# df = pd.read_sql_query(sql_query,con)
# print('Loaded lens spec DB. Found {len(df)} entries.')

specs = pd.read_csv('data/specs_clean.csv')

brands = specs['brand'].unique()
print('Considering the following brands:', brands)

def get_lens_id(post, brand_def):
  """
  Returns a list of tuples of lens_id and sentence in which the lens_id appeared.
  """
  lens_ids = []
  sentences = post.split('. ')
  for sent in sentences:
    text = sent.lower()

    # first check if a brand is mentioned, otherwise default to brand in forum title if there is such
    brand = brand_def
    nbrands = 0
    for ibrand in brands:
      if ibrand in text:
        brand = ibrand
        nbrands +=1
    if (nbrands==0 and brand_def=='') or nbrands>1:
      continue

    # Matching similar to FM forums but people refer to the lenses in more ways, so expanding on the strings to try to match
    slim_df = specs[specs['brand']==brand]
    ilens = utils.match_lens(slim_df, text, debug=False)
    if (ilens!=-1):
      lens_ids.append((slim_df['lens_id'].iloc[ilens], text))

  # print('Returning lens IDs:', lens_ids)
  return lens_ids

if __name__ == "__main__":
  activities = {'landscape','wildlife','portraits','low_light'}

  for activity in activities:
    cprint(f'---------------------------------- Parsing reviews for {activity} ----------------------------------','green')
    files = glob.glob(os.environ.get('RAW_HTML')+f'/dprev/{activity}_thread_*.csv')
    print(f'Found {len(files)} files.')

    outfile = open(f'data/usage_{activity}.csv','w')
    writer = csv.writer(outfile)
    writer.writerow(('usage', 'thread', 'lens_id', 'sentences'))

    for i, ifile in enumerate(files):
      thread_id = ifile.split('thread_')[-1].split('.csv')[0]
      # cols: 'thread_forum', 'thread_title', 'post_date', 'user','user_nposts','post_body'
      df_posts = pd.read_csv(ifile)
      df_posts.dropna(inplace=True)

      forum = df_posts['thread_forum'].iloc[0].lower()
      if forum=='Open Talk': # these are usually not about advice
        continue
      # print('Forum title:',forum)

      # check for default brand name
      brand_def = ''
      for ibrand in brands:
        if ibrand in forum:
          brand_def = ibrand
          break

      for post in df_posts['post_body']:
        matches = get_lens_id(post, brand_def)
        for match in matches:
          writer.writerow((activity, thread_id, match[0], match[1]))

    outfile.close()




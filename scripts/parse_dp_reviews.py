#! /usr/bin/env python3
import utils, csv, glob, os, sys, pprint
from termcolor import cprint
import pandas as pd
import psycopg2
import spacy

debug = False

# sql_query = """SELECT * FROM specs_clean"""
# con = psycopg2.connect(database='lens_db', user='ana', host='localhost', password='nonsense')
# df = pd.read_sql_query(sql_query,con)
# print('Loaded lens spec DB. Found {len(df)} entries.')

specs = pd.read_csv('data/specs_clean.csv')

brands = specs['brand'].unique()
print('Considering the following brands:', brands)

nlp = spacy.load('en_core_web_sm')

def get_lens_id(post, brand_def):
  """
  Returns a list of tuples of lens_id and sentence in which the lens_id appeared.
  """
  lens_ids = []
  for sent in post.sents:
    text = sent.text.lower()

    # first check if a brand is mentioned, otherwise default to brand in forum title if there is such
    brand = brand_def
    for ibrand in brands:
      if ibrand in text:
        brand = ibrand
    if brand=='': 
      break

    # Matching similar to FM forums but people refer to the lenses in more ways, so expanding on the strings to try to match
    slim_df = specs[specs['brand']==brand]
    ilens = utils.match_lens(slim_df, text)
    if (ilens!=-1):
      lens_ids.append((slim_df['lens_id'].iloc[ilens], text))

  # print('Returning lens IDs:', lens_ids)
  return lens_ids

if __name__ == "__main__":
  activities = {'landscape','wildlife','portraits','low_light'}

  outfile = open(f'data/usage.csv','w')
  writer = csv.writer(outfile)
  writer.writerow(('usage', 'lens_id', 'sentences'))

  for activity in activities:
    cprint(f'---------------------------------- Parsing reviews for {activity} ----------------------------------','green')
    files = glob.glob(os.environ.get('RAW_HTML')+f'/dprev/{activity}_thread_*.csv')
    print(f'Found {len(files)} files.')
    for ifile in files:
      # cols: 'thread_forum', 'thread_title', 'post_date', 'user','user_nposts','post_body'
      df_posts = pd.read_csv(ifile)
      df_posts.dropna(inplace=True)

      forum = df_posts['thread_forum'].iloc[0]
      if forum=='Open Talk': # these are usually not about advice
        continue

      # check for default brand name
      brand_def = ''
      for ibrand in brands:
        if ibrand in forum:
          brand_def = ibrand
          break

      posts = list(nlp.pipe(df_posts['post_body']))
      for post in posts:
        matches = get_lens_id(post, brand_def)
        for match in matches:
          writer.writerow((activity, match[0], match[1]))

  outfile.close()




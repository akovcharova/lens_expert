#! /usr/bin/env python3
import psycopg2
from termcolor import cprint
import pandas as pd
from pprint import pprint
pd.set_option("display.max_columns", 100)

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA

sql_query = """SELECT * FROM lens_specs"""

# con = None
# con = psycopg2.connect(database='lens_db', user='ana', host='localhost', password='nonsense')
# specs = pd.read_sql_query(sql_query,con)
  
specs = pd.read_csv('data/lens_specs.csv')

cprint(f'Data frame shape: {specs.shape}','blue')
cprint('First 10 rows:','blue')
print(specs.head(10))

cprint('Available specifications:', 'blue')
print(specs.info())

cprint('Summary statistics: ','blue')
print(specs.describe())

# remove columns that should not be considered in the clustering
specs.drop(columns=['lens_id','brand'], inplace=True)

full_pipeline = Pipeline(steps = [
  ('num', StandardScaler()),
  ('pca', PCA(n_components=0.95))
  ])

# PCA finds 14 axes that explain 95% of the variance
reduced = full_pipeline.fit_transform(specs)
print('Explained variance by reduced dimensions:', full_pipeline['pca'].explained_variance_ratio_)



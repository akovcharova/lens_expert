#!/usr/bin/env python3
from termcolor import colored, cprint
import pandas as pd
import numpy as np
np.set_printoptions(precision=2)

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

from sklearn.model_selection import train_test_split
from sklearn.model_selection import cross_val_score
from sklearn.metrics import mean_squared_error

from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import GradientBoostingRegressor
import joblib

def score_me(method, x_train_prepd, y_train):
  scores = cross_val_score(method, x_train_prepd, y_train,
                           scoring="neg_mean_squared_error", cv=10)
  rmse_scores = np.sqrt(-scores)
  print(f"Scores: {rmse_scores}")
  print(f"Mean: {rmse_scores.mean():.2f}")
  print(f"Standard deviation: {rmse_scores.std():.2f}")

if __name__ == "__main__":

  predict_ratio = False

  sales = pd.read_csv('data/sales_clean.csv')

  cprint(f'Data frame shape: {sales.shape}','blue')
  cprint('First 10 rows:','blue')
  print(sales.head(10))
  cprint('Summary statistics: ','blue')
  print(sales.describe())
  cprint('Number of rows per brand:','blue')
  print(sales['brand'].value_counts())

  corr_matrix = sales.corr()
  cprint('Correlation coeffficients:','blue')
  print(corr_matrix['price'].sort_values(ascending=False))

  if (predict_ratio):
    target = 'ret_value'
    sales['ret_value'] = sales['price']/sales['original_price']
    cprint(f'Mean resale/orig price: {sales.ret_value.mean()}','blue')
    cprint(f'Std resale/orig price: {sales.ret_value.std()}','blue')
  else:
    target = 'price'
    cprint(f'Mean resale price: {sales.price.mean()}','blue')
    cprint(f'Std resale price: {sales.price.std()}','blue')

  train_set, test_set = train_test_split(sales, test_size=0.2, random_state=13)
  cprint(f'Columns: {list(train_set)}')

  x_train = train_set[['original_price', 'flen_max', 'flen_min', 'f_min','brand','original_price', 'announce_date']]
  y_train = train_set[target]

  cprint(list(x_train),'yellow')

  num_attr = list(x_train)
  num_attr.remove('brand')
  cat_attr = ['brand']

  full_pipeline = ColumnTransformer([
    ('num', StandardScaler(), num_attr),
    ('cat', OneHotEncoder(), cat_attr),
    ])
    # remainder='passthrough')

  x_train_prepd = full_pipeline.fit_transform(x_train)

  cprint(f'Features shape: {x_train_prepd.shape}','red')

  # similar performance for all, so stick to simple decision tree for now
  score_me(DecisionTreeRegressor(random_state=15), x_train_prepd, y_train)
  # score_me(RandomForestRegressor(n_estimators=30, random_state=13), x_train_prepd, y_train)
  # score_me(GradientBoostingRegressor(max_depth=None, n_estimators=30, learning_rate=1.0), x_train_prepd, y_train)


  # tree_reg = DecisionTreeRegressor(random_state=15)
  # tree_reg.fit(x_train_prepd, y_train)

  # x_test = test_set[['original_price', 'flen_max', 'flen_min', 'f_min','brand','original_price', 'announce_date']]
  # y_test = test_set[target]
  # x_test_prepd = full_pipeline.transform(x_test)
  # y_pred = tree_reg.predict(x_test_prepd)
  # test_rmse = np.sqrt(mean_squared_error(y_test, y_pred))
  # print(f"Test RMSE = {test_rmse:.2f}")

  # train_set.plot(kind='scatter',x='original_price', y='price', figsize=(12, 8))




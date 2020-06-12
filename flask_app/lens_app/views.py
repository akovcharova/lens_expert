from lens_app import app
from flask import render_template
from flask import request

import psycopg2

import pandas as pd 

# results already evaluated for all available lenses, so just loading results
sql_query = """SELECT * FROM results"""
con = psycopg2.connect(database='results_db', user='ana', host='localhost', password='nonsense')
lenses = pd.read_sql_query(sql_query,con)

@app.route('/')

@app.route('/index', methods=['GET'])
def index():
    return render_template("index.html",)

@app.route('/output', methods=['GET','POST'])
def output():

  usage = request.form['usage']
  min_price = float(request.form['min_price'])
  max_price = float(request.form['max_price'])

  selected_new = lenses[(lenses['original_price']>min_price) & (lenses['original_price']<max_price)]
  selected_new = selected_new.nlargest(3, usage+'_score')
  top_new = selected_new['lens_id'].tolist()

  selected_used = lenses[(lenses['resale_price']>min_price) & (lenses['resale_price']<max_price)]
  selected_used = selected_used.nlargest(3, usage+'_score')
  top_used = selected_new['lens_id'].tolist()
  
  return render_template("output.html", top_new=top_new, top_used=top_used)
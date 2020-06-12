from lens_app import app
from flask import render_template
from flask import request

import psycopg2

import pandas as pd 

# results already evaluated for all available lenses, so just loading results
sql_query = """SELECT * FROM results"""
con = psycopg2.connect(database='results_db', user='ana', host='localhost', password='nonsense')
lenses = pd.read_sql_query(sql_query,con)

def get_top_attr(selected, usage, min_price, max_price, used):
  price_lbl = 'resale_price' if used else 'original_price'
  total_score = selected[selected[usage+'_score']>10][usage+'_score'].sum()
  print(total_score)
  selected = lenses[(lenses[price_lbl]>min_price) & (lenses[price_lbl]<max_price)]
  selected = selected.nlargest(3, usage+'_score')

  price_name = 'Expected price' if used else 'Original price'
  img, name, price, ref, pop = [], [], [], [], []
  for i in range(3):
    img.append(selected['image_href'].iloc[i])
    name.append(f"{selected['lens_id'].iloc[i].split('_')[0].capitalize()} ")
    if (selected['flen_max'].iloc[i]!=-1):
      name[i] += f"{selected['flen_min'].iloc[i]:.0f} - {selected['flen_max'].iloc[i]:.0f} mm"
    else:
      name[i] += f"{selected['flen_min'].iloc[i]:.0f} mm"
    name[i] += f" f/{selected['f_min'].iloc[i]:.1f}"

    price.append(f"{price_name}: ${selected[price_lbl].iloc[i]:.2f}")
    pop.append(f"Popularity: {selected[usage+'_score'].iloc[i]/float(total_score)*100:.0f}%")
    ref.append(f"https://www.dpreview.com/products/{selected['lens_id'].iloc[i].split('_')[0]}/lenses/{selected['lens_id'].iloc[i]}")

  return img, name, price, pop, ref

@app.route('/')

@app.route('/index', methods=['GET'])
def index():
    return render_template("index.html",)

@app.route('/output', methods=['GET','POST'])
def output():

  usage = request.form['usage']
  min_price = float(request.form['min_price'])
  max_price = float(request.form['max_price'])

  new_img, new_name, new_price, new_pop, new_ref = get_top_attr(lenses, usage, min_price, max_price, used=False)
  used_img, used_name, used_price, used_pop, used_ref = get_top_attr(lenses, usage, min_price, max_price, used=True)

  return render_template("output.html", usage=usage.replace('_',' '), 
                                        new_img=new_img, new_name=new_name, new_price=new_price, new_pop=new_pop,new_ref=new_ref,
                                        used_img=used_img, used_name=used_name, used_price=used_price, used_pop=used_pop,used_ref=used_ref)

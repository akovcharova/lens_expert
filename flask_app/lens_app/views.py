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
  selected[usage+'_score'] = selected[usage+'_score'].apply(lambda x: 0 if x<5 else x)

  selected = lenses[(lenses[price_lbl]>min_price) & (lenses[price_lbl]<max_price)]
  total_score = selected[usage+'_score'].sum()
  selected = selected.nlargest(3, usage+'_score')

  img, name, price, value, ref, pop = [], [], [], [], [], []
  for i in range(len(selected)):
    img.append(selected['image_href'].iloc[i])
    name.append(f"{selected['lens_id'].iloc[i].split('_')[0].capitalize()} ")
    if (selected['flen_max'].iloc[i]!=-1):
      name[i] += f"{selected['flen_min'].iloc[i]:.0f} - {selected['flen_max'].iloc[i]:.0f} mm"
    else:
      name[i] += f"{selected['flen_min'].iloc[i]:.0f} mm"
    name[i] += f" f/{selected['f_min'].iloc[i]:.1f}"

    price.append(f"Original price: ${selected['original_price'].iloc[i]:.0f}")
    value.append(f"Expected resale value: ${selected['resale_price'].iloc[i]:.0f}")
    pop.append(f"Popularity: {selected[usage+'_score'].iloc[i]/float(total_score)*100:.0f}%")
    ref.append(f"https://www.dpreview.com/products/{selected['lens_id'].iloc[i].split('_')[0]}/lenses/{selected['lens_id'].iloc[i]}/specifications")

  return img, name, price, value, pop, ref

@app.route('/')

@app.route('/index', methods=['GET'])
def index():
    return render_template("index.html",)

@app.route('/about', methods=['GET'])
def about():
    return render_template("about.html",)

@app.route('/output', methods=['POST'])
def output():

  usage = request.form['usage']
  if 'choose' in usage.lower():
    return render_template("error.html", my_output='oops...Intended usage must be specified for optimal results. Please try again.')

  try:
    min_price = float(request.form['min_price'])
  except:
    min_price = 0

  try:
    max_price = float(request.form['max_price'])
  except:
    max_price = 3000

  if min_price>=max_price:
    return render_template("error.html", my_output='oops...Minimum price must be smaller than maximum price. Please try again.')

  new_img, new_name, new_price, new_value, new_pop, new_ref = get_top_attr(lenses, usage, min_price, max_price, used=False)
  used_img, used_name, used_price, used_value, used_pop, used_ref = get_top_attr(lenses, usage, min_price, max_price, used=True)
  usage = usage.replace('_',' ').rstrip('s')

  if len(new_img)<3 or len(used_img)<3:
    return render_template("error.html", my_output='oops...Too few lenses in price range, please enter a wider range of values.')
  else:
    return render_template("output.html", usage=usage, min_price=f"{min_price:.0f}", max_price=f"{max_price:.0f}", 
                                        new_img=new_img, new_name=new_name, new_price=new_price, new_value=new_value, new_pop=new_pop,new_ref=new_ref,
                                        used_img=used_img, used_name=used_name, used_price=used_price, used_value=used_value, used_pop=used_pop,used_ref=used_ref)

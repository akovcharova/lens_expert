#! /usr/bin/env python3
import os, time, glob, pprint, csv, math
from bs4 import BeautifulSoup
from collections import OrderedDict
import pandas as pd

from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
import psycopg2

# -----------  Setting up database
dbname, username = 'lens_db', 'ana'
engine = create_engine(f'postgresql://{username}:nonsense@localhost/{dbname}')
print(f'Created engine: {engine.url}')
if database_exists(engine.url):
  print(f'Database {dbname} found.')
else:
  print(f'Database {dbname} not found. Creating database...',)
  create_database(engine.url)
  print('Done.')

debug = False
do_subset = True

files = glob.glob(os.environ.get('RAW_HTML')+'/specs/*info.html')
print(f'Found {len(files)} files')

specs = [
  'lens_id',                    # object/string --> just for reference, not a feature
  # ---- General Info ----  
  'brand',                      # object/string --> need one-hot encoding
  'original_price',             # float if N/A, exclude lens
  'announce_date',              # just year (consider: months)
  # ---- Principal specs ---- 
  # 'lens_type',                # bool lens_type = zoom/prime --> already clear from the focal length
  'format',                      # bool is Full Frame
  'is_apsc',                    # bool is APS-C
  'is_u43',                     # bool is Micro 4/3rds
  'flen_min',                   # float  --> consider: transform to FF equivalent based on max_format_size for model 
  'flen_max',                   # float
  'image_stabilization',        # bool yes/no
  # 'cipa_image_stabilization_rating', # float, -1 if none
  # 'lens_mount',                 # 
  # ---- Aperture ---- 
  'f_min',            # int
  # 'maximum_aperture_2',        # int, -1 if none
  # 'minimum_aperture_1',        # int
  # 'minimum_aperture_2',        # int, -1 if none
  # 'aperture_ring',               # bool yes/no
  # 'aperture_notes',
  # 'number_of_diaphragm_blades',
  # ---- Optics ---- 
  'elements',                    # int
  'groups',                      # int
  # 'special_elements__coatings',
  # ---- Focus ---- 
  'minimum_focus',               # float
  'maximum_magnification',       # float
  'autofocus',                   # bool
  # 'motor_type',                # consider: deriving categories from data
  # 'full_time_manual',
  # 'focus_method',
  # 'distance_scale',
  # 'dof_scale',
  # 'focus_distance_limiter',
  # 'focus_notes',
  # ---- Physical ---- 
  'weight',                       # int
  # 'diameter',                     # int
  # 'length',                       # int
  # 'materials',                  # consider: metal or no?
  'sealing',                      # bool
  # 'colour',
  # 'internal_zoom',                  # bool: extending or not
  # 'power_zoom',                   # bool
  # 'zoom_lock',                    
  # 'filter_thread',
  # 'filter_notes',
  # 'hood_supplied',
  # 'hood_product_code',
  # 'tripod_collar',
  # 'optional_accessories',
  # 'notes',
]



df_rows = []
for ifile, file in enumerate(files):
  print(f'---> Processing file {ifile}: {file}')
  irow = OrderedDict(zip(specs, [None]*len(specs)))
  
  irow['lens_id'] = file.split('/')[-1].split('_info')[0]
  if irow['lens_id'][0:4] == 'oly_': # a few pages randomly have this abbreviation...
    irow['lens_id'] = irow['lens_id'].replace('oly_','olympus_')
  
  irow['brand'] = irow['lens_id'].split('_')[0]
  if ('lensbaby' in irow['brand']) or ('holga' in irow['brand']): # nonsense
    continue
  
  # parse general info
  bs = BeautifulSoup(open(file).read(), 'html.parser')
  irow['original_price'] = -1
  price_tag = bs.find('div',{'class':'price single'})
  if price_tag is None: 
    price_range = bs.find('div',{'class':'price range'})
    if price_range is not None:
      price_tags = price_range.find_all('span')
      min_ = price_tags[0].contents[0].lower().strip().strip('$').replace(',','')
      max_ = price_tags[2].contents[0].lower().strip().strip('$').replace(',','')
      irow['original_price'] = (float(max_) + float(min_))/2
  else:
    price = price_tag.contents[0].lower().strip().strip('$').replace(',','')
    if 'check' not in price and 'see' not in price: # some lenses just have a link to 'Check prices'... consider later
      irow['original_price'] = float(price)
  if do_subset and irow['original_price']<0: 
    continue

  year_str = bs.find('div',{'class':'shortSpecs'})
  year_str = year_str.contents[2].strip('\n').split('\n')[0].split(',')[-1].strip()
  try:
    irow['announce_date'] = int(year_str)
  except:
    irow['announce_date'] = -1
  if do_subset and irow['announce_date']<2010: 
    continue

  keep = True

  # parse spec sheet
  bs = BeautifulSoup(open(file.replace('_info','_spec')).read(), 'html.parser')
  lbls = bs.find_all('th',{'class':'label'})
  vals = bs.find_all('td',{'class':'value'})
  for i in range(len(lbls)):
    lbl = lbls[i].contents[0].lower().strip().replace('/','').replace(' ','_')
    val = vals[i].contents[0].strip().lower()
    if debug: 
      print(f'Processing label "{lbl}" with value "{val}"')

    if lbl == "focal_length":
      val = val.replace('-','--').replace('–','--')
      if '--' in val:
        val_min, val_max = float(val.split('--')[0]), float(val.split('--')[1])
      else:
        val_min, val_max = float(val), -1
      irow['flen_min'], irow['flen_max'] = val_min, val_max
    elif (lbl == "maximum_aperture"):# or (lbl == "minimum_aperture"):
      val = val.replace('f','').replace('-','--').replace('–','--')
      if '--' in val:
        irow['f_min'] = float(val.split('--')[0])
      else:
        irow['f_min'] = float(val)
    elif lbl in ['image_stabilization','autofocus','sealing']: # ,'power_zoom'
      irow[lbl] = True if 'yes' in val else False
    # elif lbl == 'zoom_method':
    #   irow['internal_zoom'] = True if 'internal' in val else False
    elif lbl == 'max_format_size':
      if 'ff' in val:
        irow['format'] = 2 # assign value according to crop factor
      elif 'aps-c' in val:
        irow['is_apsc'] = 1.33
      elif 'fourthirds' in val:
        irow['is_u43'] = 1
      else:
        keep = False # don't care about medium format 
        # print(f"ERROR:: Unknown {lbl} with value {val} found for {irow['lens_id']}.")
    elif lbl in ['minimum_focus','maximum_magnification']: # 'cipa_image_stabilization_rating'
      irow[lbl] = float(val)
    elif lbl in ['groups','elements','weight']: # ,'diameter','length'
      irow[lbl] = int(val)
    else:
      continue # ignoring some minor specs
      # print(f"ERROR:: Unknown label {lbl} found for {irow['lens_id']}.")

  # some default values
  if irow['image_stabilization'] is None: 
    irow['image_stabilization'] = False
  if irow['sealing'] is None: 
    irow['sealing'] = False
  if irow['autofocus'] is None: 
    irow['autofocus'] = False
  if irow['elements'] is None: 
    irow['elements'] = -1
  if irow['groups'] is None: 
    irow['groups'] = -1
  if irow['weight'] is None: 
    irow['weight'] = -1
  if irow['minimum_focus'] is None: 
    irow['minimum_focus'] = -1
  if irow['maximum_magnification'] is None: 
    irow['maximum_magnification'] = -1
  if irow['flen_min'] is None:
    keep = False
  if irow['flen_max'] is None:
    irow['flen_max'] = -1
  if irow['f_min'] is None:
    irow['f_min'] = -1

  if keep:
    df_rows.append(irow)
  if debug: 
    pprint.pprint(irow)

df = pd.DataFrame(df_rows)
df.to_csv('data/lens_specs.csv', index=False)
print('Wrote lens_specs.csv')

df.to_sql('lens_specs', engine, if_exists='replace')
print('Created lens_db.')






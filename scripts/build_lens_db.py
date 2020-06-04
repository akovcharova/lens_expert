#! /usr/bin/env python3
import os, time, glob, pprint, csv
from bs4 import BeautifulSoup
from collections import OrderedDict
import pandas as pd

debug = False

files = glob.glob(os.environ.get('RAW_HTML')+'/specs/*info.html')
print(f'Found {len(files)} files')

specs = [
  'lens_id',                    # object/string --> just for reference, not a feature
  # ---- General Info ----  
  'brand',                      # object/string --> need one-hot encoding
  'original_price',             # float if N/A, exclude lens
  'announce_date',              # just year (consider: months)
  # ---- Principal specs ---- 
  'is_zoom',                    # bool lens_type = zoom/prime --> true/false
  'max_format_size_ff',         # bool is Full Frame
  'max_format_size_apsc',       # bool is APS-C
  'max_format_size_u43',        # bool is Micro 4/3rds
  'focal_length_min',           # float  --> consider: transform to FF equivalent based on max_format_size for model 
  'focal_length_max',           # float
  'image_stabilization',        # bool yes/no
  'cipa_image_stabilization_rating', # float, -1 if none
  # 'lens_mount',                 # 
  # ---- Aperture ---- 
  'maximum_aperture_1',          # int
  'maximum_aperture_2',          # int, -1 if none
  'minimum_aperture_1',          # int
  'minimum_aperture_2',          # int, -1 if none
  'aperture_ring',               # bool yes/no
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
  'diameter',                     # int
  'length',                       # int
  # 'materials',                  # consider: metal or no?
  'sealing',                      # bool
  # 'colour',
  'internal_zoom',                  # bool: extending or not
  'power_zoom',                   # bool
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
  dict_ = OrderedDict(zip(specs, [None]*len(specs)))
  
  dict_['lens_id'] = file.split('/')[-1].split('_info')[0]
  if dict_['lens_id'][0:4] == 'oly_': # a few pages randomly have this abbreviation...
    dict_['lens_id'] = dict_['lens_id'].replace('oly_','olympus_')
  
  dict_['brand'] = dict_['lens_id'].split('_')[0]
  if ('lensbaby' in dict_['brand']) or ('holga' in dict_['brand']): # nonsense
    continue
  
  # parse general info
  bs = BeautifulSoup(open(file).read(), 'html.parser')
  dict_['original_price'] = -1
  price_tag = bs.find('div',{'class':'price single'})
  if price_tag is None: 
    price_range = bs.find('div',{'class':'price range'})
    if price_range is not None:
      price_tags = price_range.find_all('span')
      min_ = price_tags[0].contents[0].lower().strip().strip('$').replace(',','')
      max_ = price_tags[2].contents[0].lower().strip().strip('$').replace(',','')
      dict_['original_price'] = (float(max_) + float(min_))/2
  else:
    price = price_tag.contents[0].lower().strip().strip('$').replace(',','')
    if 'check' not in price and 'see' not in price: # some lenses just have a link to 'Check prices'... consider later
      dict_['original_price'] = float(price)

  year_str = bs.find('div',{'class':'shortSpecs'})
  year_str = year_str.contents[2].strip('\n').split('\n')[0].split(',')[-1].strip()
  try:
    dict_['announce_date'] = int(year_str)
  except:
    dict_['announce_date'] = -1

  # parse spec sheet
  bs = BeautifulSoup(open(file.replace('_info','_spec')).read(), 'html.parser')
  lbls = bs.find_all('th',{'class':'label'})
  vals = bs.find_all('td',{'class':'value'})
  for i in range(len(lbls)):
    lbl = lbls[i].contents[0].lower().strip().replace('/','').replace(' ','_')
    val = vals[i].contents[0].strip().lower()
    if debug: 
      print(f'Processing label "{lbl}" with value "{val}"')

    if lbl == "lens_type":
      dict_['is_zoom'] = True if 'zoom' in val else False
    elif lbl == "focal_length":
      val = val.replace('-','--').replace('–','--')
      if '--' in val:
        val_min, val_max = float(val.split('--')[0]), float(val.split('--')[1])
      else:
        val_min, val_max = float(val), -1
      dict_[lbl+'_min'], dict_[lbl+'_max'] = val_min, val_max
    elif (lbl == "maximum_aperture") or (lbl == "minimum_aperture"):
      val = val.replace('f','').replace('-','--').replace('–','--')
      if '--' in val:
        val_1, val_2 = float(val.split('--')[0]), float(val.split('--')[1])
      else:
        val_1, val_2 = float(val), -1
      dict_[lbl+'_1'], dict_[lbl+'_2'] = val_1, val_2
    elif lbl in ['image_stabilization','aperture_ring','autofocus','sealing','power_zoom']:
      dict_[lbl] = True if 'yes' in val else False
    elif lbl == 'zoom_method':
      dict_['internal_zoom'] = True if 'internal' in val else False
    elif lbl == 'max_format_size':
      if ('ff' in val) or ('aps-c' in val) or ('fourthirds' in val): 
        dict_['max_format_size_ff'] = True if 'ff' in val else False
        dict_['max_format_size_apsc'] = True if 'aps-c' in val else False
        dict_['max_format_size_u43'] = True if 'fourthirds' in val else False
      else:
        continue # don't care about medium format 
        # print(f"ERROR:: Unknown {lbl} with value {val} found for {dict_['lens_id']}.")
    elif lbl in ['cipa_image_stabilization_rating','minimum_focus','maximum_magnification']:
      dict_[lbl] = float(val)
    elif lbl in ['groups','elements','weight','diameter','length']:
      dict_[lbl] = int(val)
    else:
      continue # ignoring some minor specs
      # print(f"ERROR:: Unknown label {lbl} found for {dict_['lens_id']}.")

  df_rows.append(dict_)
  if debug: 
    pprint.pprint(dict_)

df = pd.DataFrame(df_rows)
df.to_csv('lens_specs.csv')
print('Wrote lens_specs.csv')






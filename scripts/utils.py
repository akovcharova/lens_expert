#! /usr/bin/env python
import os, sys, pprint
from termcolor import cprint
import pandas as pd

def match(ref, i):
  return (ref<(i+0.01) and ref>(i-0.01))

def get_str(ival):
  return str(int(ival) if ival%1==0 else float(ival))

def match_lens(slim_df, text, allow_focal_length_only=True, debug=False):
  ilens = -1
  brand = slim_df['brand'].iloc[0] # they are all the same brand in this subset data frame
  matches = []
  for ilens in range(len(slim_df)):
    if debug: cprint(f"----> Considering match to '{slim_df['lens_id'].iloc[ilens]}'", 'blue')
    iflen_min = get_str(slim_df['flen_min'].iloc[ilens])
    iflen_max = get_str(slim_df['flen_max'].iloc[ilens])
    if slim_df['flen_max'].iloc[ilens]!=-1:
      strings_to_try = [iflen_min+'-'+iflen_max, iflen_min+' - '+iflen_max, iflen_min+' '+iflen_max]
      if debug: print('Try to match focal length:',strings_to_try)
      for istr in strings_to_try:
        if istr in text:
          matches.append(ilens)
          if debug: cprint(f"Found a match for '{istr}' in '{text}'.", 'green')
    else:
      strings_to_try = [iflen_min+'mm', iflen_min+' mm', ' '+iflen_min+' ']
      if debug: print('Try to match focal length:',strings_to_try)
      for istr in strings_to_try:
        if istr in text:
          matches.append(ilens)
          if debug: cprint(f"Found a match for '{istr}' in '{text}'.", 'green')

  if len(matches)==0:
    if debug: cprint(f"SKIP:: Could not find a match for '{text}' with brand set to {brand}",'red')
  elif len(matches)==1:
    ilens = matches[0]
    if debug: cprint(f"KEEP:: Matched '{text}' with brand set to '{brand}' to lens_id '{slim_df['lens_id'].iloc[ilens]}'",'green')
  else:
    fmatches = []
    for ilens in matches:
      if_min = get_str(slim_df['f_min'].iloc[ilens])
      strings_to_try = ['f'+if_min, 'f/'+if_min, 'f '+if_min, ' '+if_min]
      if debug: print('Try to match aperture:',strings_to_try)
      for istr in strings_to_try:
        if istr in text:
          fmatches.append(ilens)
          if debug: print(f"Found a potential match for '{text}' with brand set to '{brand}' to lens_id '{slim_df['lens_id'].iloc[ilens]}'")

    if len(fmatches)>1:
      if debug: cprint(f"DROP:: Found multiple matches for '{text}':", 'red')
      if debug: print([slim_df['lens_id'].iloc[x] for x in fmatches])
    elif len(fmatches)==1:
      ilens = fmatches[0]
      if debug: cprint(f"KEEP:: Matched '{text}' to lens_id '{slim_df['lens_id'].iloc[ilens]}'", 'green')
    else: # save even if only matched focal length and not aperture
      if (allow_focal_length_only):
        ilens = matches[0]
        if debug: cprint(f"KEEP:: Did not match aperture but the best match for '{text}' is lens_id '{slim_df['lens_id'].iloc[ilens]}'", 'yellow')
      else:
        if debug: cprint(f"DROP:: Found multiple lens matches for '{text}':", 'red')

  return ilens

#! /usr/bin/env python
import os, sys, pprint
from termcolor import cprint
import pandas as pd

def match(ref, i):
  return (ref<(i+0.01) and ref>(i-0.01))

def get_str(ival):
  return str(int(ival) if ival%1==0 else float(ival))

def match_lens(slim_df, text, debug=False):
  matched_lens_idx = -1
  if not any(char.isdigit() for char in text):
    # if debug: cprint(f"SKIP:: String does not contain lens specs.",'yellow')
    return matched_lens_idx

  if debug: cprint(f"Processing string: '{text}'.")

  brand = slim_df['brand'].iloc[0] # they are all the same brand in this subset data frame
  matches = []
  for ilens in range(len(slim_df)):
    # if debug: cprint(f"----> Considering match to '{slim_df['lens_id'].iloc[ilens]}'", 'blue')
    iflen_min = get_str(slim_df['flen_min'].iloc[ilens])
    iflen_max = get_str(slim_df['flen_max'].iloc[ilens])
    if slim_df['flen_max'].iloc[ilens]!=-1:
      strings_to_try = [' '+iflen_min+'-'+iflen_max, ' '+iflen_min+' - '+iflen_max, ' '+iflen_min+' '+iflen_max]
      # if debug: print('Try to match focal length:',strings_to_try)
      for istr in strings_to_try:
        if istr in text:
          matches.append(ilens)
          # if debug: cprint(f"Found a match for '{istr}' in '{text}'.", 'green')
    else:
      strings_to_try = [' '+iflen_min+'mm', ' '+iflen_min+' mm', ' '+iflen_min+' ']
      # if debug: print('Try to match focal length:',strings_to_try)
      for istr in strings_to_try:
        if istr in text:
          matches.append(ilens)
          # if debug: cprint(f"Found a match for '{istr}' in '{text}'.")

  if len(matches)==0:
    if debug: cprint(f"SKIP:: Could not find a match with brand set to {brand}",'yellow')
  elif len(matches)==1: 
    matched_lens_idx = matches[0]
    if debug: cprint(f"KEEP:: Matching only FLEN to '{slim_df['lens_id'].iloc[ilens]}'", 'yellow')
  else:
    if debug: cprint(f"ATTN:: Found multiple FLEN matches:\n{[slim_df['lens_id'].iloc[x] for x in matches]}", 'yellow')
    aperture_matches = []
    for idx in matches:
      if debug: cprint(f"----> Considering match to '{slim_df['lens_id'].iloc[idx]}'", 'blue')
      if_min = get_str(slim_df['f_min'].iloc[idx])
      strings_to_try = ['f'+if_min, 'f/'+if_min, 'f '+if_min, '/'+if_min, ' '+if_min+' ']
      # if debug: print('Try to match aperture:',strings_to_try)
      for istr in strings_to_try:
        if istr in text:
          aperture_matches.append(idx)
          if debug: print(f"Found a potential match: '{slim_df['lens_id'].iloc[idx]}'")

    if len(aperture_matches)>1:
      if debug: cprint(f"DROP:: Found multiple matches:\n{[slim_df['lens_id'].iloc[x] for x in aperture_matches]}", 'red')
    elif len(aperture_matches)==1:
      matched_lens_idx = aperture_matches[0]
      if debug: cprint(f"KEEP:: Matched to lens_id '{slim_df['lens_id'].iloc[ilens]}'", 'green')
    else: # save even if only matched focal length and not aperture
      if debug: cprint(f"DROP:: Found no matches for aperture.", 'red')

  return matched_lens_idx

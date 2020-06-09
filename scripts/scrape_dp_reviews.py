#! /usr/bin/env python3
import requests
from bs4 import BeautifulSoup

from termcolor import cprint
import time, random, sys, os
import re
import csv

from collections import namedtuple
thread = namedtuple('thread','date forum href')
post = namedtuple('post','date user user_nposts body')

headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:76.0) Gecko/20100101 Firefox/76.0', 
          'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
session = requests.Session()

def get_thread_list(bs_search_results):
  thread_list = []
  recent = True
  try:
    posts = bs_search_results.find_all('div',{'class':'subject'})
    dates = bs_search_results.find_all('div',{'class':'infoLine'})
    for i,__ in enumerate(posts):
      forum = dates[i].a.contents[0]
      date = dates[i].contents[2].split(',')[1]
      if int(date) < 2015:
          recent = False
          break
      # go to actual post
      html = session.get(posts[i].a['href'], headers=headers)
      bs_post = BeautifulSoup(html.text,'html.parser')
      # get href from "Flatten view" to get to the full thread
      href = bs_post.find('a',{'id':'forumsSwitchToFlatViewBottom'})['href'].split('#forum-post')[0]
      # print('Found thread:',href)
      thread_list.append(thread(date=date, forum=forum, href=href))
  except Exception as e:
    cprint(f'Encountered exception while parsing search result to find threads. Skip.\n{e}','red')
    raise
  return (recent, thread_list)

def get_posts_info(thread_href):
  posts = []
  thread_href += '?page='
  next_page_exists,ipage = True, 0
  thread_title = ''
  while next_page_exists:
    ipage +=1
    print(f'Reading {ipage}')
    try: 
      html = session.get(thread_href+str(ipage), headers=headers) 
      bs_thread = BeautifulSoup(html.text, 'html.parser')
      if ipage==1:
        thread_title = bs_thread.find('h1').contents[0].strip()
      if bs_thread.find('td',{'class':'next enabled'}) is None:
        next_page_exists = False
    except Exception as e:
      cprint(f'Encountered exception while reading {ipage} page of posts. Skip.\n{e}','red')
      raise

    try:
      bs_posts = bs_thread.find_all('div',{'class':'postBody'})
    except Exception as e:
      cprint(f'Encountered exception while parsing thread to find posts. Skip.\n{e}','red')
      raise
      return posts

    for bs_post in bs_posts:
      try:
        date = bs_post.find('div',{'class':'metadata'}).span['title'].split('at')[0].strip()
        user = bs_post.find('a',{'class':'profileLink userName'})
        if user is None:
          user = 'unknown' #bs_post.find('span',{'class':'unknownMember userName'})
        else: 
          user = user.contents[0]
        user_nposts = bs_post.find('div',{'class':'userInfo'}).contents[-1].split('Posts:')[1].strip()
        body = bs_post.find('div',{'class':'postBodyText hasBottomSection body'})
        if body is None:
          body = bs_post.find('div',{'class':'postBodyText body'})
        if body.p is None:
          cprint(f'No body found in post by {user}. Skip.','red')
          continue
        body = body.p.contents[0]
        # print(date, user, user_nposts, body)
        posts.append(post(date=date, user=user, user_nposts=user_nposts, body=body))
      except Exception as e:
        cprint(f'Encountered exception while parsing post. Skip.\n{e}','red')
        raise
        continue
  return thread_title, posts

def save_reviews(activity):
  search_url = f'https://www.dpreview.com/search/forums?query=lens%20{activity}&only-threads=yes&only-titles=yes'
  try:
    html = session.get(search_url, headers=headers) 
    bs_search_results = BeautifulSoup(html.text, 'html.parser')
  
    nthreads = 0
    next_page_exists,ipage = True, 0
    while next_page_exists and nthreads < 100:
      ipage +=1
      try: # we got the first page already
        search_url = f'https://www.dpreview.com/search/forums?query=lens%20{activity}&page={ipage}&only-threads=yes&only-titles=yes'
        html = session.get(search_url, headers=headers) 
        bs_search_results = BeautifulSoup(html.text, 'html.parser')
        if bs_search_results.find('td',{'class':'next enabled'}) is None:
          next_page_exists = False
      except Exception as e:
        cprint(f'Encountered exception while getting next page. Skip.\n{e}','red')
        break

      recent, thread_list = get_thread_list(bs_search_results)
      for thread in thread_list:
        nthreads += 1
        thread_id = thread.href.split('/')[-1]
        posts_filename = f"{os.environ.get('RAW_HTML')}/dprev/{activity.replace('%20','_')}_thread_{thread_id}.csv"
        if os.path.exists(posts_filename):
          cprint(f'Thread #{thread_id} already processed. Skip.','blue')
          continue
        else:
          cprint(f'Reading posts from thread #{(nthreads)} with id #{thread_id}','blue')

        # write info about all posts in each thread
        posts_file = open(posts_filename,'w')
        posts_writer = csv.writer(posts_file)
        posts_writer.writerow(('thread_forum', 'thread_title', 'post_date', 'user','user_nposts','post_body'))
        thread_title, posts = get_posts_info(thread.href)
        for post in posts:
          posts_writer.writerow((thread.forum, thread_title, post.date, post.user, post.user_nposts, post.body))
        posts_file.close()
        time.sleep(0.5*random.uniform(0,1))

      if not recent: # no more recent threads left to read
        break

  except Exception as e:
    cprint(f'Encountered exception while searching for {activity}. Skip.\n{e}','red')
    raise
  return

if __name__ == "__main__":
  activities = {'landscape','wildlife','portraits',f'low%20light'}
  for activity in activities:
    cprint(f'***************** Collecting reviews for {activity} **************************','green')
    save_reviews(activity)
    time.sleep(random.uniform(0,1))

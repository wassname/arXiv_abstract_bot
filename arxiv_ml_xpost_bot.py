import praw
import logging
import requests
import bs4
import html2text
import time, os
import shelve
import re
from prawcore import NotFound
import datetime


from botlib import get_bot, get_logger

logger = get_logger()

# from https://github.com/arxiv-vanity/arxiv-vanity/blob/master/arxiv_vanity/scraper/arxiv_ids.py
ARXIV_ID_PATTERN = r'([a-z\-]+(?:\.[A-Z]{2})?/\d{7}|\d+\.\d+)(v\d+)?'
ARXIV_URL_RE = re.compile(r'arxiv.org/[^\/]+/({})(\.pdf)?'.format(ARXIV_ID_PATTERN), re.I)
OPENREVIEW_URL_RE = re.compile(r'openreview.net/', re.I)
# OPENREVIEW_URL_RE = re.compile(r'distill.pub/./', re.I)

r = get_bot()

# source subreddits
subreddits = [
    r.subreddit('machinelearning'),
    r.subreddit('reinforcementlearning'),
    r.subreddit('LanguageTechnology')
]
# target_subreddit = r.subreddit('mlresearch')
# target_subreddit = r.subreddit('testingground4bots')

SLEEP = 60*10
LIMIT_CHECK = 120
MIN_SECONDS = 60 * 60
MIN_SCORE = 5


if r.read_only == False:
    print("Connected and running.")


def comment():
    with shelve.open('.arxiv_bot') as cache:
        for j, subreddit in enumerate(subreddits):
            try:
                all_posts = subreddit.new(limit=LIMIT_CHECK)
                for i, post in enumerate(all_posts):
                    match = ARXIV_URL_RE.search(post.url) or OPENREVIEW_URL_RE.search(post.url)
                    
                    ts = time.time() - post.created_utc
                    if match and (post.score > MIN_SCORE) and (ts > MIN_SECONDS):

                        if cache.get(post.id) and cache.get(post.id) is 'T':
                            print(j, i, "Parsed this post already: %s. %s. %s" % (post.permalink, post.id, post.url))
                            continue
                        else:
                            print(j, i, "posting", post, post.url, post.permalink, post.id, post.score, ts)
                            post.crosspost('researchml')
                            # xpost(['r/researchml'], post)
                            cache[post.id] = 'T'
                            time.sleep(60)
                    time.sleep(1)
            except Exception as error:
                logger.error("Failed to scrape")
                print(error)


if __name__ == "__main__":

    while True:
        comment()
        time.sleep(SLEEP)

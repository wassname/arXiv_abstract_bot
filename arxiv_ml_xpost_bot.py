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
# OPENREVIEW_URL_RE = re.compile(r'openreview.net/./', re.I)
# OPENREVIEW_URL_RE = re.compile(r'distill.pub/./', re.I)

r = get_bot()

# source subreddits
subreddits = [
    r.subreddit('machinelearning'),
    # r.subreddit('reinforcementlearning')
    # r.subreddit('LanguageTechnology')
]
# target_subreddit = r.subreddit('mlresearch')
# target_subreddit = r.subreddit('testingground4bots')

SLEEP = 600
LIMIT_CHECK=20


if r.read_only == False:
    print("Connected and running.")


def comment():
    with shelve.open('.arxiv_bot') as cache:
        for subreddit in subreddits:
            try:
                all_posts = subreddit.new(limit=LIMIT_CHECK)
                for post in all_posts:
                    match = ARXIV_URL_RE.search(post.url)
                    if match:
                        arxiv_id = match.group(1)

                        # crosspost
                        print('found', arxiv_id)
                        

                        if cache.get(post.id) and cache.get(post.id) is 'T':
                            print ("Parsed this post already: %s"%(post.permalink))
                            continue
                        else:
                            xpost(['r/researchml'], post)
                            cache[post.id]='T'
                            time.sleep(10)
            except Exception as error:
                logger.error("Failed to scrape")
                print(error)

def xpost(subs, originalpost):
    # originalpost = where.submission
    newtitle = "(X-Post r/" + str(originalpost.subreddit.display_name) + ") " + originalpost.title
    print("New post: " + str(newtitle))
    link = "https://www.reddit.com" + str(originalpost.permalink)
    workedsubs = []
    failedsubs = []
    wasError = False
    for workingsub in subs:
        exists = True
        try:
            r.subreddits.search_by_name(workingsub[2:], exact=True)
        except NotFound:
            logging.error("Failed to post")
            exists = False
        if exists == True:
            subreddit = r.subreddit(workingsub[2:])
            try:
                subreddit.submit(newtitle, url=link, resubmit=True, send_replies=False)
                workedsubs.append(str(workingsub))
                print("Posting: " + str(newtitle) + " to " + str(workingsub))
            except praw.exceptions.APIException:
                logging.error("Failed to post")
                wasError = True
                break
        else:
            failedsubs.append(str(workingsub))
    if not wasError:
        print(workedsubs,failedsubs)
        # reply(workedsubs,failedsubs,where)
        pass
    else:
        response = ""
        if workedsubs:
            response = "I was able to crosspost in "
            for i in workedsubs:
                response = response + str(i) + " and "
            response = response[:-5] + ", but I was rate-limited on the others."
            print(response)
        else:
            response = "Sorry, I was rate-limited, and I couldn't post."
            print(response)
        # where.reply(str(response) + " Make sure to give me karma to prevent that in the future.")




if __name__ == "__main__":

    while True:
        comment()
        time.sleep(SLEEP)

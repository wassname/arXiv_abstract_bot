"""
Posts new shortscience.org summaries to researchml
"""
import praw
import os
import time
import datetime
import pytz
import feedparser
import logging
import shelve
from time import mktime
from botlib import get_bot, get_logger

logger = get_logger()

r = get_bot()

SUBREDDIT = 'researchml'  # 'testingground4bots'
SLEEP = 600
MAX_AGE_DAYS = 1
POST_DESCRIPTION = True
DESCRIPTION_FORMAT = "{}"

# main procedure

sources = ["https://distill.pub/rss.xml", "https://www.shortscience.org/rss.xml"]

def run_bot(sources):
    with shelve.open('.rss_bot') as cache:
        sub = r.subreddit(SUBREDDIT)
        t0 = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(days=MAX_AGE_DAYS) 

        logger.info("Start bot for subreddit %s", SUBREDDIT)
        while True:
            try:
                logger.info("check sources")
                newArticles = []
                for source in sources:
                    d = feedparser.parse(source)
                    newArticles = d['entries']
                        
                    for article in newArticles:
                        dt = datetime.datetime.fromtimestamp(mktime(article['published_parsed'])).replace(tzinfo=pytz.utc)
                        url = id = article['link']
                        desc = article['summary']
                        title= article['title']

                        if dt < t0:
                            # skip older ones
                            logger.debug(f"skipping older article '{title}', id='{id}' td={dt-t0}")
                            continue
                        
                        if cache.get(id) and cache.get(id) is 'T':
                            logger.info(f"skipping done article '{title}', id='{id}'")
                            continue
                        else:
                            logger.info('posting %s', id)
                            try:
                                submission = sub.submit('[S] ' + title, url=url, resubmit=True, send_replies=False)
                                if POST_DESCRIPTION and desc is not None:
                                    submission.reply(DESCRIPTION_FORMAT.format(desc))
                            except praw.exceptions.PRAWException as e:
                                logger.exception("could not submit %s", e)
                            else:
                                cache[id] ='T'
                                logger.info("submit article %s", article)

            # Allows the bot to exit on ^C, all other exceptions are ignored
            except KeyboardInterrupt:
                return 0
                break
            except Exception as e:
                logger.error("Exception %s", e, exc_info=True)

            logger.info("sleep for %s s", SLEEP)
            time.sleep(SLEEP)

    # write_config_done(done)


if __name__ == "__main__":
    run_bot(sources)

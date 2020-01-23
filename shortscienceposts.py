"""
Posts new shortscience.org summaries to researchml
"""
import praw
import os
import time
import datetime
import pytz
import RSSReader
import logging

from bot import get_bot, get_memcache_client

# https://github.com/SmBe19/RedditBots/blob/master/RSSBot/RSSBot.py
log = logging


r = get_bot()
cache = get_memcache_client()

SUBREDDIT = 'researchml'  # 'testingground4bots'
SLEEP = 60
POST_DESCRIPTION = True
DESCRIPTION_FORMAT = "{}"

# main procedure
def run_bot():
    sub = r.subreddit(SUBREDDIT)
    t0 = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(days=0) 

    log.info("Start bot for subreddit %s", SUBREDDIT)
    while True:
        sources = ["https://www.shortscience.org/rss.xml"]
        try:
            log.info("check sources")
            newArticles = []
            for source in sources:
                newArticles.extend(RSSReader.get_new_articles(source))

            for article in newArticles:
                title, url, desc, id, dt = article

                if dt < t0:
                    # skip older ones
                    # print(f"skipping older article {title}, {id} {dt-t0}")
                    continue
                
                if cache.get(id) and cache.get(id) is 'T':
                    # print(f"skipping done article {title}, {id}")
                    continue
                else:
                    cache.set(id, 'T')
                    print('posting', id)
                    try:
                        # submission = sub.submit(title, url=url, resubmit=RESUBMIT_ANYWAYS, send_replies=False)
                        submission = sub.submit('[S] ' + title, url=url, resubmit=True, send_replies=False)
                        if POST_DESCRIPTION and desc is not None:
                            submission.reply(DESCRIPTION_FORMAT.format(desc))
                    except praw.exceptions.PRAWException as e:
                        log.error("could not submit %s", e)
                    else:
                        log.info("submit article %s", article)

        # Allows the bot to exit on ^C, all other exceptions are ignored
        except KeyboardInterrupt:
            return 0
            break
        except Exception as e:
            log.error("Exception %s", e, exc_info=True)

        # write_config_done(done)
        log.info("sleep for %s s", SLEEP)
        time.sleep(SLEEP)

    # write_config_done(done)


if __name__ == "__main__":
    run_bot()

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
MIN_AGE_DAYS = 2
MAX_AGE_DAYS = 30
POST_DESCRIPTION = True
DESCRIPTION_FORMAT = "{}"

# main procedure

sources = ["https://www.shortscience.org/rss.xml"]#, "https://distill.pub/rss.xml", ]
# TODO might be nice to check shortscience votes 'shortscience:votes'

# note this is what the entries look like
# {'title': 'Visualizing Neural Networks with the Grand Tour', 'title_detail': {'type': 'text/plain', 'language': None, 'base': 'https://distill.pub/rss.xml', 'value': 'Visualizing Neural Networks with the Grand Tour'}, 'links': [{'rel': 'alternate', 'type': 'text/html', 'href': 'https://distill.pub/2020/grand-tour'}], 'link': 'https://distill.pub/2020/grand-tour', 'summary': 'By focusing on linear dimensionality reduction, we show how to visualize many dynamic phenomena in neural networks.', 'summary_detail': {'type': 'text/html', 'language': None, 'base': 'https://distill.pub/rss.xml', 'value': 'By focusing on linear dimensionality reduction, we show how to visualize many dynamic phenomena in neural networks.'}, 'id': 'https://distill.pub/2020/grand-tour', 'guidislink': False, 'published': 'Mon, 16 Mar 2020 20:0:0 Z', 'published_parsed': time.struct_time(tm_year=2020, tm_mon=3, tm_mday=16, tm_hour=20, tm_min=0, tm_sec=0, tm_wday=0, tm_yday=76, tm_isdst=0)}

# {'shortscience_arxivid': '1708.09259', 'shortscience_bibtexkey': 'journals/corr/1708.09259', 'shortscience_votes': '2', 'title': 'Efficient Convolutional Network Learning using Parametric Log based Dual-Tree Wavelet ScatterNet', 'title_detail': {'type': 'text/plain', 'language': None, 'base': 'https://www.shortscience.org/rss.xml', 'value': 'Efficient Convolutional Network Learning using Parametric Log based Dual-Tree Wavelet ScatterNet'}, 'authors': [{'name': 'hanoch kremer'}], 'author': 'hanoch kremer', 'author_detail': {'name': 'hanoch kremer'}, 'summary': "ScatterNets incorporates geometric knowledge of images to produce discriminative and invariant (translation and rotation) features i.e. edge information. The same outcome as CNN's first layers hold. So why not replace that first layer/s with an equivalent, fixed, structure and let the optimizer find the best weights for the CNN with its leading-edge removed.\nThe main motivations of the idea of replacing the first convolutional, ReLU and pooling layers of the CNN with a two-layer parametric log-b...", 'summary_detail': {'type': 'text/html', 'language': None, 'base': 'https://www.shortscience.org/rss.xml', 'value': "ScatterNets incorporates geometric knowledge of images to produce discriminative and invariant (translation and rotation) features i.e. edge information. The same outcome as CNN's first layers hold. So why not replace that first layer/s with an equivalent, fixed, structure and let the optimizer find the best weights for the CNN with its leading-edge removed.\nThe main motivations of the idea of replacing the first convolutional, ReLU and pooling layers of the CNN with a two-layer parametric log-b..."}, 'links': [{'rel': 'alternate', 'type': 'text/html', 'href': 'http://www.shortscience.org/paper?bibtexKey=journals/corr/1708.09259#hanochkremer'}], 'link': 'http://www.shortscience.org/paper?bibtexKey=journals/corr/1708.09259#hanochkremer', 'id': 'http://www.shortscience.org/paper?bibtexKey=journals/corr/1708.09259#hanochkremer', 'guidislink': False, 'published': 'Thu, 09 Apr 2020 12:05:38 +0000', 'published_parsed': time.struct_time(tm_year=2020, tm_mon=4, tm_mday=9, tm_hour=12, tm_min=5, tm_sec=38, tm_wday=3, tm_yday=100, tm_isdst=0)}



def run_bot(sources):
    with shelve.open('.rss_bot') as cache:
        sub = r.subreddit(SUBREDDIT)
        t0 = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(days=MAX_AGE_DAYS)
        t1 = datetime.datetime.utcnow().replace(tzinfo=pytz.utc) - datetime.timedelta(days=MIN_AGE_DAYS) 

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
                        title = article['title']
                        votes = int(article.get('shortscience_votes', 99))

                        if votes < 2:
                            logger.debug(f"skipping low votes article '{title}', id='{id}' td={dt-t0}, votes={votes}")
                            continue

                        if (dt > t0) and (dt < t1):
                            # skip older ones and new ones (that way we miss bugs that are removed from rss feed within a day)
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
            # except Exception as e:
            #     logger.error("Exception %s", e, exc_info=True)

            logger.info("sleep for %s s", SLEEP)
            time.sleep(SLEEP)

    # write_config_done(done)


if __name__ == "__main__":
    run_bot(sources)

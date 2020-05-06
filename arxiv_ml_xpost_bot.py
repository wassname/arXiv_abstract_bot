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
ARXIV_ID_PATTERN = r"([a-z\-]+(?:\.[A-Z]{2})?/\d{7}|\d+\.\d+)(v\d+)?"
ARXIV_URL_RE = re.compile(
    r"arxiv.org/[^\/]+/({})(\.pdf)?".format(ARXIV_ID_PATTERN), re.I
)
OPENREVIEW_URL_RE = re.compile(r"openreview.net/", re.I)
# OPENREVIEW_URL_RE = re.compile(r'distill.pub/./', re.I)

r = get_bot()

# source subreddits
subreddits = [
    r.subreddit("machinelearning"),
    r.subreddit("reinforcementlearning"),
    r.subreddit("LanguageTechnology"),
]
# target_subreddit = r.subreddit('mlresearch')
# target_subreddit = r.subreddit('testingground4bots')

SLEEP = 60 * 10
LIMIT_CHECK = 20
MIN_SECONDS = 3 * 60 * 60
MIN_SCORE = 5


if r.read_only == False:
    logger.info("Connected and running.")


def comment():
    with shelve.open(".arxiv_bot") as cache:
        for j, subreddit in enumerate(subreddits):
            try:
                all_posts = subreddit.new(limit=LIMIT_CHECK)
                for i, post in enumerate(all_posts):
                    match = ARXIV_URL_RE.search(post.url) or OPENREVIEW_URL_RE.search(
                        post.url
                    )

                    ts = time.time() - post.created_utc
                    logger.debug(
                        "%s %s %s, match %s, score %s>%s, age %s>%s, url %s",
                        j,
                        i,
                        subreddit,
                        bool(match),
                        post.score,
                        MIN_SCORE,
                        int(ts),
                        MIN_SECONDS,
                        post.url,
                    )
                    if match and (post.score > MIN_SCORE) and (ts > MIN_SECONDS):

                        if cache.get(post.id) is "T":
                            logger.debug(
                                "%s %s. Parsed this post already: %s. %s. %s"
                                % (j, i, post.permalink, post.id, post.url)
                            )
                            continue
                        elif cache.get(post.url) is "T":
                            # avoid situations where the same url is in multiple subreddits
                            logger.debug(
                                "%s %s .Parsed this url already: %s. %s. %s"
                                % (j, i, post.permalink, post.id, post.url)
                            )
                            continue
                        else:
                            logger.info(
                                "%s %s. Posting %s %s %s %s %s %s",
                                j,
                                i,
                                post,
                                post.url,
                                post.permalink,
                                post.id,
                                post.score,
                                ts,
                            )
                            post.crosspost("ResearchML")
                            cache[post.id] = "T"
                            cache[post.url] = "T"
                            time.sleep(60)
                    time.sleep(0.1)
            except Exception as error:
                logger.error(f"Failed to scrape {error} {subreddit}")
                logger.exception(error)


if __name__ == "__main__":

    while True:
        comment()
        logger.debug("Sleeping for %s", SLEEP)
        time.sleep(SLEEP)

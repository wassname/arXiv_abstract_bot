import praw
import logging
import requests
import bs4
import html2text
import time, os
import bmemcached
import re
from prawcore import NotFound
import datetime


from botlib import get_bot, get_memcache_client, get_logger

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
target_subreddit = r.subreddit('mlresearch')
target_subreddit = r.subreddit('testingground4bots')


if r.read_only == False:
    print("Connected and running.")
# alreadydone = set()


# def scrape_arxiv(arxiv_id):
#     url = 'https://arxiv.org/abs/{}'.format(arxiv_id)
#     r = requests.get(url)
#     soup = bs4.BeautifulSoup(r.text)
#     abstract = soup.select('.abstract')[0]
#     abstract = html2text.html2text(abstract.decode()).replace('\n', ' ')

#     authors = soup.select('.authors')[0]
#     authors = html2text.html2text(authors.decode()).replace('\n', ' ')
#     authors = authors.replace('(/', '(http://arxiv.org/')

#     title = soup.select('.title')[0]
#     title =  html2text.html2text(title.decode()).replace('\n', ' ')[2:]

#     abs_link = u'[Landing Page]({})'.format(url)
#     pdf_link = u'[PDF Link](https://arxiv.org/pdf/{})'.format(arxiv_id)
#     web_link = u'[Read as web page on arXiv Vanity](https://www.arxiv-vanity.com/papers/{}/)'.format(arxiv_id)
#     links = u'{} | {} | {}'.format(pdf_link, abs_link, web_link)
#     response = '\n\n'.join([title, authors, abstract, links]) 
#     return response


def comment(cache):
    # print(time.asctime(), "searching")
    for subreddit in subreddits:
        try:
            all_posts = subreddit.new(limit=100)
            for post in all_posts:
                match = ARXIV_URL_RE.search(post.url)
                if match:
                    arxiv_id = match.group(1)

                    # crosspost
                    print('found', arxiv_id)
                    

                    if cache.get(post.id) and cache.get(post.id) is 'T':
                        print ("Parsed this post already: %s"%(post.permalink))
                        continue
                    # for comment in post.comments:
                    #     if str(comment.author) == 'arXiv_abstract_bot':
                    #         break
                    else:
                        xpost(['r/researchml'], post)
                        # response = scrape_arxiv(arxiv_id)
                        # post.reply(response)
                        cache.set(post.id, 'T')
                    #     print "Parsed post: %s"%(post.permalink)
                    #     print(arxiv_id, response)
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
    cache = get_memcache_client()

    while True:
        comment(cache)
        time.sleep(30)

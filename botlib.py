import praw
import logging
import requests
import bs4
import html2text
import time, os
import bmemcached
import re
from prawcore import NotFound

import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def get_logger():
    logger = logging.getLogger(__name__)
    return logger

def get_memcache_client():
    # Store IDs of comments that the bot has already replied to.
    # Read local cache by default

    MEMCACHEDCLOUD_SERVERS = os.environ.get('MEMCACHEDCLOUD_SERVERS')
    MEMCACHEDCLOUD_USERNAME = os.environ.get('MEMCACHEDCLOUD_USERNAME')
    MEMCACHEDCLOUD_PASSWORD = os.environ.get('MEMCACHEDCLOUD_PASSWORD')

    client = bmemcached.Client((MEMCACHEDCLOUD_SERVERS,), MEMCACHEDCLOUD_USERNAME,
                           MEMCACHEDCLOUD_PASSWORD)
    return client
    

def get_bot():
    PRAW_CLIENT_ID = os.environ.get('PRAW_CLIENT_ID')
    PRAW_CLIENT_SECRET = os.environ.get('PRAW_CLIENT_SECRET')
    PRAW_PASSWORD = os.environ.get('PRAW_PASSWORD')
    PRAW_USERNAME = os.environ.get('PRAW_USERNAME')
    PRAW_USERAGENT = os.environ.get('PRAW_USERAGENT')
    return praw.Reddit(
        username=PRAW_USERNAME,
        password=PRAW_PASSWORD,
        client_id=PRAW_CLIENT_ID,
        client_secret=PRAW_CLIENT_SECRET,
        user_agent=PRAW_USERAGENT
        )

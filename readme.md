I would like to autocrosspost
- [x] arxiv from r/machinelearning
- [x] shortscience summaries from shortscience rss feed
- [ ] openreview
- [ ] openai, googlemin, facebookai, deepmind blogposts


# start

```sh
pyenv activate jup3.7.2
#memcached?
#https://github.com/jaysonsantos/python-binary-memcached
source ./vars.sh
python ./arxiv_ml_xpost_bot.py &
python ./rss_poster_bot.py &
```

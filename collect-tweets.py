import json
import os

import tweepy
from tweepy import Tweet
from text import clean_text
from kutiguse import ngram, tokenize

client = tweepy.Client(os.environ['BEARER_TOKEN'])


def collect_tweet_from_topic(topic: str):
    res = client.search_recent_tweets(
        query=f'{topic} -is:retweet -has:hashtags lang:ja -has:links -has:media -is:reply',
        expansions='author_id',
    )
    for t in res.data:
        tweet: Tweet = t
        ngram_list = []
        text = clean_text(tweet.text)
        tokens = tokenize(text)
        for i in range(1, 5):
            ngram_list.append(ngram(tokens, i))
        out = {
            "author_id": tweet.author_id,
            "topic": topic,
            "ngram_list": ngram_list
        }
        filepath = os.path.join("data", f'{tweet.author_id}.txt')

        try:
            with open(filepath, mode='r') as f:
                saved_list: list = json.loads(f.read())
        except FileNotFoundError:
            saved_list = []

        saved_list.append(out)

        with open(filepath, mode='w') as f:
            f.write(json.dumps(saved_list, ensure_ascii=False))


if __name__ == '__main__':
    for topic in ['寿司', '公式', '感動']:
        collect_tweet_from_topic(topic)

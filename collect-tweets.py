import os
import re

import tweepy
from tweepy import Tweet

client = tweepy.Client(os.environ['BEARER_TOKEN'])
res = client.search_recent_tweets(query="ワールドカップ -is:retweet -has:hashtags lang:ja -has:links -has:media -is:reply",
                                  expansions='author_id',
                                  )


# from: https://gist.github.com/n1n9-jp/5857d7725f3b14cbc8ec3e878e4307ce
def remove_emoji(string):
    emoji_pattern = re.compile("["
                               u"\U00002700-\U000027BF"  # Dingbats
                               u"\U0001F600-\U0001F64F"  # Emoticons
                               u"\U00002600-\U000026FF"  # Miscellaneous Symbols
                               u"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols And Pictographs
                               u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
                               u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
                               u"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'。', string)


def clean_text(text: str) -> str:
    special_character_pattern = re.compile('["#$%&\'\\\\()*+-/:;<=>@[\\]^_`{|}~「」〔〕“”〈〉『』【】＆＊・（）＄＃＠｀＋￥％]')
    cleaned_text = special_character_pattern.sub(r'', text)
    cleaned_text = remove_emoji(cleaned_text)

    cleaned_text = cleaned_text.replace("\n", "")
    cleaned_text = cleaned_text.replace(r'((。|．)\s*)+', "。")
    cleaned_text = cleaned_text.replace(r'((、|,)\s*)+', "、")
    cleaned_text = cleaned_text.replace(r'((…|‥)\s*)', "。")
    cleaned_text = cleaned_text.replace(r'((？|?)\s*)', "？")
    cleaned_text = cleaned_text.replace(r'((！|!)\s*)', "。")

    return cleaned_text


for t in res.data:
    tweet: Tweet = t

    print(str(tweet.author_id) + " " + clean_text(tweet.text))

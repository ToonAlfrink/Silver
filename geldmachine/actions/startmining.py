import tweepy
import json
import re
from geldmachine.models import Word
from datetime import date

class Miner(object):
    def __init__(self, optionsfile, authfile):
        self._getstream(authfile)
        self._parseoptions(optionsfile)
        self._processor = Processor()
        self.i = 0

    def _getstream(self, authfile):
        auth = [l.strip() for l in open(authfile).readlines()]
        auth_handler = tweepy.OAuthHandler(auth[0], auth[1])
        auth_handler.set_access_token(auth[2], auth[3])
        listener = StreamListener(self)
        self.stream = tweepy.Stream(auth_handler, listener)

    def _parseoptions(self, optionsfile):
        data = json.load(open(optionsfile, 'r'))
        endpoint = data['endpoint']
        self.options = data[endpoint]
        
    def run(self):
        from time import sleep
        while True:
            try:
                self.stream.filter(**self.options)
            except Exception as e:
                sleep(5)

    def on_status(self, tweet):
        self.i += 1
        self._processor.addtweet(tweet.text)
        if self.i % 10000 == 0:
            self._processor.save()

    def on_error(self, status_code):
        print(status_code)

class StreamListener(tweepy.StreamListener):
    def __init__(self, callback, *args, **kwargs):
        super(StreamListener, self).__init__(*args, **kwargs)
        self.callback = callback #class that handles results

    def on_status(self, tweet):
        self.callback.on_status(tweet)

    def on_error(self, status_code):
        self.callback.on_error(status_code)


positive_patterns = [r"(i'?m( feeling)?|i am( feeling)?|i feel|makes me)( kinda)? (\w+)"]

negative_patterns = [r"(i'm|i am) not (\w+)",
                     r"i don't feel (\w+)",
                     r"doesn't make me (\w+)",
                     r"im not (\w+)",
                     r"i am not feeling (\w+)",
                     r"im not feeling (\w+)",
                     r"i'm not feeling (\w+)",]

from collections import Counter
from nltk import word_tokenize, pos_tag

class Processor(object):
    def __init__(self):
        self.states = Counter()

    def addtweet(self, text):
        text = text.lower()
        tags = dict(pos_tag(word_tokenize(text)))
        for p in positive_patterns:
            match = re.search(p, text)
            if match and match.groups()[-1]:                
                word = match.groups()[-1]
                if tags.get(word) == "JJ":
                    self.states[word] += 1
        for p in negative_patterns:
            match = re.search(p, text)
            if match and match.groups()[-1]:
                word = match.groups()[-1]
                if tags.get(word) == "JJ":
                    self.states["-"+word] += 1

    def save(self):
        print(self.states)
        for word, count in self.states.items():
            w_model = Word.objects.get_or_create(word = word, date = date.today(),defaults={'count':0})[0]
            w_model.count += count
            w_model.save()
        self.states = Counter()

if __name__ == "__main__":
    from sys import argv
    if not len(argv) == 3:
        print("please provide an options (json) file and an auth (txt) file")
    else:
        Miner(argv[1], argv[2]).run()

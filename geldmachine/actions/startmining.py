import tweepy
import json
import re
from geldmachine.models import Word

class Miner:
    def __init__(self, authfile, optionsfile):
        self._getstream(authfile)
        self._parseoptions(optionsfile)
        self._wordmanager = WordManager()
        self.i = 0

    def _getstream(self, authfile):
        auth = [l.strip() for l in open(authfile).readlines()]
        auth_handler = tweepy.OAuthHandler(auth[0], auth[1])
        auth_handler.set_access_token(auth[2], auth[3])
        listener = StreamListener(self)
        self.stream = tweepy.Stream(auth_handler, listener)

    def _parseoptions(self, optionsfile):
        data = json.load(open(optionsfile))
        endpoint = data['endpoint']
        self.options = data[endpoint]
        
    def run(self):
        print(self.options)
        self.stream.filter(**self.options)

    def on_status(self, tweet):
        self.i += 1
        self._wordmanager.addline(tweet.text, tweet.created_at.date())
        if self.i % 1000 == 0:
            self._wordmanager.save()


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

class WordManager:
    _words = {}
    def addline(self, line, date):
        words = [w.lower() for w in re.findall("[\w]+", line)]        
        for w in words:
            self.add(w, date)

    def add(self, word, date):
        if (word, date) in self._words.keys():
            self._words[(word, date)] += 1
        else:
            self._words[(word, date)] = 1
    
    def _tuples(self):
        return [(v, k[0], k[1]) for k, v in self._words.items()]

    def top100(self):
        return list(sorted(self._tuples()))[:100]

    def save(self):
        tuples = self._tuples()
        print("saving {n} words".format(n = len(tuples)))
        for count, word, date in tuples:
            w, created = Word.objects.get_or_create(word = word, date = date, defaults = {'count':0})
            if created:
                w.count = 0
            else:
                w.count += count
            w.save()

        self._words = {}

if __name__ == "__main__":
    from sys import argv
    Miner(argv[1], argv[2]).run()

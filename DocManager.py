import os
import sys
import threading
import logging
from collections import defaultdict
import pickle

logging.basicConfig(level=logging.DEBUG, 
                    format='(%(threadName)-10s) %(message)s',)

class SingletonMixin(object):
    #https://gist.github.com/werediver/4396488
    __singleton_lock = threading.Lock()
    __singleton_instance = None

    @classmethod
    def instance(cls):
        if not cls.__singleton_instance:
            with cls.__singleton_lock:
                if not cls.__singleton_instance:
                    cls.__singleton_instance = cls()
        return cls.__singleton_instance

# The TDM already has all of this information
# so why have DocManager
class DocManager (SingletonMixin):
    def __init__(self):
        self.dm = defaultdict(list) #dict()
        
    def add(self, docName, tokenList):
        logging.debug("Adding %d tokens from %s" % (len(tokenList), docName))
        for t in tokenList:
            self.tdm.setdefault(t, []).append(docName)
        self.status = "Ready"

    def getStatus(self):
        return self.status
        
    def search(self, term):
        if term in self.tdm:
            return self.tdm[term]
        else:
            print ("Seach term [%s] not found" % term)
            return None

    def store(self):
        with open(self.tdmPickle, 'wb') as f:
            pickle.dump(self.tdmPickle, f, pickle.HIGHEST_PROTOCOL)
        logging.debug("Stored %d entries into %s" %(len(self.tdm), self.tdmPickle))

    def load(self):
        if os.path.isfile(self.tdmPickle):
            with open(self.tdmPickle, 'rb') as f:
                self.tdm = pickle.load(f)    
        logging.debug("Loaded %d entries from %s" %(len(self.tdm), self.tdmPickle))


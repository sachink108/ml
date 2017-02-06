import os
import sys
import threading
import logging
from collections import defaultdict
import pickle
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize
from TermDocumentMatrix import TDM
from DocManager import DocManager

nltk.data.path.append("G:\\nltk_data")
nltk.data.path.append("C:\\nltk_data")

logging.basicConfig(level=logging.DEBUG, 
                    format='(%(threadName)-10s) %(message)s',)

class TParser(threading.Thread):
    def __init__(self, docName, docContent):
        self.stopWords = set(stopwords.words('english'))
        self.ps = PorterStemmer()
        self.doc = docName
        self.docContent = docContent
        self.stemmed = defaultdict(int)
        self.thName = os.path.basename(self.doc)
        threading.Thread.__init__(self, group=None, target=None, name=self.thName)
        print ("Creating parser thread [%s] for doc %s" % (self.thName, self.doc))
        
    def run(self):
        self._parse()
        logging.debug("Trying to acquire tdm instance")
        tdm = TDM.instance()
        logging.debug("Got tdm instance %s" % tdm);
        tdm.add(self.stemmed, self.doc)
    
    def _parse(self):
        tokens = nltk.word_tokenize(self.docContent)
        logging.info("[%s] Total Tokens = %d" % (self.thName, len(tokens)))
        filtered = [w for w in tokens if not w in self.stopWords]
        logging.info("[%s] Filtered Tokens = %d" % (self.thName, len(filtered)))
        for w in filtered:
            self.stemmed[self.ps.stem(w)] += 1
        logging.info("[%s] Stemmed Tokens = %d" % (self.thName, len(self.stemmed)))
        dm = DocManager.instance()
        logging.debug("Got doc manager instance %s" % dm);
        
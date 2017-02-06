#!python
import sys
import argparse
import tornado.ioloop
import tornado.web
import tornado.websocket
import logging
import threading
from glob import glob
import threading

parser=argparse.ArgumentParser("Console backend")
parser.add_argument("--project-root", required=True)
parser.add_argument("--serverport", type=int, default=9000)
args=parser.parse_args()
logging.basicConfig(level=logging.INFO)
sys.path.append(args.project_root)

from TermDocumentMatrix import TDM
from TParser import TParser
from SearchHandler import *
from DocHandler import *
# /
class MainHandler(tornado.web.RequestHandler):
    def initialize(self, tdm):
        self._tdm=tdm

    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.write({'message':'Garble backend. GET /quit to quit. Other information being added'})

# what is the right thing to do?
# have a separate status handler or check for status 
# from the Search Handler. At scale this decision will have a serious impact
# because of how tornado handlers work (non-blocking)
# VS how we have designed the tdm.getStatus() call AND
# how often we call get status from the web page
class StatusHandler(tornado.web.RequestHandler):
    def initialize(self, tdm):
        self._tdm=tdm

    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.write({'message': self._tdm.getStatus()})

# -- start
logging.info("Garble web server starting up on port %d" % args.serverport)
logging.getLogger("requests").setLevel(logging.CRITICAL)

tdm = TDM.instance()
es =  Elasticsearch()
print ("Garble is ready\n")

application = tornado.web.Application([
    (r"/"                      , MainHandler, { 'tdm' : tdm})
   
    # DocHandler.py
   , (r"/getdoc/(.*)"           , DocHandler, {'tdm' : tdm, 'es' : es})
   , (r"/postdoc"               , DocHandler, {'tdm' : tdm, 'es' : es})

   # SearchHandler.py
    , (r"/status"              , SearchHandler, {'tdm' : tdm, 'es' : es})
    , (r"/search/(.*)"         , SearchHandler, {'tdm' : tdm, 'es' : es})
    , (r"/index/(.*)"          , IndexHandler, {'tdm':tdm})
    , (r"/quit"                , QuitHandler)
    , (r"/listeners/(.*)"      , ListenerHandler)
    , (r"/ws-stream/(.*)"      , WebSocketHandler, {"serverport":args.serverport})

])

application.listen(args.serverport)
tornado.ioloop.IOLoop.instance().start()

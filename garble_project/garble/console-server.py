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
print (sys.path)

from TermDocumentMatrix import TDM
from TParser import TParser
from SearchHandler import *
# /
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.write({'message':'Garble backend. GET /quit to quit. Other information being added'})

# -- start
logging.info("Garble web server starting up on port %d" % args.serverport)
logging.getLogger("requests").setLevel(logging.CRITICAL)

dataFolder = "G:\\SachinK\\progs\\search\\docs"
for doc in glob(dataFolder+ '\\*.txt'):
	p1 = TParser(doc)
	p1.start()
	
mainThread = threading.currentThread()
for t in threading.enumerate():
	if t is mainThread:
		continue
	t.join()

print ("Garble is ready\n")
application = tornado.web.Application([
    (r"/"                               , MainHandler)

    # SearchHandler.py
    , (r"/search"                       , SearchHandler)
	, (r"/index"                        , IndexHandler)
    , (r"/quit"                         , QuitHandler)

    , (r"/listeners/(.*)"               , ListenerHandler)
    , (r"/ws-stream/(.*)"               , WebSocketHandler, {"serverport":args.serverport})
])

application.listen(args.serverport)
tornado.ioloop.IOLoop.instance().start()

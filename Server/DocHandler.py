import os
import sys
import json
import time
import requests
import tornado.ioloop
import tornado.web
import tornado.websocket
import logging
import json
from TParser import TParser

class DocHandler(tornado.web.RequestHandler):
    def initialize(self, tdm):
        self._tdm = tdm
        self._es = es

    # used by  Garble when returning search result
    def get(self, request):
        self.set_header("Access-Control-Allow-Origin", "*")
        print ("GET %s" % request)
        file_content = open(request).read() 
        self.write({'file':'filename', 'filecontent': file_content})
    
    def post(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        data = json.loads(self.request.body.decode('utf-8'))
        dir = data['dir']
        filename = data['filename']
        content = data['content']
        self._es.

        #p1 = TParser(filename, content)
        #p1.start()
        #self.write({'status': 'queued doc' + filename})

#class DocStatHandler(tornado.web.RequestHandler):
#    def initialize(self):
#        pass
    
#    def get(self, request):
#        self.set_header("Access-Control-Allow-Origin", "*")
#        print ("GET %s" % request)
#        dm = DocManager.instance()
#        logging.debug("Got dm instance %s" % dm)
#        


import os
import sys
import json
import time
import requests
import tornado.ioloop
import tornado.web
import tornado.websocket
import logging

# /search        
class SearchHandler(tornado.web.RequestHandler):
    def initialize(self, tdm):
        self._tdm=tdm
        
    def get(self, request=None):
        self.set_header("Access-Control-Allow-Origin", "*")
        if (request is not None):
            print ("GET %s" % self.request.uri)
            print (request)
            
            searchResult = self._tdm.search(request)
            retobj = {'result' : searchResult}
        else:
            retobj = {'message' : self._tdm.getStatus()}
        self.write(retobj)

class IndexHandler(tornado.web.RequestHandler):
    def initialize(self, tdm):
        self._tdm=tdm

    def options(self, request):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE")
        self.write({'status':'success'})

    def delete(self, request):
        #self.request_manager.logger.info("DELETE /%s" % request)
        self.set_header("Access-Control-Allow-Origin", "*")

    def post(self, request):
        self.set_header("Access-Control-Allow-Origin", "*")
        print (request)
        # create a new parser here
        #p1 = TParser() # pass the document name here
        #p1.start() # this will start a new thread
        # where do we wait for it to complete?
        self.write({'status':status,'msg':'ok'})

    def get(self, query):
        self.set_header("Access-Control-Allow-Origin", "*")
        print ("GET /%s" % query)
        #(status, retmsg)=self.request_manager.getStatus()
        self.write({'status':'ok','info':'ok'})

class QuitHandler(tornado.web.RequestHandler):
    def get(self):
        tornado.ioloop.IOLoop.instance().stop()
        self.write("quit Garble backend")

# =================================================== PROCESS INFO ====================================================
# process name => { listener URL = localhost:<server port>/listeners/<process name> 
#                    subscriber id, to unsubscribe when all clients disconnect
#                    followers = [listener id, listener id, ...]
#                    message queue, from process
#                  }
all_listeners = {}

# POST /listeners/PUBLISHER-PROCESS
# subscribe to a process's PubSub system to receive POST updates here
class ListenerHandler(tornado.web.RequestHandler):
    def post(self, name):
        global all_listeners
        # byte stream to string
        info=self.request.body.decode("utf-8")
        if name in all_listeners:
            for ws in all_listeners[name]['ws_clients']:
                ws.write_message(info)
            logging.debug("received message [%s] from %s" % (info, name))
            self.write({"status": "success"})
        else:
            logging.warn("received message for unknown listener %s" % name)
            self.write({"status": "error"})

# WEBSOCKET
class WebSocketHandler(tornado.websocket.WebSocketHandler):

    def initialize(self, **kwargs):
        #print "Initializing WebSocketHandler"
        self.serverport = kwargs['serverport']
    
    def check_origin(self, origin):
        return True
    
    # open websocket as server. client is usually the angular application
    # adds this WebSocketHandler instance to the list of ws_clients held  in the relevant all_listeners entry
    def open(self, name):
        global all_listeners
        self.name = name
        logging.info("WebSocket OPEN %s" % name)
        
        # subscribe as listener to this process
        
#        if name in programs:
#            if name in all_listeners:
#                all_listeners[name]["ws_clients"].append(self)
#            else:
#                # first follower - have to subscribe to the process
#                listener_url = "http://ai-ml-dev.cloudapp.net:%d/listeners/%s" % (self.serverport, name)
#                subscription_url = "http://ai-ml-dev.cloudapp.net/%s/listener" % name
#                r=requests.post(subscription_url, data=json.dumps({'Url': listener_url}), headers={"Content-Type": "text/json"})
#                if r.status_code != requests.codes.ok:
#                    self.write_message("error: unable to register with %s" % name)
#                    self.close()
#                else:
#                    subscriber_id = r.json()['response']
#                    all_listeners[name] = {'unsubscription_url': "%s/%s" % (subscription_url, subscriber_id), 'ws_clients': [self] }
#        else:
#            logging.warn("received request for unknown process %s" % name)
#            self.write_message("error: unknown process %s" % name)
#            self.close()
#
    # message from client - unused
    def on_message(self, message):
        self.write_message("Client said: " + message)

    def on_close(self):
        global all_listeners
        logging.info("WebSocket CLOSE")
        if self.name in all_listeners:
            all_listeners[self.name]['ws_clients'].remove(self)
            logging.info ("WebSocket client for %s disconnected" % self.name)

            if len(all_listeners[self.name]["ws_clients"]) == 0:
                requests.delete(all_listeners[self.name]['unsubscription_url'])
                all_listeners.pop(self.name)
                logging.info ("Server unsubscribed from %s" % self.name)

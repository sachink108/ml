import os
import sys
import json
import time
import requests
import tornado.ioloop
import tornado.web
import tornado.websocket
import logging

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
        return;
        # source the information from tdm or whereever and send
        # continuously to the client
        if name in programs:
            if name in all_listeners:
                all_listeners[name]["ws_clients"].append(self)
            else:
                # first follower - have to subscribe to the process
                listener_url = "http://ai-ml-dev.cloudapp.net:%d/listeners/%s" % (self.serverport, name)
                subscription_url = "http://ai-ml-dev.cloudapp.net/%s/listener" % name
                r=requests.post(subscription_url, data=json.dumps({'Url': listener_url}), headers={"Content-Type": "text/json"})
                if r.status_code != requests.codes.ok:
                    self.write_message("error: unable to register with %s" % name)
                    self.close()
                else:
                    subscriber_id = r.json()['response']
                    all_listeners[name] = {'unsubscription_url': "%s/%s" % (subscription_url, subscriber_id), 'ws_clients': [self] }
        else:
            logging.warn("received request for unknown process %s" % name)
            self.write_message("error: unknown process %s" % name)
            self.close()

    # message from client - unused
    def on_message(self, message):
        self.write_message("Client said: " + message)

    def on_close(self):
        logging.info("WebSocket CLOSE")

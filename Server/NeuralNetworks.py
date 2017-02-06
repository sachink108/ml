import os
import sys
import json
import datetime
import time
import subprocess
import tornado.web
import logging
import re
import threading

from RequestManagement import *

# /nn/train/
# /nn/validate/
class NNRequestHandler(tornado.web.RequestHandler):

    def initialize(self, request_manager):
        self.request_manager=request_manager

    def options(self, request):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE")
        self.write({'status':'OK'})        

    def delete(self, request):
        self.set_header("Access-Control-Allow-Origin", "*")
        
        uriparser=URIParser()
        r=uriparser.parse(request)
        
        if (('action' in r['dict'] and "request_id" in r['dict'])):
            action=r['dict']['action']
            request_id=r['dict']['request_id']
            if (action == "delete"):
                (msg, status)=self.request_manager.deleteRequest(int(r['dict']['request_id']))
                self.write({'status':status, 'info':msg})
            elif (action == "cancel"):
                (msg, status)=self.request_manager.cancelRequest(int(r['dict']['request_id']))
                self.write({'status':status, 'info':msg})
            else:    
                self.write({'status':"NOK", 'info':"Invalid action"})
        else:
            self.write({'status':"NOK", 'info':"Invalid Request"})
            
    def post(self, request):
        self.set_header("Access-Control-Allow-Origin", "*")
        print "Received =", request
        (retmsg, status, robj)=self.request_manager.addRequest(request)
        print "Returning = ", {'status':status, 'msg': retmsg, 'request' : robj}
        self.write({'status':status, 'msg': retmsg, 'request' : robj})

    def get(self, query):
        self.set_header("Access-Control-Allow-Origin", "*")
        (status, retmsg)=self.request_manager.getStatus()
        self.write({'status':status,'info':retmsg})

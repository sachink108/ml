import logging
import re
import threading
from URIParser import *
import datetime
import subprocess


timeFormat='%Y-%m-%d %H:%M:%S'

# Functions to create command lines
def createTrainingCommand(params, serverport):
    return ["python",
            "F:\\Predictions\\binaries\\python-scripts\\nntrainer.py",
            "--console-port", str(serverport),
            "--streamlet-id", params['streamlet-id'],
            "--history", params['history'],
            "--prediction", params['predictions'],
            "--model-name", params['model-name-prefix']
            ]

def createValidationCommand(params, serverport):
    return ["python",
            "F:\\Predictions\\binaries\\python-scripts\\prediction_runs.py",
            "--console-port",  str(serverport),
            "--streamlet-ids", params['streamlet-id'],
            "--model-ids",     params['model-id']
            ]

# Request Manager
class RequestManager:

    def __init__(self, serverport, _type):
        if _type not in ["training", "validation"]:
            raise Exception("Invalid type of RequestManager: %s" % _type)

        self.sameRequestSafeguardDict={}
        self.lock=threading.Lock()
        self.requestId=0
        self.pending=[]
        self.runningRequest=None
        self.done=[]

        self.serverport=serverport
        self.type=_type

    def addRequest(self, request):
        uriparser=URIParser()
        r=uriparser.parse(request)
        rkey="_".join(r['dict'].values())  # 'streamlet-id_modelprefix_history_predictions'

        self.lock.acquire()
        # from http://stackoverflow.com/questions/5904969/python-how-to-print-a-dictionarys-key

        if (not rkey in self.sameRequestSafeguardDict):
            self.requestId += 1
            self.sameRequestSafeguardDict[rkey]=self.requestId

            reqobj=r['dict']
            reqobj["request-id"]=self.requestId
            reqobj["request-time"]=datetime.datetime.now().strftime(timeFormat)
            reqobj["status"]="PENDING"

            if self.type=="training":
                reqobj["command"]=createTrainingCommand(r['dict'], self.serverport)
            else:
                reqobj["command"]=createValidationCommand(r['dict'], self.serverport)

            self.pending.append(reqobj)
            (msg, status, robj)=("Queued Request %d" % self.requestId, "OK", reqobj)
        else:
            (msg, status, robj)=("Request already queued with parameters [" + ", ".join(["%s:%s" % (key, r['dict'][key]) for key in r['dict']]) + "]", "NOK", self.sameRequestSafeguardDict[rkey])

        self.lock.release()
        self._run()
        logging.info("ADD")
        logging.info(self.pending)
        return (msg, status, robj)

    def cancelRequest(self, req_id):
        self.lock.acquire()
        try:
            index=map(lambda reqObj: reqObj["request-id"]==req_id, self.pending).index(True)
            self.pending.pop(index)
            for k,v in self.sameRequestSafeguardDict.iteritems():
                if v==req_id:
                    self.sameRequestSafeguardDict.pop(k)
                    break
            (msg, status)=("Successfully cancelled request", "OK")
        except ValueError:
            (msg, status)=("Unable to cancel request", "NOK")

        self.lock.release()
        return (msg, status)

    def deleteRequest(self, req_id):
        self.lock.acquire()
        try:
            index=map(lambda reqObj: reqObj["request-id"]==req_id, self.done).index(True)
            self.done.pop(index)
            for k,v in self.sameRequestSafeguardDict.iteritems():
                if v==req_id:
                    self.sameRequestSafeguardDict.pop(k)
                    break
            (msg, status)=("Successfully deleted request", "OK")
        except ValueError:
            (msg, status)=("Unable to delete request", "NOK")

        self.lock.release()
        return (msg, status)

    def _run(self):
        self.lock.acquire()
        if self.runningRequest is None and len(self.pending) > 0:
            t=threading.Thread(target=self._finishPendingItems)
            t.start()
        self.lock.release()

    def _finishPendingItems(self):
        while len(self.pending) != 0:
            # first check if any training is running
            self.lock.acquire()
            if self.runningRequest is not None and self.runningRequest['status']=="FINISHED":
                self.done.append(self.runningRequest)
                self.runningRequest=None

            if self.runningRequest is None:
                self.runningRequest=self.pending.pop()
            self.lock.release()

            self._launchProcess()

        self.lock.acquire()
        if self.runningRequest is not None and self.runningRequest['status']=="FINISHED":
            self.done.append(self.runningRequest)
            self.runningRequest=None
        self.lock.release()

    # starts a subprocess and monitors its STDOUT to build the list of stats
    # incoming runningRequest must be PENDING, then _launchProcess sets to RUNNING, and finally to FINISHED
    def _launchProcess(self):
        logging.info("Launch command is=" + " ".join(self.runningRequest['command']))
        self.lock.acquire()
        if self.runningRequest['status'] != "PENDING":
            return
        self.runningRequest['status']="RUNNING"
        self.runningRequest['stats']=[]  # create a stats entry now that we are going to get some stats!
        self.lock.release()

        lprocess=subprocess.Popen(self.runningRequest['command'],
                                  shell=True,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT)

        infoPatterns=['(STARTED HFP)',
                      '(FINISHED HFP)',

                      ## training patterns
                      '(STARTED TRAINING)',
                      '(FINISHED TRAINING)',
                      '(TRAINING TABLE ROWS)=\[(.*?)\]$',
                      '(MODEL NAME)=\[(.*?)\]$',
                      '(MODEL ID)"=\[(.*?)\]$',

                      ## validation patterns
                      '(STARTED PRED PACKET COLLECTOR)',
                      '(OUTPUT FILES) = \[(.*?)\]$',
                      '(FINISHED PREDICTION RUN)',
                      '(STARTED MOVE-PREDS-TO-DB)',
                      '(FINISHED MOVE-PREDS-TO-DB)',
                      ]
        errorPatterns=['(TRAINING ABORTED)=\[(.*?)\]$',
                       ]

        infoMatches=[re.compile('^(.*?)\[INFO\s*\]\s '+ pat) for pat in infoPatterns]
        errorMatches=[re.compile('^(.*?)\[ERROR\s*\]\s '+ pat) for pat in errorPatterns]

        patterns = infoMatches + errorMatches

        #show all tasks that are not done also (grey color)
        textForConsoleMap={
            # training parameters
            "STARTED HFP"                      : "Data streaming start",
            "FINISHED HFP"                     : "Data streaming end",
            "STARTED TRAINING"                 : "Training start",
            "FINISHED TRAINING"                : "Train end",
            "TRAINING TABLE ROWS"              : "Training rows",
            "MODEL NAME"                       : "Model name",
            "MODEL ID"                         : "Model id",
            
            # training errors
            "TRAINING ABORTED"                 : "Training Error",
            # validation text
            "STARTED PRED PACKET COLLECTOR"    : "Prediction start",
            "OUTPUT FILES"                     : "Prediction output file",
            "FINISHED PREDICTION RUN"          : "Prediction end",
            "STARTED MOVE-PREDS-TO-DB"         : "Moving preds to db start",
            "FINISHED MOVE-PREDS-TO-DB"        : "Moving preds to db end",
        }

        # Funny observation - in subsequent training runs the output captured was one line less that the actual output.
        # eventually getting only the first few lines
        # hence temporarily reverted to the below commented method of capturing output.
        """
        while True:
            line = lprocess.stdout.readline().strip()
            if line == '' and lprocess.poll() != None:
                break
            print "ORIGINAL = ", line;
        """

        while lprocess.poll() is None:
            line=lprocess.stdout.readline().strip()
            print ">>>", line
            for pat in patterns:
                m=re.match(pat, line)
                if m:
                    print ">>>", line
                    # group(1) is time ; group(2) is event; group(3) is event value
                    self.runningRequest['stats'].append({
                        "key"   : textForConsoleMap[m.group(2)],
                        "value" : m.group(3) if m.group(2) in ["TRAINING ABORTED", "TRAINING TABLE ROWS", "MODEL NAME", "OUTPUT FILES"] else m.group(1)
                        })

        # do not access self.runningRequest after this line, may become None in _finishPendingItems
        self.runningRequest['status']="FINISHED"
        logging.info("Finished Processing")
        logging.info(self.runningRequest)

    # get status will be called on refresh.
    def getStatus(self):
        self.lock.acquire()

        retval={
            "PENDING" : dict([(self.pending[index]["request-id"],self.pending[index]) for index in range(0,len(self.pending))]),
            "RUNNING" : {self.runningRequest["request-id"] : self.runningRequest} if self.runningRequest is not None else {},
            "DONE" : dict([(self.done[index]["request-id"],self.done[index]) for index in range(0,len(self.done))])
        }
        self.lock.release()

        return ("OK", retval)

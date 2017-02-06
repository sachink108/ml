# Handlers which basically run DB queries for us

import datetime
import tornado.web
import logging
import re
import subprocess

from ConfigDB import ConfigDB
from EventProvider import EventProvider
from Streamlets import Streamlets
from SQLConnector import SQLConnector

from URIParser import *

# /sources
class SourcesHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        configDB=ConfigDB()
        self.write({'status':'success','sources':configDB.sources()})

# /dix-info/devices
# /dix-info/components/device=
# /dix-info/kpis/device=/component=
class DixInfoHandler(tornado.web.RequestHandler):
    def get(self, query):

        self.set_header("Access-Control-Allow-Origin", "*")
        configDB=ConfigDB()
        if re.match('devices/?$',query):
            devices=configDB.dix_strings('device')
            self.write({'status':'success','devices':devices})
            return

        m=re.match('components/device=([^\/]+)$',query)
        if m:
            device=m.groups()[0]
            components=configDB.dix_strings('component',device=device)
            self.write({'status':'success','device':device,'components':components})
            return

        m=re.match('kpis/device=([^\/]+)/component=([^\/]+)$',query)
        if m:
            device=m.groups()[0]
            component=m.groups()[1]
            kpis=configDB.dix_strings('kpi',device=device,component=component)
            self.write({'status':'success','device':device,'component':component,'kpis':kpis})
            return

        self.write({'status':'error','message':'invalid request'})

# /streamlet-info
class StreamletInfoHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        configDB=ConfigDB()
        streamlet_list=configDB.streamlet_info(-1)
        isoFormat='%Y-%m-%dT%H:%M:%S.%fZ'
        for streamlet in streamlet_list:
            streamlet['start']=streamlet['start'].strftime(isoFormat)
            streamlet['end']=streamlet['end'].strftime(isoFormat)
        self.write({'status':'success','streamlet-list':streamlet_list})

class DeltaTHandler(tornado.web.RequestHandler):
    def get(self, query):
        self.set_header("Access-Control-Allow-Origin", "*")
        print "query is", query
        uriparser=URIParser()
        r=uriparser.parse(query)
        #print ">>>>", r

        configDB=ConfigDB()
        dix_id = configDB.dix_id(r['dict']['d'], r['dict']['c'], r['dict']['k'])

        isoFormat='%Y-%m-%d %H:%M:%S'
        start_time=datetime.datetime.strptime(r['dict']['s'],"%d-%m-%Y T%H:%M:%S").strftime(isoFormat)
        end_time=datetime.datetime.strptime(r['dict']['e'],"%d-%m-%Y T%H:%M:%S").strftime(isoFormat)

        cmd = ["python", "F:\\Predictions\\binaries\\python-scripts\\get-delta-t.py",
               "--start-time", start_time, "--end-time", end_time, "--dix-id", str(dix_id)
               ]

        #print ">>>" ,cmd
        lprocess=subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        delta_t = None
        while lprocess.poll() is None:
            line = lprocess.stdout.readline().strip()
            if (len(line) != 0):
                delta_t = line

        self.write({'status':'success','delta-t':delta_t})

# /create-streamlet/s=START-TIME,e=END-TIME,d=DEVICE,c=COMPONENT,k=KPI,dt=DELTAT,n=NEVENTS
class CreateStreamletHandler(tornado.web.RequestHandler):
    def get(self, query):
        self.set_header("Access-Control-Allow-Origin", "*")
        uriparser=URIParser()
        r=uriparser.parse(query)
        print r

        configDB=ConfigDB()
        dx_id = configDB.dix_id(r['dict']['d'], r['dict']['c'], r['dict']['k'])

        sql=SQLConnector("PredictionCfg")
        poller = sql.executeSelect("Select source from DevCompKPI where Device=\'%s\' and Component=\'%s\' and KPI=\'%s\'" % (r['dict']['d'],r['dict']['c'],r['dict']['k']))

        isoFormat='%Y-%m-%d %H:%M:%S'
        start_time=datetime.datetime.strptime(r['dict']['s'],"%d-%m-%Y T%H:%M:%S").strftime(isoFormat)
        end_time=datetime.datetime.strptime(r['dict']['e'],"%d-%m-%Y T%H:%M:%S").strftime(isoFormat)

        query="Insert into Streamlets_Info values (\'%s\', %d, \'%s\', \'%s\', \'dt=%s %s\', %d)" % (poller[0][0], int(dx_id), start_time, end_time,r['dict']['dt'],r['dict']['de'],int(r['dict']['n']))
        #print "insert query = ", query
        sql.execute(query)

        query="Select id from Streamlets_Info where source=\'%s\' and dix_id=%d and interval_start=\'%s\' and interval_end=\'%s\' and [run-length]=%d" % (poller[0][0], int(dx_id), start_time, end_time, int(r['dict']['n']))

        #print "select query =", query
        id = sql.executeSelect(query)

        self.write({'status':'success','streamlet-id':id[0][0]})

# /delete-streamlet/id=STREAMLET_ID
class DeleteStreamletHandler(tornado.web.RequestHandler):
    def get(self, query):
        self.set_header("Access-Control-Allow-Origin", "*")
        uriparser=URIParser()
        r=uriparser.parse(query)
        print r

        sql=SQLConnector("PredictionCfg")
        query = "delete from Streamlets_Info where id=%d" % (int(r['dict']['id']))
        print query
        sql.execute(query)

        self.write({'status':'success'})

# /model-info
class ModelInfoHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        configDB=ConfigDB()
        model_list=configDB.model_info(-1)
        self.write({'status':'success','model-list':model_list})

# /run-info
class RunInfoHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header("Access-Control-Allow-Origin", "*")
        configDB=ConfigDB()
        run_list=configDB.run_info(-1)
        isoFormat='%Y-%m-%dT%H:%M:%S.%fZ'
        for run in run_list:
            run["run-time"]=run["run-time"].strftime(isoFormat)
        self.write({'status':'success','run-list':run_list})

# /run-data/run-id=,cycle=
class RunDataHandler(tornado.web.RequestHandler):
    def get(self, query):
        self.set_header("Access-Control-Allow-Origin", "*")
        uriparser=URIParser()
        r=uriparser.parse(query)
        if r['status'] == 'error':
            self.write(r)
            return

        isoFormat='%Y-%m-%dT%H:%M:%S.%fZ'
        if False in [rq in r['dict'] for rq in ['run-id','cycle']]:
            self.write({'status':'error','message':'parameter missing'})
            return

        try:
            run_id=int(r['dict']['run-id'])
            cycle=int(r['dict']['cycle'])
        except ValueError:
            self.write({'status':'error', 'message': 'run-id and cycle must be integers'})
            return
        request={'run-id':run_id, 'cycle':cycle}

        sql=SQLConnector("Analytics")
        query="SELECT [event-time], [actual], [prediction] FROM [Analytics].[dbo].[PredictionRuns] WHERE [run-id]=%d AND [cycle]=%d" % (run_id, cycle)
        r=[x for x in sql.executeSelect(query)]
        response=[{'event-time': x[0].strftime(isoFormat), 'actual': x[1], 'prediction': x[2]} for x in r]
        query="SELECT MAX(cycle) FROM [Analytics].[dbo].[PredictionRuns] WHERE [run-id]=%d" % run_id
        max_cycle=sql.executeSelect(query)[0][0]
        self.write({'status':'success', 'request':request, 'response':response, 'max_cycle':max_cycle})

# /historical/streamlet-id=STREAMLET-ID
# /historical/s=START-TIME,e=END-TIME,d=DEVICE,c=COMPONENT,k=KPI
class HistoricalTimeSeriesDataHandler(tornado.web.RequestHandler):
    # query = s=yyyy-mm-dd.hh.mm.ss,e=yyyy-mm-dd.hh.mm.ss,d=device,c=component,k=kpi
    def get(self, query):
        self.set_header("Access-Control-Allow-Origin", "*")
        uriparser=URIParser()
        r=uriparser.parse(query)
        if r['status'] == 'error':
            self.write(r)
            return

        isoFormat='%Y-%m-%dT%H:%M:%S.%fZ'

        if 'streamlet-id' in r['dict']:
            try:
                streamlet_id=int(r['dict']['streamlet-id'])
            except ValueError:
                self.write({'status':'error','message':'invalid streamlet-id'})
                return

            streamlets=Streamlets()
            dix_id=streamlets.getDixId(streamlet_id)
            start_time=streamlets.getIntervalStart(streamlet_id)
            end_time=streamlets.getIntervalEnd(streamlet_id)
            request={'streamlet-id':streamlet_id}
            logging.info("streamlet_id=%d dix_id=%d start_time=%s end_time=%s" % (streamlet_id,dix_id,start_time,end_time))

        else:

            if False in [rq in r['dict'] for rq in ['s','e','d','c','k']]:
                self.write({'status':'error','message':'parameter missing'})
                return

            try:
                start_time=datetime.datetime.strptime(r['dict']['s'],isoFormat)
            except ValueError:
                self.write({'status':'error','message':'invalid datetime format for s'})
                print(query)
                return

            print(start_time.strftime("%Y-%m-%d %H:%M:%S"))

            try:
                end_time=datetime.datetime.strptime(r['dict']['e'],isoFormat)
            except ValueError:
                self.write({'status':'error','message':'invalid datetime format for e'})
                return

            device=r['dict']['d']
            component=r['dict']['c']
            kpi=r['dict']['k']

            request={'start_time':start_time.strftime(isoFormat), 'end_time': end_time.strftime(isoFormat),'device':device,'component':component,'kpi':kpi}
            if start_time > end_time:
                self.write({'status':'success','request':request,'message':'start time > end time'})
                return

            # use ConfigDB to get the dix id
            configDB=ConfigDB()
            dix_id=configDB.dix_id(device,component,kpi)
            print("DIX ID=%d" % dix_id)

        # use EventProvider with the dix id and time interval
        ep=EventProvider(dix_id,start_time,end_time,-1)
        events=[]
        [actual_start,actual_end]=[None,None]
        while True:
            event=ep.next()
            if event is None:
                break
            if actual_start is None:
                actual_start=event[0]
            actual_end=event[0]
            events.append({'time':event[0].strftime(isoFormat),'value':event[1]})

        # put events into response
        response={}
        if len(events) > 0:
            response['actual_start'] = actual_start.strftime(isoFormat)
            response['actual_end'] = actual_end.strftime(isoFormat)
            response['events'] = events
        else:
            response['events'] = []

        self.write({'status':'success','request':request,'response':response})

# /rawtablenames/prefix=
class RawTableNamesHandler(tornado.web.RequestHandler):
    def get(self, query):
        self.set_header("Access-Control-Allow-Origin", "*")
        uriparser=URIParser()
        r=uriparser.parse(query)
        if r['status'] == 'error':
            self.write(r)
            return

        if 'prefix' not in r['dict']:
            self.write({'status':'error','message':'expected URI parameter <prefix>'})
            return

        prefix=r['dict']['prefix']
        table_query="SELECT TABLE_NAME FROM Predict.information_schema.tables WHERE TABLE_NAME LIKE 'Raw-%s-%%'" % prefix
        sqlConnector=SQLConnector('Predict')
        tables=[r[0] for r in sqlConnector.executeSelect(table_query)]

        request={'prefix':prefix}
        response={'tables':tables}
        self.write({'status':'success','request':request,'response':response})

# /alldixdata/prefix=<>,dix-id=<>
class AllDixDataHandler(tornado.web.RequestHandler):
    def get(self,query):
        self.set_header("Access-Control-Allow-Origin","*")
        uriparser=URIParser()
        r=uriparser.parse(query)
        if r['status']=='error':
            self.write(r)
            return

        if 'prefix' not in r['dict']:
            self.write({'status':'error','message':'expected URI parameter <prefix>'})
            return
        if 'dix-id' not in r['dict']:
            self.write({'status':'error','message':'expected URI parameter <dix-id>'})
            return

        prefix=r['dict']['prefix']
        dix_id=int(r['dict']['dix-id'])
        table_query="SELECT TABLE_NAME FROM Predict.information_schema.tables WHERE TABLE_NAME LIKE 'Raw-%s-%d-%%'" % (prefix,dix_id)
        sqlConnector=SQLConnector('Predict')
        tables=[r[0] for r in sqlConnector.executeSelect(table_query)]
        tables.sort()

        data=[]
        isoFormat='%Y-%m-%dT%H:%M:%S.%fZ'
        for table in tables:
            query="SELECT eventTime, value FROM Predict.dbo.[%s] ORDER BY eventTime" % table
            data += [(r[0].strftime(isoFormat),float(r[1])) for r in sqlConnector.executeSelect(query)]

        request={'prefix':prefix,'dix-id':dix_id}
        response={'data':data}
        self.write({'status':'success','request':request,'response':response})

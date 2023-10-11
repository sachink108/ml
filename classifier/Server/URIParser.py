# parses URI params given as /key=value,key=value,...

class URIParser:
    def __init__(self):
        pass

    def parse(self, query):
        query=query.strip()
        if len(query) == 0:
            return {'status':'error','message':'no query string provided'}
        ret_dict={}
        params=query.split(',')
        for param in params:
            kv=param.strip().split('=')
            if len(kv) != 2:
                return {'status':'error','message':"params must be of the form k=v: %s" % param}
            [k,v]=kv
            if len(k) == 0 or len(v) == 0:
                return {'status':'error','message':'invalid request'}
            if ret_dict.has_key(k):
                return {'status':'error','message':'repeated parameter:' + k}
            ret_dict[k]=v
        return {'status':'success','dict':ret_dict}


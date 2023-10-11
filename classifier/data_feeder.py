import os
import sys
import requests
import json
import io

def readDir(path):
    for dirpath, dirs, files in os.walk(path):
        for name in files:
            filename = os.path.join(dirpath,name);
            print(filename)
            with io.open(filename, "r", encoding="utf-8", errors='ignore') as my_file:
                content = my_file.read() 
            r = requests.post('http://localhost:9000/postdoc', 
                            data=json.dumps({'dir': dirpath, 
                                            'filename' : name,
                                            'content' : content}),
                            headers={"Content-Type": "text/json"})
            #r = requests.post('http://localhost:9000/postdoc', data=json.dumps({'filename': filename, 'file_content' : content}, ensure_ascii=False, encoding='utf-8'), headers={"Content-Type": "text/json"})
            if r.status_code != requests.codes.ok:
                print ("Could not send " + filename)
            else:
                print ("Sent " + filename)
            #raw_input()

def main():
    dataFolder = ".\\data\\20_newsgroups"
    readDir(dataFolder)

main()
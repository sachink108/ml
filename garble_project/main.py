import os
import sys
from glob import glob
import threading
from TermDocumentMatrix import TDM
from TParser import TParser

def main():
    dataFolder = "G:\\SachinK\\progs\\search\\docs"
    tdm = TDM.instance()
    
    for doc in glob(dataFolder+ '\\*.txt'):
        p1 = TParser(doc)
        p1.start()
    
    mainThread = threading.currentThread()
    for t in threading.enumerate():
        if t is mainThread:
            continue
        t.join()
    
    print (tdm.search("Gutenberg"))
    tdm.store()
main()        

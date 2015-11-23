#!/usr/bin/python

import random
import sys
import pandas as pd
from Queue import Queue
from multiprocessing import Process 
import time
from pymongo import MongoClient
import pymongo
from UseTor import UseTor
from Scraper import Scraper, pass_function



url_format = 'http://www.zillow.com/homes/recently_sold/{}_rb/1_p'

http_codes_counter = {}

MONGODB_HOSTNAME = 'localhost'

class Worker(Process):
    def __init__(self, zip_code, socks_proxy_port, base_control_port):
        Process.__init__(self)
        self.socks_proxy_port = socks_proxy_port
        self.base_control_port = base_control_port
        self.conn = MongoClient(MONGODB_HOSTNAME, 27017)
        self.db = self.conn.Zillow
        self.coll = self.db.zip_codes
        self.zip_code = zip_code

    def run(self):
        # create tor here
        self.opener = UseTor(
            'mypasswordAndy',
            self.socks_proxy_port,
            self.base_control_port,
            pass_function)
        try:

            #from here pass the opener connection to Scraper 
            #which will update the housing database
            Scraper(self.opener,self.zip_code)
            self.coll.update({'zip_code':zip_code}, {'$set': {'finished':1}})
            self.conn.close()

        except:
            print "Unexpected error:", sys.exc_info()[0]
            pass # leave this element for the next cycle

class Discovery:
    NWorkers = 100
    SocksProxyBasePort = 9050
    BaseControlPort = 8118
    Contention = 10000

    def __init__(self):
        
        self.conn = MongoClient(MONGODB_HOSTNAME, 27017)
        self.db = self.conn.Zillow
        self.coll = self.db.zip_codes
        
        self.queue = Queue()
        
        # add items into queue
        for item in self.coll.find({'finished': {'$ne': 1}}):
            self.queue.put(item['zip_code'])

    def start(self):
        """
        Runs through all of the items in the queue
        Starts up the number of Discovery Workers then waits for them to finish then repeats
        """
        while(self.queue.empty()!=True):
            self.workers = []
            for i in range(Discovery.NWorkers):
                worker = Worker(self.queue.get(), Discovery.SocksProxyBasePort + i, Discovery.BaseControlPort + i)
                self.workers.append(worker)

            for w in self.workers:
                w.start()

            for w in self.workers:
                w.join()

def main():
    discovery = Discovery()
    discovery.start()

if __name__ == '__main__':
    main()

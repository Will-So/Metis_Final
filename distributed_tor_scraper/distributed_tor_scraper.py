#!/usr/bin/python

import random
import sys
import pandas as pd
from Queue import Queue
from threading import Thread, Condition, Lock
from threading import active_count as threading_active_count
from multiprocessing import Process 
import time
from pymongo import MongoClient
import pymongo
from UseTor import UseTor
from Scraper import Scraper, pass_function



url_format = 'http://www.zillow.com/homes/recently_sold/{}_rb/1_p'

http_codes_counter = {}

MONGODB_HOSTNAME = 'localhost'

class Worker(Thread):
    def __init__(self, queue, discovery, socks_proxy_port, base_control_port):
        Thread.__init__(self)
        self.queue = queue
        self.discovery = discovery
        self.socks_proxy_port = socks_proxy_port
        self.base_control_port = base_control_port
        self.conn = MongoClient(MONGODB_HOSTNAME, 27017)
        self.db = self.conn.Zillow
        self.coll = self.db.zip_codes

    def run(self):
        # create tor here
        self.opener = UseTor(
            'mypasswordAndy',
            self.socks_proxy_port,
            self.base_control_port,
            pass_function)
        while True:
            try:
                zip_code = self.queue.get()

                if zip_code == None:
                    self.queue.put(None) # Notify the next worker
                    break

                #from here pass the opener connection to Scraper 
                #which will update the housing database
                Scraper(self.opener,zip_code)

                print 'update zip codes'
                self.coll.update({'zip_code':zip_code}, {'$set': {'finished':1}})

                self.discovery.lock.acquire()
                self.discovery.records_to_process -= 1
                if self.discovery.records_to_process == 0:
                    self.discovery.lock.notify()
                self.discovery.lock.release()

            except:
                print "Unexpected error:", sys.exc_info()[0]
                self.discovery.exception_counter_lock.acquire()
                self.discovery.exception_counter += 1
                self.discovery.exception_counter_lock.release()
                pass # leave this element for the next cycle

            time.sleep(1.5)

class Croupier(Thread):
    def __init__(self, queue, discovery):
        Thread.__init__(self)
        self.conn = MongoClient(MONGODB_HOSTNAME, 27017)
        self.db = self.conn.Zillow
        self.coll = self.db.zip_codes
        self.finish_signal = False
        self.queue = queue
        self.discovery = discovery
        self.discovery.records_to_process = 0

    def run(self):
        # Look if imdb collection is empty. Only if its empty we create all the items
        c = self.coll.count()
        if c == 0:
            print "Inserting items"
            self.coll.ensure_index([('zip_code', pymongo.ASCENDING), ('finished', pymongo.ASCENDING)])

            #use data from pandas
            df = pd.read_csv('zip_code_database.csv')
            # Just use 5 digit zip codes
            df = df[df['zip'].apply(lambda x:len(str(x))==5)]
            for zip_code in df['zip']:
                self.coll.insert({'zip_code':zip_code, 'url': url_format.format(zip_code), 'finished': 0})

        else:
            print "Using #", c, " persisted items"

        while True:
            items = self.coll.find({'finished': {'$ne': 1}})

            self.discovery.records_to_process = items.count()

            if self.discovery.records_to_process == 0:
                break

            for item in items:
                self.queue.put(item['zip_code'])

            # Wait until the last item is updated on the db
            self.discovery.lock.acquire()
            while self.discovery.records_to_process != 0:
                self.discovery.lock.wait()
            self.discovery.lock.release()

            time.sleep(60)

        # Send a 'signal' to workers to finish
        self.queue.put(None)

    def finish(self):
        self.finish_signal = True

class Discovery:
    NWorkers = 5
    SocksProxyBasePort = 9050
    BaseControlPort = 8118
    Contention = 10000

    def __init__(self):
        self.queue = Queue(Discovery.Contention)
        self.workers = []
        self.lock = Condition()
        self.exception_counter_lock = Lock()
        self.records_to_process = 0
        self.exception_counter = 0

    def start(self):
        croupier = Croupier(self.queue, self)
        croupier.start()

        for i in range(Discovery.NWorkers):
            worker = Worker(self.queue, self, Discovery.SocksProxyBasePort + i, Discovery.BaseControlPort + i)
            self.workers.append(worker)

        for w in self.workers:
            w.start()

        print 'workers all started set to join them'
        for w in self.workers:
            w.join()

        croupier.join()

        print "Queue finished with:", self.queue.qsize(), "elements"

def main():
    discovery = Discovery()
    discovery.start()

if __name__ == '__main__':
    main()

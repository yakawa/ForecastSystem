#!/usr/bin/env python3
import os
import datetime
import json
import logging
import argparse
import sqlite3

import numpy as np
from slack_log_handler import SlackLogHandler

HOME = os.path.expanduser('~')

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

def init_slack():
    if not os.path.exists(HOME + '/.slack_hook'):
        return
    wh = json.loads(open(HOME + '/.slack_hook').read())
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    slack = SlackLogHandler(
        wh['webhook'],
        username = 'Notifier',
        emojis = {
            logging.INFO: ':grinning:',
            logging.WARNING: ':white_frowning_face:',
            logging.ERROR: ':persevere:',
            logging.CRITICAL: ':confounded:',
        }
    )
    slack.setLevel(logging.INFO)
    slack.setFormatter(formatter)
    logger.addHandler(slack)    

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

def makeStationList(fn):
    ret = []
    with open(fn, 'r') as f:
        for line in f:
            w = line.split(' ')
            ret.append(w[0])
    return ret

def makeDB(db):
    with sqlite3.connect(db) as con:
        cur = con.cursor()

        sql = '''
        CREATE TABLE IF NOT EXISTS StationFcstHourly
        (
         Station TEXT,
         init DATETIME,
         ft   INTEGER,
         Wx   INTEGER,
         PoP  INTEGER,
         Temp INTEGER,
         WD   INTEGER,
         WS   INTEGER,
         RH   INTEGER,
         Prec INTEGER,
        UNIQUE (Station, init, ft)
        );'''
        cur.execute(sql)
        

def makeEmptyColumn(db, init, stations):
    with sqlite3.connect(db) as con:
        con.row_factory = dict_factory
        cur = con.cursor()
        
        sql = '''
        INSERT OR REPLACE INTO StationFcstHourly
        (Station, init, ft, Wx, PoP, Temp, WD, WS, RH, Prec) VALUES (?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL)
        '''
        for station in stations:
            for ft in range(85):
                cur.execute(sql, (station, init, ft))
        con.commit()
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Guidance Temp.')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time (YYYYmmddHH)')
    parser.add_argument('list', metavar='LIST', type=str, help='Station List')
    parser.add_argument('fcst', metavar='FCST', type=str, help='Forecast DB')
    
    args = parser.parse_args()

    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    stations = makeStationList(args.list)
    makeDB(args.fcst)
    makeEmptyColumn(args.fcst, init, stations)

    

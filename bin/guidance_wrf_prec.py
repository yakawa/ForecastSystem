#!/usr/bin/env python3
import os
import datetime
import json
import logging
import argparse
import sqlite3
import math

import numpy as np
from slack_log_handler import SlackLogHandler

HOME = os.path.expanduser('~')

R = np.mat([1])
S = 0.0001
I = np.identity(11)


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

def makeGuidance(db, init, coeff):
    stations = []
    with sqlite3.connect(db) as con:
        con.row_factory = dict_factory
        cur = con.cursor()

        sql = '''
        SELECT DISTINCT Station FROM WRFFcst WHERE init = ?;
        '''
        cur.execute(sql, (init,))

        rows = cur.fetchall()
        for r in rows:
            stations.append(r['Station'])
        for station in stations:
            sql = '''SELECT init, ft, rain_rnc, rain_rc FROM WRFFcst WHERE Station = ? AND init = ?'''
            cur.execute(sql, (station, init))
            rows = cur.fetchall()
            for r in rows:
                rnc = float(r['rain_rnc'])
                rc = float(r['rain_rc'])
                if rnc < 0:
                    rnc = 0.
                if rc < 0:
                    rc = 0.    
                prec = rnc + rc
                sql2 = ''' UPDATE StationFcstHourly SET Prec = ? WHERE Station = ? AND init = ? AND ft = ?;'''
                cur.execute(sql2, (prec, station, init, int(r['ft'])))
            con.commit()

            

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Guidance Temp.')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time (YYYYmmddHH)')
    parser.add_argument('fcst', metavar='FCST', type=str, help='Forecast DB')
    parser.add_argument('coeff', metavar='COEFFICIENT', type=str, help='Coefficient Directory')
    
    args = parser.parse_args()

    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    makeGuidance(args.fcst, init, args.coeff)

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

def wd(ws, deg):
    if ws < 0.5 or deg == 0.:
        return 0
    if 348.75 < deg <= 360 or 0 < deg <= 11.25:
        return 16
    if 11.25 < deg <= 33.75:
        return 1
    if 33.75 < deg <= 56.25:
        return 2
    if 56.25 < deg <= 78.75:
        return 3
    if 78.75 < deg <= 101.25:
        return 4
    if 101.25 < deg <= 123.75:
        return 5
    if 123.75 < deg <= 146.25:
        return 6
    if 146.25 < deg <= 168.75:
        return 7
    if 168.75 < deg <= 191.25:
        return 8
    if 191.25 < deg <= 213.75:
        return 9
    if 213.75 < deg <= 236.25:
        return 10
    if 236.75 < deg <= 258.75:
        return 11
    if 258.75 < deg <= 281.25:
        return 12
    if 281.25 < deg <= 303.75:
        return 13
    if 303.75 < deg <= 326.25:
        return 14
    if 326.25 < deg <= 348.25:
        return 15
    else:
        return -1

def wdws(u, v):
    ws = math.sqrt(u * u + v * v)
    ws = int(round(ws * 10, 0))
    if v == 0 and u == 0:
        d = 0
    else:
        d = math.degrees(math.atan2(u, v) + math.pi)
    return wd(ws, d), ws
    

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
            sql = '''SELECT init, ft, u10, v10 FROM WRFFcst WHERE Station = ? AND init = ?'''
            cur.execute(sql, (station, init))
            rows = cur.fetchall()
            for r in rows:
                wd, ws = wdws(float(r['u10']), float(r['v10']))
                sql2 = ''' UPDATE StationFcstHourly SET WD = ?, WS = ? WHERE Station = ? AND init = ? AND ft = ?;'''
                cur.execute(sql2, (wd, ws, station, init, int(r['ft'])))
            con.commit()

            

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Guidance Temp.')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time (YYYYmmddHH)')
    parser.add_argument('fcst', metavar='FCST', type=str, help='Forecast DB')
    parser.add_argument('coeff', metavar='COEFFICIENT', type=str, help='Coefficient Directory')
    
    args = parser.parse_args()

    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    makeGuidance(args.fcst, init, args.coeff)

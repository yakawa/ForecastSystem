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
            cld = {}
            sql = ''' SELECT ft, cld_lo, cld_mo, cld_hi FROM WRFFcst WHERE Station = ? AND init = ?;'''
            cur.execute(sql, (station, init))
            rows = cur.fetchall()
            for r in rows:
                cld[r['ft']] = {
                    'cld_lo': float(r['cld_lo']),
                    'cld_mi': float(r['cld_mo']),
                    'cld_hi': float(r['cld_hi']),
                    'cld': 1. - (1. - float(r['cld_lo'])) * (1. - float(r['cld_mo'])) 
                }
            sql = ''' SELECT ft, Prec, PoP, Temp, RH FROM StationFcstHourly WHERE Station = ? AND init = ?; '''
            cur.execute(sql, (station, init))
            rows = cur.fetchall()
            for r in rows:
                wx = -1
                if r['Prec'] >= 0.5 or r['PoP'] >= 50:
                    l1 = -(100. / 9.) * (int(r['Temp']) / 10. - 10.5)
                    l2 = -(100. / 9.) * (int(r['Temp']) / 10. - 9.75)
                    l3 = -(100. / 9.) * (int(r['Temp']) / 10. - 8.75)
                    if l1 < int(r['RH']):
                        wx = 300
                    elif l2 < int(r['RH']) <= l1:
                        wx = 334
                    elif l3 < int(r['RH']) <= l2:
                        wx = 433
                    else:
                        wx = 400
                else:
                    if cld[r['ft']]['cld_lo'] >= 0.7 or cld[r['ft']]['cld_mi'] >= 0.7 or cld[r['ft']]['cld_hi'] >= 0.8:
                        wx = 200
                    elif cld[r['ft']]['cld'] >= 0.7:
                        wx = 200
                    else:
                        wx = 100
                sql2 = ''' UPDATE StationFcstHourly SET Wx = ? WHERE Station = ? AND init = ? AND ft = ?;'''
                cur.execute(sql2, (wx, station, init, int(r['ft'])))
            con.commit()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Guidance Temp.')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time (YYYYmmddHH)')
    parser.add_argument('fcst', metavar='FCST', type=str, help='Forecast DB')
    parser.add_argument('coeff', metavar='COEFFICIENT', type=str, help='Coefficient Directory')
    
    args = parser.parse_args()

    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    makeGuidance(args.fcst, init, args.coeff)

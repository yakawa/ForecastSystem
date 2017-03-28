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

R = np.mat([1])
S = 0.0001
I = np.identity(11)


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

def readCoefficient(station, d):
    if os.path.isdir(d + '/wrf_rh/{}'.format(station)) is False:
        #[[1], [f['rh']], [f['ew']], [f['ww']], [f['nw']], [f['sw']], [f['cldlo']], [f['cldmi']], [1. - f['cldlo']], [1. - f['cldmi']], [f['prec']]])
        return [np.mat([[0.], [1.], [0.], [0],[0],[0],[0],[0],[0],[0],[0]]),] * 24
    x_hat = np.load(d + '/wrf_rh/{}/x_hat.npy'.format(station))
    return x_hat
    
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
            x_hat = readCoefficient(station, coeff)
            sql = ''' SELECT ft, rh2, u10, v10, cld_lo, cld_mo, cld_hi, rain_rc + rain_rnc AS prec FROM WRFFcst WHERE Station = ? AND init = ?;'''
            cur.execute(sql, (station, init))
            rows = cur.fetchall()
            for r in rows:
                date = init + datetime.timedelta(hours=int(r['ft']))
                ew = r['u10'] if r['u10'] > 0. else 0.
                ww = -1 * r['u10'] if r['u10'] <= 0. else 0.
                nw = r['v10'] if r['v10'] > 0. else 0.
                sw = -1 * r['v10'] if r['v10'] <= 0. else 0.

                C = np.mat([[1], [r['rh2']], [ew], [ww], [nw], [sw], [r['cld_lo']], [r['cld_mo']], [1. - r['cld_lo']], [1. - r['cld_mo']], [r['prec']]])
                v = int(round(float(C.T * x_hat[date.hour]), 2) * 100)
                sql2 = ''' UPDATE StationFcstHourly SET RH = ? WHERE Station = ? AND init = ? AND ft = ?;'''
                if v > 100.:
                    v = 100
                if v < 0:
                    v = 0
                cur.execute(sql2, (v, station, init, int(r['ft'])))
                
                print(date, station, float(C.T * x_hat[date.hour]), r['rh2'], v)
            con.commit()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Guidance Temp.')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time (YYYYmmddHH)')
    parser.add_argument('fcst', metavar='FCST', type=str, help='Forecast DB')
    parser.add_argument('coeff', metavar='COEFFICIENT', type=str, help='Coefficient Directory')
    
    args = parser.parse_args()

    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    makeGuidance(args.fcst, init, args.coeff)

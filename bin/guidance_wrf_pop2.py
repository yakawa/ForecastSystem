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
    if os.path.isdir(d + '/wrf_pop/{}'.format(station)) is False:
        #[[1], [v['ne850']], [v['sw850']], [v['nw850']], [v['se850']], [v['w850']], [v['ne500']], [v['sw500']], [v['nw500']], [v['se500']], [v['rh850']], [v['cape']], [v['cin']], [v['cape-cin']], [v['ssi']], [v['ssi75']], [v['ssi98']]]
        return np.mat([[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0],[0]])
    x_hat = np.load(d + '/wrf_pop/{}/x_hat.npy'.format(station))
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
            sql = '''
            SELECT init, ft, uwind_850, vwind_850, rh_850, uwind_500, vwind_500, wwind_850, rain_rc, cape, cin, tpw, ssi, ssi700_500, ssi925_850 FROM WRFFcst WHERE Station = ? AND init = ?;
            '''
            cur.execute(sql, (station, init))
      
            rows = cur.fetchall()
            for r in rows:
                t_ne = r['uwind_850'] / math.sqrt(2) + r['vwind_850'] / math.sqrt(2.)
                ne850 = 0. if t_ne < 0 else t_ne
                sw850 = 0. if t_ne >= 0 else  -1 * t_ne
                t_nw = -1. * r['uwind_850'] / math.sqrt(2.) + r['vwind_850'] / math.sqrt(2.)
                nw850 = 0. if t_nw < 0 else t_nw
                se850 = 0. if t_nw >= 0 else -1 * t_nw
                t_ne = r['uwind_500'] / math.sqrt(2) + r['vwind_500'] / math.sqrt(2.)
                ne500 = 0. if t_ne < 0 else t_ne
                sw500 = 0. if t_ne >= 0 else  -1 * t_ne
                t_nw = -1. * r['uwind_500'] / math.sqrt(2.) + r['vwind_500'] / math.sqrt(2.)
                nw500 = 0. if t_nw < 0 else t_nw
                se500 = 0. if t_nw >= 0 else -1 * t_nw
                rh850 = float(r['rh_850'])
                cape = float(r['cape'])
                cin = float(r['cin'])
                cc = cape - cin
                ssi = float(r['ssi'])
                ssi75 = float(r['ssi700_500'])
                ssi98 = float(r['ssi925_850'])
                w850 = float(r['wwind_850'])
                
                C = np.mat([[1], [ne850], [sw850], [nw850], [se850], [w850], [ne500], [sw500], [nw500], [se500], [rh850], [cape], [cin], [cc], [ssi], [ssi75], [ssi98]])
                v = int(round(float((C.T * x_hat)[0]), 0))
                sql2 = ''' UPDATE StationFcstHourly SET PoP = ? WHERE Station = ? AND init = ? AND ft = ?;'''
                cur.execute(sql2, (v, station, init, int(r['ft'])))
            con.commit()
            
                
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Guidance Temp.')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time (YYYYmmddHH)')
    parser.add_argument('fcst', metavar='FCST', type=str, help='Forecast DB')
    parser.add_argument('coeff', metavar='COEFFICIENT', type=str, help='Coefficient Directory')
    
    args = parser.parse_args()

    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    makeGuidance(args.fcst, init, args.coeff)

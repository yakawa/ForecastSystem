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

def makeStationList(obs, fcst):
    stn = {}
    
    with sqlite3.connect(obs) as con:
        con.row_factory = dict_factory
        cur = con.cursor()

        sql = '''
        SELECT
          DISTINCT StationID
        FROM
          JMAObsHourly;
        '''
        cur.execute(sql)
        rows = cur.fetchall()
        for r in rows:
            stn[r['StationID']] = 1
            
    with sqlite3.connect(fcst) as con:
        con.row_factory = dict_factory
        cur = con.cursor()

        sql = '''
        SELECT
          DISTINCT Station
        FROM
          WRFFcst;
        '''
        cur.execute(sql)
        rows = cur.fetchall()
        for r in rows:
            if r['Station'] not in stn:
                stn[r['Station']] = 1
            else:
                stn[r['Station']] += 1

    return [s for s in stn if stn[s] == 2]
    
def update(P, C, R, x_hat, obs, I):
    """
    P: 誤差共分散行列
    C: 観測系数行列
    R: 観測ノイズ分散行列
    """
    #カルマンゲイン
    G = P * C / (C.T * P * C + R)
    x_hat = x_hat + G * (obs - C.T * x_hat)
    P = (I -  G * C.T) * P
    return x_hat, P

def readCoefficient(d, station):
    if os.path.isdir(d + '/wrf_temp/{}'.format(station)) is False:
        return None, None, None
    P = np.load(d + '/wrf_temp/{}/P.npy'.format(station))
    x_hat = np.load(d + '/wrf_temp/{}/x_hat.npy'.format(station))
    with open(d + '/wrf_temp/{}/last.json'.format(station)) as f:
        v = json.loads(f.read())
    return P, x_hat, datetime.datetime.strptime(v['LastDate'], '%Y/%m/%d %H:%M:%S')

def saveCoefficient(d, station, P, x_hat, last):
    if os.path.isdir(d + '/wrf_temp/{}'.format(station)) is False:
        os.makedirs(d + '/wrf_temp/{}'.format(station))
    np.save(d + '/wrf_temp/{}/P.npy'.format(station), P)
    np.save(d + '/wrf_temp/{}/x_hat.npy'.format(station), x_hat)

    v = {'LastDate': (last + datetime.timedelta(hours=9)).strftime('%Y/%m/%d %H:%M:%S')}
    with open(d + '/wrf_temp/{}/last.json'.format(station), 'w') as f:
        f.write(json.dumps(v))
    
def getForecast(db, station, ft, begin, end):
    ret = []
    with sqlite3.connect(db) as con:
        con.row_factory = dict_factory
        cur = con.cursor()

        if begin is None:
            sql = ''' SELECT init, ft, t2, u10, v10, cld_lo, cld_mo, cld_hi, rain_rc + rain_rnc AS prec FROM WRFFcst WHERE ft = ? AND Station = ? AND init <= ? ORDER BY init; '''
            cur.execute(sql, (ft, station, end))
        else:
            sql = ''' SELECT init, ft, t2, u10, v10, cld_lo, cld_mo, cld_hi, rain_rc + rain_rnc AS prec FROM WRFFcst WHERE ft = ? AND Station = ? AND init > ? AND init <= ? ORDER BY init;'''
            cur.execute(sql, (ft, station, begin, end))
        rows = cur.fetchall()
        for r in rows:
            init = datetime.datetime.strptime(r['init'], '%Y-%m-%d %H:%M:%S')
            date = init + datetime.timedelta(hours=int(r['ft']))
            ew = r['u10'] if r['u10'] > 0. else 0.
            ww = -1 * r['u10'] if r['u10'] <= 0. else 0.
            nw = r['v10'] if r['v10'] > 0. else 0.
            sw = -1 * r['v10'] if r['v10'] <= 0. else 0.
            
            ret.append({'date': date, 'temp': float(r['t2']), 'ew': ew, 'ww': ww, 'nw': nw, 'sw': sw, 'cldlo': float(r['cld_lo']), 'cldmi': float(r['cld_mo']), 'cldhi': float(r['cld_hi']), 'prec': float(r['prec']), 'init': init})
    return ret

def getObservation(db, station, begin, end):
    ret = {}
    with sqlite3.connect(db) as con:
        con.row_factory = dict_factory
        cur = con.cursor()

        if begin is None:
            sql = ''' SELECT Date, Temp FROM JMAObsHourly WHERE StationID = ? AND TempFlag = 0 AND Date <= ? ORDER BY Date; '''
            cur.execute(sql, (station, end))
        else:
            sql = ''' SELECT Date, Temp FROM JMAObsHourly WHERE StationID = ? AND TempFlag = 0 AND Date > ? AND Date <= ? ORDER BY Date;'''
            cur.execute(sql, (station, begin, end))
        rows = cur.fetchall()
        for r in rows:
            date = datetime.datetime.strptime(r['Date'], '%Y-%m-%d %H:%M:%S') - datetime.timedelta(hours=9)
            ret[date] = float(r['Temp'])
    return ret

def learnCoefficient(stations, dir):
    _end_init = (datetime.datetime.utcnow() - datetime.timedelta(days=4)).replace(hour=0, minute=0, second=0)
    _end_obs =  (datetime.datetime.utcnow() - datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0)
    
    for station in stations:
        P = [np.identity(11),] * 24
        x_hat = [np.mat([[0], [0], [0], [0], [0], [0], [0], [0], [0], [0], [0]]),] * 24

        _P, _x_hat, _begin = readCoefficient(dir, station)
        if _P is not None:
            P = _P
            x_hat = _x_hat
            
        obs = getObservation(args.obs, station, _begin, _end_obs)
        for ft in range(24 * 3):
            fcst = getForecast(args.fcst, station, ft, _begin, _end_init)
                
            for f in fcst:
                if f['date'] not in obs:
                    continue
                h = f['date'].hour
                C = np.mat([[1], [f['temp']], [f['ew']], [f['ww']], [f['nw']], [f['sw']], [f['cldlo']], [f['cldmi']], [1. - f['cldlo']], [1. - f['cldmi']], [f['prec']]])
                P[h] = P[h] + S ** 2
                ob = np.mat(obs[f['date']])

                x_hat[h], P[h] = update(P[h], C, R, x_hat[h], ob, I)
        saveCoefficient(dir, station, P, x_hat, _end_obs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Learn Temp KF.')
    parser.add_argument('fcst', metavar='FCST', type=str, help='Forecast DB')
    parser.add_argument('obs', metavar='OBS', type=str, help='Observation DB')
    parser.add_argument('coeff', metavar='COEFFICIENT', type=str, help='Coefficient Directory')
    
    args = parser.parse_args()

    stations = makeStationList(args.obs, args.fcst)
    logger.info('気温ガイダンスの学習を開始しました。')
    learnCoefficient(stations, args.coeff)
    logger.info('気温ガイダンスの学習を終了しました。')

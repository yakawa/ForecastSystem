#!/usr/bin/env python3
import os
import datetime
import json
import logging
import argparse
import sqlite3
import time

from slack_log_handler import SlackLogHandler
import requests
from pyquery import PyQuery as pq

HOME = os.path.expanduser('~')
URLBase = 'http://www.data.jma.go.jp/obd/stats/etrn/view/daily_s1.php'

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
    
def getStation(db):
    ret = []
    with sqlite3.connect(db) as con:
        con.row_factory = dict_factory
        cur = con.cursor()

        sql = '''
        SELECT
          BlockNo, StationNo, Name
        FROM
          JMAStation
        WHERE
          Type = 's'
        '''
        cur.execute(sql)
        rows = cur.fetchall()
        for r in rows:
            if r['StationNo'] in ['89532', '47639', '47821']:
                continue
            ret.append({'Block': r['BlockNo'], 'Station': r['StationNo'], 'Name': r['Name']})
    return ret

def changeWD(wd):
    w = {'北': 16, '北北東': 1, '北東': 2, '東北東': 3,
         '東': 4, '東南東': 5, '南東': 6, '南南東': 7,
         '南': 8, '南南西': 9, '南西': 10, '西南西': 11,
         '西': 12, '西北西': 13, '北西': 14, '北北西': 15,
         '静穏': 0}
    return w[wd]         

def parseData(html, obs):
    root = pq(html)
    ret = []
    for i, days in enumerate(root('table#tablefix1.data2_s tr.mtx').items()):
        if i < 4:
            continue
        day = i - 3
        obs = obs.replace(day=day)

        v = {
            'date': obs,
        }
        for j, col in enumerate(days('td.data_0_0').items()):
            if j == 0:
                if col.text() == '×':
                    v['StationPress'] = None
                    v['StationPressFlag'] = 9
                elif col.text() == '':
                    v['StationPress'] = None
                    v['StationPressFlag'] = None
                else:
                    try:
                        v['StationPress'] = float(col.text())
                        v['StationPressFlag'] = 0
                    except:
                        v['StationPress'] = None
                        v['StationPressFlag'] = -1
            elif j == 1:
                if col.text() == '×':
                    v['MSL'] = None
                    v['MSLFlag'] = 9
                elif col.text() == '':
                    v['MSL'] = None
                    v['MSLFlag'] = None
                else:
                    try:
                        v['MSL'] = float(col.text())
                        v['MSLFlag'] = 0
                    except:
                        v['MSL'] = None
                        v['MSLFlag'] = -1
            elif j == 2:
                if col.text() == '--':
                    v['Prec'] = None
                    v['PrecFlag'] = 0
                elif col.text() == '×':
                    v['Prec'] = None
                    v['PrecFlag'] = 9
                elif col.text() == '':
                    v['Prec'] = None
                    v['PrecFlag'] = None
                else:
                    try:
                        v['Prec'] = float(col.text())
                        v['PrecFlag'] = 0
                    except:
                        v['Prec'] = None
                        v['PrecFlag'] = -1
            elif j == 3:
                if col.text() == '--':
                    v['PrecMax1hour'] = None
                    v['PrecMax1hourFlag'] = 0
                elif col.text() == '×':
                    v['PrecMax1hour'] = None
                    v['PrecMax1hourFlag'] = 9
                elif col.text() == '':
                    v['PrecMax1hour'] = None
                    v['PrecMax1hourFlag'] = None
                else:
                    try:
                        v['PrecMax1hour'] = float(col.text())
                        v['PrecMax1hourFlag'] = 0
                    except:
                        v['PrecMax1hour'] = None
                        v['PrecMax1hourFlag'] = -1
            elif j == 4:
                if col.text() == '--':
                    v['PrecMax10min'] = None
                    v['PrecMax10minFlag'] = 0
                elif col.text() == '×':
                    v['PrecMax10min'] = None
                    v['PrecMax10minFlag'] = 9
                elif col.text() == '':
                    v['PrecMax10min'] = None
                    v['PrecMax10minFlag'] = None
                else:
                    try:
                        v['PrecMax10min'] = float(col.text())
                        v['PrecMax10minFlag'] = 0
                    except:
                        v['PrecMax10min'] = None
                        v['PrecMax10minFlag'] = -1
            elif j == 5:
                if col.text() == '×':
                    v['TempAve'] = None
                    v['TempAveFlag'] = 9
                elif col.text() == '':
                    v['TempAve'] = None
                    v['TempAveFlag'] = None
                else:
                    try:
                        v['TempAve'] = float(col.text())
                        v['TempAveFlag'] = 0
                    except:
                        v['TempAve'] = None
                        v['TempAveFlag'] = -1
            elif j == 6:
                if col.text() == '×':
                    v['TempMax'] = None
                    v['TempMaxFlag'] = 9
                elif col.text() == '':
                    v['TempMax'] = None
                    v['TempMaxFlag'] = None
                else:
                    try:
                        v['TempMax'] = float(col.text())
                        v['TempMaxFlag'] = 0
                    except:
                        v['TempMax'] = None
                        v['TempMaxFlag'] = -1
            elif j == 7:
                if col.text() == '×':
                    v['TempMin'] = None
                    v['TempMinFlag'] = 9
                elif col.text() == '':
                    v['TempMin'] = None
                    v['TempMinFlag'] = None
                else:
                    try:
                        v['TempMin'] = float(col.text())
                        v['TempMinFlag'] = 0
                    except:
                        v['TempMin'] = None
                        v['TempMinFlag'] = -1
            elif j == 8:
                if col.text() == '×':
                    v['RHAve'] = None
                    v['RHAveFlag'] = 9
                elif col.text() == '':
                    v['RHAve'] = None
                    v['RHAveFlag'] = None
                else:
                    try:
                        v['RHAve'] = float(col.text())
                        v['RHAveFlag'] = 0
                    except:
                        v['RHAve'] = None
                        v['RHAveFlag'] = -1
            elif j == 9:
                if col.text() == '×':
                    v['RHMin'] = None
                    v['RHMinFlag'] = 9
                elif col.text() == '':
                    v['RHMin'] = None
                    v['RHMinFlag'] = None
                else:
                    try:
                        v['RHMin'] = float(col.text())
                        v['RHMinFlag'] = 0
                    except:
                        v['RHMin'] = None
                        v['RHMinFlag'] = -1
            elif j == 10:
                if col.text() == '×':
                    v['WindSpeedAve'] = None
                    v['WindSpeedAveFlag'] = 9
                elif col.text() == '':
                    v['WindSpeedAve'] = None
                    v['WindSpeedAveFlag'] = None
                else:
                    try:
                        v['WindSpeedAve'] = float(col.text())
                        v['WindSpeedAveFlag'] = 0
                    except:
                        v['WindSpeedAve'] = None
                        v['WindSpeedAveFlag'] = -1
            elif j == 11:
                if col.text() == '×':
                    v['WindSpeedMax'] = None
                    v['WindSpeedMaxFlag'] = 9
                elif col.text() == '':
                    v['WindSpeedMax'] = None
                    v['WindSpeedMaxFlag'] = None
                else:
                    try:
                        v['WindSpeedMax'] = float(col.text())
                        v['WindSpeedMaxFlag'] = 0
                    except:
                        v['WindSpeedMax'] = None
                        v['WindSpeedMaxFlag'] = -1
            elif j == 12:
                if col.text() == '×':
                    v['WindDirectionMax'] = None
                    v['WindDirectionMaxFlag'] = 9
                elif col.text() == '':
                    v['WindDirectionMax'] = None
                    v['WindDirectionMaxFlag'] = None
                else:
                    try:
                        v['WindDirectionMax'] = changeWD(col.text())
                        v['WindDirectionMaxFlag'] = 0
                    except:
                        v['WindDirectionMax'] = None
                        v['WindDirectionMaxFlag'] = -1
            elif j == 13:
                if col.text() == '×':
                    v['WindSpeedInst'] = None
                    v['WindSpeedInstFlag'] = 9
                elif col.text() == '':
                    v['WindSpeedInst'] = None
                    v['WindSpeedInstFlag'] = None
                else:
                    try:
                        v['WindSpeedInst'] = float(col.text())
                        v['WindSpeedInstFlag'] = 0
                    except:
                        v['WindSpeedInst'] = None
                        v['WindSpeedInstFlag'] = -1
            elif j == 14:
                if col.text() == '×':
                    v['WindDirectionInst'] = None
                    v['WindDirectionInstFlag'] = 9
                elif col.text() == '':
                    v['WindDirectionInst'] = None
                    v['WindDirectionInstFlag'] = None
                else:
                    try:
                        v['WindDirectionInst'] = changeWD(col.text())
                        v['WindDirectionInstFlag'] = 0
                    except:
                        v['WindDirectionInst'] = None
                        v['WindDirectionInstFlag'] = -1
            elif j == 15:
                if col.text() == '×':
                    v['SunDuration'] = None
                    v['SunDurationFlag'] = 9
                elif col.text() == '':
                    v['SunDuration'] = None
                    v['SunDurationFlag'] = None
                else:
                    try:
                        v['SunDuration'] = float(col.text())
                        v['SunDurationFlag'] = 0
                    except:
                        v['SunDuration'] = None
                        v['SunDurationFlag'] = -1
            elif j == 16:
                if col.text() == '×':
                    v['Snowfall'] = None
                    v['SnowfallFlag'] = 9
                elif col.text() == '':
                    v['Snowfall'] = None
                    v['SnowfallFlag'] = None
                else:
                    try:
                        v['Snowfall'] = float(col.text())
                        v['SnowfallFlag'] = 0
                    except:
                        v['Snowfall'] = None
                        v['SnowfallFlag'] = -1
            elif j == 17:
                if col.text() == '×':
                    v['SnowDepth'] = None
                    v['SnowDepthFlag'] = 9
                elif col.text() == '':
                    v['SnowDepth'] = None
                    v['SnowDepthFlag'] = None
                else:
                    try:
                        v['SnowDepth'] = float(col.text())
                        v['SnowDepthFlag'] = 0
                    except:
                        v['SnowDepth'] = None
                        v['SnowDepthFlag'] = -1
            elif j == 18:
                if col.text() == '×':
                    v['Weather1'] = None
                    v['Weather1Flag'] = 9
                else:
                    wx = col.text()
                    if wx is None:
                        v['Weather1'] = None
                        v['Weather1Flag'] = None
                    else:
                        v['Weather1'] = wx
                        v['Weather1Flag'] = 0
            elif j == 19:
                if col.text() == '×':
                    v['Weather2'] = None
                    v['Weather2Flag'] = 9
                else:
                    wx = col.text()
                    if wx is None:
                        v['Weather2'] = None
                        v['Weather2Flag'] = None
                    else:
                        v['Weather2'] = wx
                        v['Weather2Flag'] = 0

        ret.append(v)
    return ret
    

def getObsData(station, db, obs_date):
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        for s in station:
            logger.debug('Getting {Name}'.format(**s))
            data = {
                'prec_no': s['Block'],
                'block_no': s['Station'],
                'year': obs_date.year,
                'month': obs_date.month,
            }
            req = requests.get(URLBase, params=data)
            req.encoding = 'utf-8'

            ds = parseData(req.text, datetime.datetime(year=obs_date.year, month=obs_date.month, day=obs_date.day))
            for d in ds:
                d['station'] = s['Station']
                sql = '''
                INSERT OR REPLACE INTO JMAObsDaily (
                  StationID, Date,
                  StationPress, StationPressFlag, MSL, MSLFlag, Prec, PrecFlag, PrecMax1hour, PrecMax1hourFlag, PrecMax10min, PrecMax10minFlag,
                  TempAve, TempAveFlag, TempMax, TempMaxFlag, TempMin, TempMinFlag, RHAve, RHAveFlag, RHMin, RHMinFlag,
                  WindSpeedAve, WindSpeedAveFlag, WindSpeedMax, WindSpeedMaxFlag, WindDirectionMax, WindDirectionMaxFlag,
                  WindSpeedInst, WindSpeedInstFlag, WindDirectionInst, WindDirectionInstFlag,
                  SunDuration, SunDurationFlag, SnowFall, SnowFallFlag, SnowDepth, SnowDepthFlag,
                  Weather1, Weather1Flag, Weather2, Weather2Flag)
                VALUES (
                  ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                );
                '''
                cur.execute(sql, (
                    d['station'], d['date'],
                    d['StationPress'], d['StationPressFlag'], d['MSL'], d['MSLFlag'], d['Prec'], d['PrecFlag'], d['PrecMax1hour'], d['PrecMax1hourFlag'], d['PrecMax10min'], d['PrecMax10minFlag'],
                    d['TempAve'], d['TempAveFlag'], d['TempMax'], d['TempMaxFlag'], d['TempMin'], d['TempMinFlag'], d['RHAve'], d['RHAveFlag'], d['RHMin'], d['RHMinFlag'],
                    d['WindSpeedAve'], d['WindSpeedAveFlag'], d['WindSpeedMax'], d['WindSpeedMaxFlag'], d['WindDirectionMax'], d['WindDirectionMaxFlag'],
                    d['WindSpeedInst'], d['WindSpeedInstFlag'], d['WindDirectionInst'], d['WindDirectionInstFlag'],
                    d['SunDuration'], d['SunDurationFlag'], d['Snowfall'], d['SnowfallFlag'], d['SnowDepth'], d['SnowDepthFlag'],
                    d['Weather1'], d['Weather1Flag'], d['Weather2'], d['Weather2Flag'] ))
            con.commit()
            time.sleep(0.5)

            
def createDB(db):
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        
        sql = '''
        CREATE TABLE IF NOT EXISTS JMAObsDaily (
          StationID TEXT NOT NULL,
          Date date NOT NULL,
          StationPress FLOAT DEFAULT NULL,
          StationPressFlag INTEGER DEFAULT NULL,
          MSL FLOAT DEFAULT NULL,
          MSLFlag INT DEFAULT NULL,
          Prec FLOAT DEFAULT NULL,
          PrecFlag INT DEFAULT NULL,
          PrecMax1hour FLOAT DEFAULT NULL,
          PrecMax1hourFlag INT DEFAULT NULL,
          PrecMax10min FLOAT DEFAULT NULL,
          PrecMax10minFlag INT DEFAULT NULL,
          TempAve FLOAT DEFAULT NULL,
          TempAveFlag INT DEFAULT NULL,
          TempMax FLOAT DEFAULT NULL,
          TempMaxFlag INT DEFAULT NULL,
          TempMin FLOAT DEFAULT NULL,
          TempMinFlag INT DEFAULT NULL,
          RHAve FLOAT DEFAULT NULL,
          RHAveFlag INT DEFAULT NULL,
          RHMin FLOAT DEFAULT NULL,
          RHMinFlag INT DEFAULT NULL,
          WindSpeedAve FLOAT DEFAULT NULL,
          WindSpeedAveFlag INT DEFAULT NULL,
          WindSpeedMax FLOAT DEFAULT NULL,
          WindSpeedMaxFlag INT DEFAULT NULL,
          WindDirectionMax INT DEFAULT NULL,
          WindDirectionMaxFlag INT DEFAULT NULL,
          WindSpeedInst FLOAT DEFAULT NULL,
          WindSpeedInstFlag INT DEFAULT NULL,
          WindDirectionInst INT DEFAULT NULL,
          WindDirectionInstFlag INT DEFAULT NULL,
          SunDuration FLOAT DEFAULT NULL,
          SunDurationFlag INT DEFAULT NULL,
          SnowFall FLOAT DEFAULT NULL,
          SnowFallFlag INT DEFAULT NULL,
          SnowDepth FLOAT DEFAULT NULL,
          SnowDepthFlag INT DEFAULT NULL,
          Weather1 TEXT DEFAULT NULL,
          Weather1Flag INT DEFAULT NULL,
          Weather2 TEXT DEFAULT NULL,
          Weather2Flag INT DEFAULT NULL,
          UNIQUE (StationID, Date)
        );
        '''
    
    cur.execute(sql)
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JMA Obs Daily Getter')
    parser.add_argument('station_db', metavar='S_DB', type=str, help='Station Database')
    parser.add_argument('db', metavar='DB', type=str, help='Database')
    parser.add_argument('-t', '--target', metavar='DATE', type=str, help='Target Date YYYYMM')
    
    args = parser.parse_args()
    init_slack()

    if args.target is None:
        target = datetime.date.today() - datetime.timedelta(days=1)
    else:
        target = datetime.datetime.strptime(args.target, '%Y%m')
        target = datetime.date(year=target.year, month=target.month, day=1)

    logger.info('Obs Dailyの取得を開始しました。')
    createDB(args.db)
    stn = getStation(args.station_db)
    getObsData(stn, args.db, target)
    logger.info('Obs Dailyの取得を完了しました。')
    

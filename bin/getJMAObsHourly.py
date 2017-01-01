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
URLBase = 'http://www.data.jma.go.jp/obd/stats/etrn/view/hourly_s1.php'

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
        if i < 2:
            continue
        hour = i - 1
        if hour == 24:
            obs += datetime.timedelta(days=1)
            obs = obs.replace(hour=0)
        else:
            obs = obs.replace(hour=hour)

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
                if col.text() == '×':
                    v['Temp'] = None
                    v['TempFlag'] = 9
                elif col.text() == '':
                    v['Temp'] = None
                    v['TempFlag'] = None
                else:
                    try:
                        v['Temp'] = float(col.text())
                        v['TempFlag'] = 0
                    except:
                        v['Temp'] = None
                        v['TempFlag'] = -1
            elif j == 4:
                if col.text() == '×':
                    v['TD'] = None
                    v['TDFlag'] = 9
                elif col.text() == '':
                    v['TD'] = None
                    v['TDFlag'] = None
                else:
                    try:
                        v['TD'] = float(col.text())
                        v['TDFlag'] = 0
                    except:
                        v['TD'] = None
                        v['TDFlag'] = -1
            elif j == 5:
                if col.text() == '×':
                    v['WaterPress'] = None
                    v['WaterPressFlag'] = 9
                elif col.text() == '':
                    v['WaterPress'] = None
                    v['WaterPressFlag'] = None
                else:
                    try:
                        v['WaterPress'] = float(col.text())
                        v['WaterPressFlag'] = 0
                    except:
                        v['WaterPress'] = None
                        v['WaterPressFlag'] = -1
            elif j == 6:
                if col.text() == '×':
                    v['RH'] = None
                    v['RHFlag'] = 9
                elif col.text() == '':
                    v['RH'] = None
                    v['RHFlag'] = None
                else:
                    try:
                        v['RH'] = float(col.text())
                        v['RHFlag'] = 0
                    except:
                        v['RH'] = None
                        v['RHFlag'] = -1
            elif j == 7:
                if col.text() == '×':
                    v['WindSpeed'] = None
                    v['WindSpeedFlag'] = 9
                elif col.text() == '':
                    v['WindSpeed'] = None
                    v['WindSpeedFlag'] = None
                else:
                    try:
                        v['WindSpeed'] = float(col.text())
                        v['WindSpeedFlag'] = 0
                    except:
                        v['WindSpeed'] = None
                        v['WindSpeedFlag'] = -1
            elif j == 8:
                if col.text() == '×':
                    v['WindDirection'] = None
                    v['WindDirectionFlag'] = 9
                elif col.text() == '':
                    v['WindDirection'] = None
                    v['WindDirectionFlag'] = None
                else:
                    try:
                        v['WindDirection'] = changeWD(col.text())
                        v['WindDirectionFlag'] = 0
                    except:
                        v['WindDirection'] = None
                        v['WindDirectionFlag'] = -1
            elif j == 9:
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
            elif j == 10:
                if col.text() == '×':
                    v['Radiation'] = None
                    v['RadiationFlag'] = 9
                elif col.text() == '':
                    v['Radiation'] = None
                    v['RadiationFlag'] = None
                else:
                    try:
                        v['Radiation'] = float(col.text())
                        v['RadiationFlag'] = 0
                    except:
                        v['Radiation'] = None
                        v['RadiationFlag'] = -1
            elif j == 11:
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
            elif j == 12:
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
            elif j == 13:
                if col.text() == '×':
                    v['Weather'] = None
                    v['WeatherFlag'] = 9
                else:
                    i = col('td img')
                    wx = i.attr('alt')
                    if wx is None:
                        v['Weather'] = None
                        v['WeatherFlag'] = None
                    else:
                        v['Weather'] = wx
                        v['WeatherFlag'] = 0
            elif j == 14:
                if col.text() == '×':
                    v['CloudAmount'] = None
                    v['CloudAmountFlag'] = 9
                elif col.text() == '':
                    v['CloudAmount'] = None
                    v['CloudAmountFlag'] = None
                else:
                    try:
                        v['CloudAmount'] = col.text()
                        v['CloudAmountFlag'] = 0
                    except:
                        v['CloudAmount'] = None
                        v['CloudAmountFlag'] = -1
            elif j == 15:
                if col.text() == '×':
                    v['Visibility'] = None
                    v['VisibilityFlag'] = 9
                elif col.text() == '':
                    v['Visibility'] = None
                    v['VisibilityFlag'] = None
                else:
                    try:
                        v['Visibility'] = float(col.text())
                        v['VisibilityFlag'] = 0
                    except:
                        v['Visibility'] = None
                        v['VisibilityFlag'] = -1
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
                'day': obs_date.day,
            }
            req = requests.get(URLBase, params=data)
            req.encoding = 'utf-8'

            ds = parseData(req.text, datetime.datetime(year=obs_date.year, month=obs_date.month, day=obs_date.day))
            for d in ds:
                d['station'] = s['Station']
                sql = '''
                INSERT OR REPLACE INTO JMAObsHourly (
                  StationID, Date,
                  StationPress, StationPressFlag, MSL, MSLFlag, Prec, PrecFlag, Temp, TempFlag, DewPoint, DewPointFlag,
                  WaterVaporPress, WaterVaporPressFlag, RH, RHFlag, WindSpeed, WindSpeedFlag, WindDirection, WindDirectionFlag,
                  SunDuration, SunDurationFlag, SunRadiation, SunRadiationFlag, SnowFall, SnowFallFlag, SnowDepth, SnowDepthFlag,
                  Weather, WeatherFlag, CloudAmount, CloudAmountFlag, Visibility, VisibilityFlag)
                VALUES (
                  ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?
                );
                '''
                cur.execute(sql, (
                    d['station'], d['date'],
                    d['StationPress'], d['StationPressFlag'], d['MSL'], d['MSLFlag'], d['Prec'], d['PrecFlag'], d['Temp'], d['TempFlag'], d['TD'], d['TDFlag'],
                    d['WaterPress'], d['WaterPressFlag'], d['RH'], d['RHFlag'], d['WindSpeed'], d['WindSpeedFlag'], d['WindDirection'], d['WindDirectionFlag'],
                    d['SunDuration'], d['SunDurationFlag'], d['Radiation'], d['RadiationFlag'], d['Snowfall'], d['SnowfallFlag'], d['SnowDepth'], d['SnowDepthFlag'],
                    d['Weather'], d['WeatherFlag'], d['CloudAmount'], d['CloudAmountFlag'], d['Visibility'], d['VisibilityFlag']))
            con.commit()
            time.sleep(0.5)

            
def createDB(db):
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        
        sql = '''
        CREATE TABLE IF NOT EXISTS JMAObsHourly (
          StationID TEXT NOT NULL,
          Date date NOT NULL,
          StationPress FLOAT DEFAULT NULL,
          StationPressFlag INTEGER DEFAULT NULL,
          MSL FLOAT DEFAULT NULL,
          MSLFlag INT DEFAULT NULL,
          Prec FLOAT DEFAULT NULL,
          PrecFlag INT DEFAULT NULL,
          Temp FLOAT DEFAULT NULL,
          TempFlag INT DEFAULT NULL,
          DewPoint FLOAT DEFAULT NULL,
          DewPointFlag INT DEFAULT NULL,
          WaterVaporPress FLOAT DEFAULT NULL,
          WaterVaporPressFlag INT DEFAULT NULL,
          RH FLOAT DEFAULT NULL,
          RHFlag INT DEFAULT NULL,
          WindSpeed FLOAT DEFAULT NULL,
          WindSpeedFlag INT DEFAULT NULL,
          WindDirection INT DEFAULT NULL,
          WindDirectionFlag INT DEFAULT NULL,
          SunDuration FLOAT DEFAULT NULL,
          SunDurationFlag INT DEFAULT NULL,
          SunRadiation FLOAT DEFAULT NULL,
          SunRadiationFlag INT DEFAULT NULL,
          SnowFall FLOAT DEFAULT NULL,
          SnowFallFlag INT DEFAULT NULL,
          SnowDepth FLOAT DEFAULT NULL,
          SnowDepthFlag INT DEFAULT NULL,
          Weather TEXT DEFAULT NULL,
          WeatherFlag INT DEFAULT NULL,
          CloudAmount TEXT DEFAULT NULL,
          CloudAmountFlag INT DEFAULT NULL,
          Visibility FLOAT DEFAULT NULL,
          VisibilityFlag INT DEFAULT NULL,
          UNIQUE (StationID, Date)
        );
        '''
    
    cur.execute(sql)
        
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JMA Obs Hourly Getter')
    parser.add_argument('station_db', metavar='S_DB', type=str, help='Station Database')
    parser.add_argument('db', metavar='DB', type=str, help='Database')
    parser.add_argument('-t', '--target', metavar='DATE', type=str, help='Target Date YYYYMMDD')
    
    args = parser.parse_args()
    init_slack()

    if args.target is None:
        target = datetime.date.today() - datetime.timedelta(days=1)
    else:
        target = datetime.datetime.strptime(args.target, '%Y%m%d')
        target = datetime.date(year=target.year, month=target.month, day=target.day)

    logger.info('Obs Hourlyの取得を開始しました。')
    createDB(args.db)
    stn = getStation(args.station_db)
    getObsData(stn, args.db, target)
    logger.info('Obs Hourlyの取得を完了しました。')
    

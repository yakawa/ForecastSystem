#!/usr/bin/env python3
import os
import datetime
import json
import logging
import argparse
import sqlite3

from slack_log_handler import SlackLogHandler

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)

HOME = os.path.expanduser('~')
TMPDIR = HOME + '/ForecastSystem/tmp/'

FILE1 = TMPDIR + '0000-0312_surf.dat'
FILE2 = TMPDIR + '0000-0312_pall.dat'
FILE3 = TMPDIR + '0000-0312_add.dat'
FILE4 = TMPDIR + '0315-0800_surf.dat'
FILE5 = TMPDIR + '0318-0800_pall.dat'
FILE6 = TMPDIR + '0318-0800_add.dat'
FILE7 = TMPDIR + '0803-1100_surf.dat'
FILE8 = TMPDIR + '0806-1100_pall.dat'
FILE9 = TMPDIR + '0806-1100_add.dat'

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

def readData(init):
    ret = {}
    with open(FILE1, 'r') as f:
        for l in f:
            l = l.strip()
            w = l.split('\t')
            vals = {}
            for v in w:
                vv = v.split(':')
                if vv[0] == 'FT':
                    vv[1] = int(vv[1].strip())
                elif vv[0] == 'Station':
                    vv[1] = str(vv[1].strip())
                else:
                    vv[1] = float(vv[1].strip())
                vals[vv[0]] = vv[1]
            if vals['Station'] not in ret:
                ret[vals['Station']] = {}
            if vals['FT'] not in ret:
                ret[vals['Station']][vals['FT']] = {}
            for v in vals:
                if v == 'Station' or v == 'FT':
                    continue
                ret[vals['Station']][vals['FT']][v] = vals[v]
    with open(FILE2, 'r') as f:
        for l in f:
            l = l.strip()
            w = l.split('\t')
            vals = {}
            for v in w:
                vv = v.split(':')
                if vv[0] == 'FT':
                    vv[1] = int(vv[1].strip())
                elif vv[0] == 'Station':
                    vv[1] = str(vv[1].strip())
                else:
                    vv[1] = float(vv[1].strip())
                vals[vv[0]] = vv[1]
            for v in vals:
                if v == 'Station' or v == 'FT':
                    continue
                ret[vals['Station']][vals['FT']][v] = vals[v]
    with open(FILE3, 'r') as f:
        for l in f:
            l = l.strip()
            w = l.split('\t')
            vals = {}
            for v in w:
                vv = v.split(':')
                if vv[0] == 'FT':
                    vv[1] = int(vv[1].strip())
                elif vv[0] == 'Station':
                    vv[1] = str(vv[1].strip())
                else:
                    vv[1] = float(vv[1].strip())
                vals[vv[0]] = vv[1]
            for v in vals:
                if v == 'Station' or v == 'FT':
                    continue
                ret[vals['Station']][vals['FT']][v] = vals[v]
    if init.hour != 12:
        return ret
    with open(FILE4, 'r') as f:
        for l in f:
            l = l.strip()
            w = l.split('\t')
            vals = {}
            for v in w:
                vv = v.split(':')
                if vv[0] == 'FT':
                    vv[1] = int(vv[1].strip())
                elif vv[0] == 'Station':
                    vv[1] = str(vv[1].strip())
                else:
                    vv[1] = float(vv[1].strip())
                vals[vv[0]] = vv[1]
            if vals['FT'] not in ret:
                ret[vals['Station']][vals['FT']] = {}
            for v in vals:
                if v == 'Station' or v == 'FT':
                    continue
                ret[vals['Station']][vals['FT']][v] = vals[v]
    with open(FILE5, 'r') as f:
        for l in f:
            l = l.strip()
            w = l.split('\t')
            vals = {}
            for v in w:
                vv = v.split(':')
                if vv[0] == 'FT':
                    vv[1] = int(vv[1].strip())
                elif vv[0] == 'Station':
                    vv[1] = str(vv[1].strip())
                else:
                    vv[1] = float(vv[1].strip())
                vals[vv[0]] = vv[1]
            for v in vals:
                if v == 'Station' or v == 'FT':
                    continue
                ret[vals['Station']][vals['FT']][v] = vals[v]
    with open(FILE6, 'r') as f:
        for l in f:
            l = l.strip()
            w = l.split('\t')
            vals = {}
            for v in w:
                vv = v.split(':')
                if vv[0] == 'FT':
                    vv[1] = int(vv[1].strip())
                elif vv[0] == 'Station':
                    vv[1] = str(vv[1].strip())
                else:
                    vv[1] = float(vv[1].strip())
                vals[vv[0]] = vv[1]
            for v in vals:
                if v == 'Station' or v == 'FT':
                    continue
                ret[vals['Station']][vals['FT']][v] = vals[v]
    with open(FILE7, 'r') as f:
        for l in f:
            l = l.strip()
            w = l.split('\t')
            vals = {}
            for v in w:
                vv = v.split(':')
                if vv[0] == 'FT':
                    vv[1] = int(vv[1].strip())
                elif vv[0] == 'Station':
                    vv[1] = str(vv[1].strip())
                else:
                    vv[1] = float(vv[1].strip())
                vals[vv[0]] = vv[1]
            if vals['FT'] not in ret:
                ret[vals['Station']][vals['FT']] = {}
            for v in vals:
                if v == 'Station' or v == 'FT':
                    continue
                ret[vals['Station']][vals['FT']][v] = vals[v]
    with open(FILE8, 'r') as f:
        for l in f:
            l = l.strip()
            w = l.split('\t')
            vals = {}
            for v in w:
                vv = v.split(':')
                if vv[0] == 'FT':
                    vv[1] = int(vv[1].strip())
                elif vv[0] == 'Station':
                    vv[1] = str(vv[1].strip())
                else:
                    vv[1] = float(vv[1].strip())
                vals[vv[0]] = vv[1]
            for v in vals:
                if v == 'Station' or v == 'FT':
                    continue
                ret[vals['Station']][vals['FT']][v] = vals[v]
    with open(FILE9, 'r') as f:
        for l in f:
            l = l.strip()
            w = l.split('\t')
            vals = {}
            for v in w:
                vv = v.split(':')
                if vv[0] == 'FT':
                    vv[1] = int(vv[1].strip())
                elif vv[0] == 'Station':
                    vv[1] = str(vv[1].strip())
                else:
                    vv[1] = float(vv[1].strip())
                vals[vv[0]] = vv[1]
            for v in vals:
                if v == 'Station' or v == 'FT':
                    continue
                ret[vals['Station']][vals['FT']][v] = vals[v]
    return ret

def saveDB(init, db, vals):
    with sqlite3.connect(db) as con:
        cur = con.cursor()
        for station in vals:
            for ft in sorted(vals[station]):
                if ft == 0:
                    prec = 0
                elif ft == 1:
                    prec = vals[station][ft]['APCP']
                elif ft <= 84:
                    prec = vals[station][ft]['APCP'] - vals[station][ft - 1]['APCP']
                    if prec < 0:
                        prec = 0
                else:
                    prec = vals[station][ft]['APCP'] - vals[station][ft - 3]['APCP']
                    if prec < 0:
                        prec = 0
                if (ft <= 84 and ft % 3 == 0) or (ft > 84 and ft % 6 == 0):
                    sql = '''
                    INSERT OR REPLACE INTO GSMFcst(
                      Station, init, ft,
                      msl, press, uwind, vwind, temp, rh, lcld, mcld, hcld, tcld, prec,
                      ssi, ssi850_700, ssi925_850, ept_850, td_850, td_700,
                      h_1000, uwind_1000, vwind_1000, t_1000, wwind_1000, rh_1000,
                      h_975,  uwind_975,  vwind_975,  t_975,  wwind_975,  rh_975,
                      h_950,  uwind_950,  vwind_950,  t_950,  wwind_950,  rh_950,
                      h_925,  uwind_925,  vwind_925,  t_925,  wwind_925,  rh_925,
                      h_900,  uwind_900,  vwind_900,  t_900,  wwind_900,  rh_900,
                      h_850,  uwind_850,  vwind_850,  t_850,  wwind_850,  rh_850,
                      h_800,  uwind_800,  vwind_800,  t_800,  wwind_800,  rh_800,
                      h_700,  uwind_700,  vwind_700,  t_700,  wwind_700,  rh_700,
                      h_600,  uwind_600,  vwind_600,  t_600,  wwind_600,  rh_600,
                      h_500,  uwind_500,  vwind_500,  t_500,  wwind_500,  rh_500,
                      h_400,  uwind_400,  vwind_400,  t_400,  wwind_400,  rh_400,
                      h_300,  uwind_300,  vwind_300,  t_300,  wwind_300,  rh_300,
                      h_250,  uwind_250,  vwind_250,  t_250,  wwind_250,
                      h_200,  uwind_200,  vwind_200,  t_200,  wwind_200,
                      h_150,  uwind_150,  vwind_150,  t_150,  wwind_150,
                      h_100,  uwind_100,  vwind_100,  t_100,  wwind_100        
                    ) VALUES (
                     ?, ?, ?,
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?,
                     ?, ?, ?, ?, ?
                    );
                    '''
                    cur.execute(sql, (
                        station, init, ft,
                        vals[station][ft]['MSL'], vals[station][ft]['PRESS'], vals[station][ft]['U10'], vals[station][ft]['V10'], vals[station][ft]['TEMP'], vals[station][ft]['RH'], vals[station][ft]['LCLD'], vals[station][ft]['MCLD'], vals[station][ft]['HCLD'], vals[station][ft]['TCLD'], prec,
                        vals[station][ft]['SSI'], vals[station][ft]['SSI850_700'], vals[station][ft]['SSI925_850'], vals[station][ft]['EPT'], vals[station][ft]['TD850'], vals[station][ft]['TD700'],
                        vals[station][ft]['H1000'], vals[station][ft]['U1000'], vals[station][ft]['V1000'], vals[station][ft]['T1000'], vals[station][ft]['W1000'], vals[station][ft]['RH1000'],
                        vals[station][ft]['H975'], vals[station][ft]['U975'], vals[station][ft]['V975'], vals[station][ft]['T975'], vals[station][ft]['W975'], vals[station][ft]['RH975'],
                        vals[station][ft]['H950'], vals[station][ft]['U950'], vals[station][ft]['V950'], vals[station][ft]['T950'], vals[station][ft]['W950'], vals[station][ft]['RH950'],
                        vals[station][ft]['H925'], vals[station][ft]['U925'], vals[station][ft]['V925'], vals[station][ft]['T925'], vals[station][ft]['W925'], vals[station][ft]['RH925'],
                        vals[station][ft]['H900'], vals[station][ft]['U900'], vals[station][ft]['V900'], vals[station][ft]['T900'], vals[station][ft]['W900'], vals[station][ft]['RH900'],
                        vals[station][ft]['H850'], vals[station][ft]['U850'], vals[station][ft]['V850'], vals[station][ft]['T850'], vals[station][ft]['W850'], vals[station][ft]['RH850'],
                        vals[station][ft]['H800'], vals[station][ft]['U800'], vals[station][ft]['V800'], vals[station][ft]['T800'], vals[station][ft]['W800'], vals[station][ft]['RH800'],
                        vals[station][ft]['H700'], vals[station][ft]['U700'], vals[station][ft]['V700'], vals[station][ft]['T700'], vals[station][ft]['W700'], vals[station][ft]['RH700'],
                        vals[station][ft]['H600'], vals[station][ft]['U600'], vals[station][ft]['V600'], vals[station][ft]['T600'], vals[station][ft]['W600'], vals[station][ft]['RH600'],
                        vals[station][ft]['H500'], vals[station][ft]['U500'], vals[station][ft]['V500'], vals[station][ft]['T500'], vals[station][ft]['W500'], vals[station][ft]['RH500'],
                        vals[station][ft]['H400'], vals[station][ft]['U400'], vals[station][ft]['V400'], vals[station][ft]['T400'], vals[station][ft]['W400'], vals[station][ft]['RH400'],
                        vals[station][ft]['H300'], vals[station][ft]['U300'], vals[station][ft]['V300'], vals[station][ft]['T300'], vals[station][ft]['W300'], vals[station][ft]['RH300'],
                        vals[station][ft]['H250'], vals[station][ft]['U250'], vals[station][ft]['V250'], vals[station][ft]['T250'], vals[station][ft]['W250'],
                        vals[station][ft]['H200'], vals[station][ft]['U200'], vals[station][ft]['V200'], vals[station][ft]['T200'], vals[station][ft]['W200'],
                        vals[station][ft]['H150'], vals[station][ft]['U150'], vals[station][ft]['V150'], vals[station][ft]['T150'], vals[station][ft]['W150'],
                        vals[station][ft]['H100'], vals[station][ft]['U100'], vals[station][ft]['V100'], vals[station][ft]['T100'], vals[station][ft]['W100']))
                else:
                    sql = '''
                    INSERT OR REPLACE INTO GSMFcst(
                      Station, init, ft,
                      msl, press, uwind, vwind, temp, rh, lcld, mcld, hcld, tcld, prec,
                      ssi, ssi850_700, ssi925_850, ept_850, td_850, td_700,
                      h_1000, uwind_1000, vwind_1000, t_1000, wwind_1000, rh_1000,
                      h_975,  uwind_975,  vwind_975,  t_975,  wwind_975,  rh_975,
                      h_950,  uwind_950,  vwind_950,  t_950,  wwind_950,  rh_950,
                      h_925,  uwind_925,  vwind_925,  t_925,  wwind_925,  rh_925,
                      h_900,  uwind_900,  vwind_900,  t_900,  wwind_900,  rh_900,
                      h_850,  uwind_850,  vwind_850,  t_850,  wwind_850,  rh_850,
                      h_800,  uwind_800,  vwind_800,  t_800,  wwind_800,  rh_800,
                      h_700,  uwind_700,  vwind_700,  t_700,  wwind_700,  rh_700,
                      h_600,  uwind_600,  vwind_600,  t_600,  wwind_600,  rh_600,
                      h_500,  uwind_500,  vwind_500,  t_500,  wwind_500,  rh_500,
                      h_400,  uwind_400,  vwind_400,  t_400,  wwind_400,  rh_400,
                      h_300,  uwind_300,  vwind_300,  t_300,  wwind_300,  rh_300,
                      h_250,  uwind_250,  vwind_250,  t_250,  wwind_250,
                      h_200,  uwind_200,  vwind_200,  t_200,  wwind_200,
                      h_150,  uwind_150,  vwind_150,  t_150,  wwind_150,
                      h_100,  uwind_100,  vwind_100,  t_100,  wwind_100        
                    ) VALUES (
                     ?, ?, ?,
                     ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL,
                     NULL, NULL, NULL, NULL, NULL
                    );
                    '''
                    cur.execute(sql, (
                        station, init, ft,
                        vals[station][ft]['MSL'], vals[station][ft]['PRESS'], vals[station][ft]['U10'], vals[station][ft]['V10'], vals[station][ft]['TEMP'], vals[station][ft]['RH'], vals[station][ft]['LCLD'], vals[station][ft]['MCLD'], vals[station][ft]['HCLD'], vals[station][ft]['TCLD'], prec
                    ))
        con.commit()
            


    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GFS Getter')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time')
    parser.add_argument('db', metavar='DB', type=str, help="DB")

    args = parser.parse_args()
    
    #init_slack()
    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    
    r = readData(init)
    saveDB(init, args.db, r)

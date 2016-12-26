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
OUTPUTDIR = HOME + '/WRF/DATA/output/{}/'

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

def saveDB(init, db):
    fn = OUTPUTDIR.format(init.strftime('%Y%m%d_%H0000')) + '/station.dat'
    with open(fn, 'r') as f:
        with sqlite3.connect(db) as con:
            cur = con.cursor()
            
            for l in f:
                l = l.strip()
                w = l.split('\t')
                vals = {}
                for v in w:
                    vv = v.split(':')
                    if vv[0] == 'FT':
                        vals[vv[0].strip()] = int(vv[1].strip())
                    elif vv[0] == 'Station':
                        vals[vv[0].strip()] = str(vv[1].strip())
                    else:
                        if vv[0] in vals:
                            vals['QC100'] = float(vv[1].strip())
                        else:
                            vals[vv[0].strip()] = float(vv[1].strip())

                sql = '''
                INSERT OR REPLACE INTO WRFFcst (
                  Station, init, ft,
                  t2, td2, rh2, u10, v10, tpw, ssi, ssi700_500, ssi925_850, 
                  sdown, rain_c, rain_rc, rain_nc, rain_rnc, cld_lo, cld_mo, cld_hi,
                  msl, cape, cin, lcl, lfc, dbz,
                  uwind_1000, uwind_925, uwind_900, uwind_850, uwind_800, uwind_700, uwind_600, uwind_500, uwind_400, uwind_300, uwind_200, uwind_100,
                  vwind_1000, vwind_925, vwind_900, vwind_850, vwind_800, vwind_700, vwind_600, vwind_500, vwind_400, vwind_300, vwind_200, vwind_100,
                  wwind_1000, wwind_925, wwind_900, wwind_850, wwind_800, wwind_700, wwind_600, wwind_500, wwind_400, wwind_300, wwind_200, wwind_100,
                  temp_1000, temp_925, temp_900, temp_850, temp_800, temp_700, temp_600, temp_500, temp_400, temp_300, temp_200, temp_100,
                  td_1000, td_925, td_900, td_850, td_800, td_700, td_600, td_500, td_400, td_300, td_200, td_100,
                  rh_1000, rh_925, rh_900, rh_850, rh_800, rh_700, rh_600, rh_500, rh_400, rh_300, rh_200, rh_100,
                  qv_1000, qv_925, qv_900, qv_850, qv_800, qv_700, qv_600, qv_500, qv_400, qv_300, qv_200, qv_100,
                  th_1000, th_925, th_900, th_850, th_800, th_700, th_600, th_500, th_400, th_300, th_200, th_100,
                  qc_1000, qc_925, qc_900, qc_850, qc_800, qc_700, qc_600, qc_500, qc_400, qc_300, qc_200, qc_100,
                  qr_1000, qr_925, qr_900, qr_850, qr_800, qr_700, qr_600, qr_500, qr_400, qr_300, qr_200, qr_100,
                  ept_1000, ept_925, ept_900, ept_850, ept_800, ept_700, ept_600, ept_500, ept_400, ept_300, ept_200, ept_100,
                  geoh_1000, geoh_925, geoh_900, geoh_850, geoh_800, geoh_700, geoh_600, geoh_500, geoh_400, geoh_300, geoh_200, geoh_100
                ) VALUES (
                  ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                  ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                );
                '''
                cur.execute(sql, (
                    vals['Station'], init, vals['FT'],
                    vals['T2'] - 273.15, vals['TD2'], vals['RH2'] / 100., vals['U10'], vals['V10'], vals['PW'], vals['SSI'], vals['SSI700_500'], vals['SSI925_850'],
                    vals['SWDOWN'], vals['RAINC'], vals['RAINRC'], vals['RAINNC'], vals['RAINRNC'], vals['CLFLO'], vals['CLFMI'], vals['CLFHI'],
                    vals['SLP'], vals['CAPE'], vals['CIN'], vals['LCL'], vals['LFC'], vals['DBZ'],
                    vals['U1000'], vals['U925'], vals['U900'], vals['U850'], vals['U800'], vals['U700'], vals['U600'], vals['U500'], vals['U400'], vals['U300'], vals['U200'], vals['U100'],
                    vals['V1000'], vals['V925'], vals['V900'], vals['V850'], vals['V800'], vals['V700'], vals['V600'], vals['V500'], vals['V400'], vals['V300'], vals['V200'], vals['V100'],
                    vals['W1000'], vals['W925'], vals['W900'], vals['W850'], vals['W800'], vals['W700'], vals['W600'], vals['W500'], vals['W400'], vals['W300'], vals['W200'], vals['W100'],
                    vals['T1000'], vals['T925'], vals['T900'], vals['T850'], vals['T800'], vals['T700'], vals['T600'], vals['T500'], vals['T400'], vals['T300'], vals['T200'], vals['T100'],
                    vals['TD1000'], vals['TD925'], vals['TD900'], vals['TD850'], vals['TD800'], vals['TD700'], vals['TD600'], vals['TD500'], vals['TD400'], vals['TD300'], vals['TD200'], vals['TD100'],
                    vals['RH1000'] / 100., vals['RH925'] / 100., vals['RH900'] / 100., vals['RH850'] / 100., vals['RH800'] / 100., vals['RH700'] / 100., vals['RH600'] / 100., vals['RH500'] / 100., vals['RH400'] / 100., vals['RH300'] / 100., vals['RH200'] / 100., vals['RH100'] / 100.,
                    vals['QV1000'], vals['QV925'], vals['QV900'], vals['QV850'], vals['QV800'], vals['QV700'], vals['QV600'], vals['QV500'], vals['QV400'], vals['QV300'], vals['QV200'], vals['QV100'],
                    vals['TH1000'], vals['TH925'], vals['TH900'], vals['TH850'], vals['TH800'], vals['TH700'], vals['TH600'], vals['TH500'], vals['TH400'], vals['TH300'], vals['TH200'], vals['TH100'],
                    vals['QC1000'], vals['QC925'], vals['QC900'], vals['QC850'], vals['QC800'], vals['QC700'], vals['QC600'], vals['QC500'], vals['QC400'], vals['QC300'], vals['QC200'], vals['QC100'],
                    vals['QR1000'], vals['QR925'], vals['QR900'], vals['QR850'], vals['QR800'], vals['QR700'], vals['QR600'], vals['QR500'], vals['QR400'], vals['QR300'], vals['QR200'], vals['QR100'],
                    vals['EPT1000'], vals['EPT925'], vals['EPT900'], vals['EPT850'], vals['EPT800'], vals['EPT700'], vals['EPT600'], vals['EPT500'], vals['EPT400'], vals['EPT300'], vals['EPT200'], vals['EPT100'],
                    vals['G1000'] / 9.8, vals['G925'] / 9.8, vals['G900'] / 9.8, vals['G850'] / 9.8, vals['G800'] / 9.8, vals['G700'] / 9.8, vals['G600'] / 9.8, vals['G500'] / 9.8, vals['G400'] / 9.8, vals['G300'] / 9.8, vals['G200'] / 9.8,  vals['G100'] / 9.8
                    ))
                    
            con.commit()

    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GFS Getter')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time')
    parser.add_argument('db', metavar='DB', type=str, help="DB")

    args = parser.parse_args()
    
    #init_slack()
    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    
    saveDB(init, args.db)

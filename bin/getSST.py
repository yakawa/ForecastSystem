#!/usr/bin/env python3
import os
import datetime
import json
import logging
import argparse

import requests
from slack_log_handler import SlackLogHandler

URLBASE = 'http://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/sst.{year:04d}{month:02d}{day:02d}/rtgssthr_grb_0.083.grib2'
HOME = os.path.expanduser('~')
DATADIR =  HOME + '/WRF/DATA/SST/'
FILEBASE = 'gfs.t{hour:02d}z.pgrb2.0p50.f{ft:03d}'

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

def downloader(init):
    dir = DATADIR + init.strftime('%Y%m%d%H')
    if not os.path.isdir(dir):
        os.makedirs(dir)
    fp = dir + '/rtgssthr_grb_0.083.grib2'
    if os.path.isfile(fp):
        return
    url = URLBASE.format(year=init.year, month=init.month, day=init.day)
    res = requests.get(url)
    with open(fp, "wb") as f:
        f.write(res.content)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SST Getter')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time')

    args = parser.parse_args()
    
    init_slack()
    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')

    logger.debug('SST ({})の取得を開始しました。'.format(init.strftime('%Y/%m/%d %H:00:00')))
    downloader(init)
    logger.debug('SSTの取得を終了しました。')

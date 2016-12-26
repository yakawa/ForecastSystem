#!/usr/bin/env python3
import os
import queue
import datetime
import time
from threading import Thread
import json
import logging
import argparse

import requests
from slack_log_handler import SlackLogHandler

URLBASE = 'http://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.{year:02d}{month:02d}{day:02d}{hour:02d}/gfs.t{hour:02d}z.pgrb2.0p50.f{ft:03d}'

HOME = os.path.expanduser('~')
DATADIR =  HOME + '/WRF/DATA/GFS/'
FILEBASE = 'gfs.t{hour:02d}z.pgrb2.0p50.f{ft:03d}'

download_que = queue.Queue()

num_thread = 10

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
    while True:
        ft = download_que.get()
        fp = dir + '/' + FILEBASE.format(year=init.year, month=init.month, day=init.day, hour=init.hour, ft=ft)
        if os.path.isfile(fp):
            logger.debug('FT={}は取得済みです。'.format(ft))
            download_que.task_done()
            continue
        url = URLBASE.format(year=init.year, month=init.month,day=init.day, hour=init.hour, ft=ft)
        try:
            if os.path.exists(fp + '.tmp'):
                os.unlink(fp + '.tmp')

            res = requests.get(url, stream=True, timeout=60)
            if res.status_code == 200 or res.status_code == 206:
                with open(fp + '.tmp', "wb") as f:
                    for chunk in res.iter_content(2 * 1024 * 1024):
                        f.write(chunk)
                os.rename(fp + '.tmp', fp)
            logger.debug('FT={}を取得しました。'.format(ft))
            download_que.task_done()
        except:
            logger.error("GFS FT={} の取得に失敗しました。".format(ft))
            download_que.put(ft)
            time.sleep(60)
            download_que.task_done()
            continue

def make_que(init):
    dir = DATADIR + init.strftime('%Y%m%d%H')
    if not os.path.isdir(dir):
        os.makedirs(dir)

    for ft in range(0, 87, 3):
        download_que.put(ft)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GFS Getter')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time')

    args = parser.parse_args()
    
    init_slack()
    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')

    make_que(init)
    logger.debug('GFS ({})の取得を開始しました。'.format(init.strftime('%Y/%m/%d %H:00:00')))
    for i in range(num_thread):
        worker = Thread(target=downloader, args=(init,))
        worker.setDaemon(True)
        worker.start()
        
    download_que.join()
    logger.debug('GFSの取得を終了しました。')

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

URLBASE = 'http://database.rish.kyoto-u.ac.jp/arch/jmadata/data/gpv/original/{year:04d}/{month:02d}/{day:02d}/'

HOME = os.path.expanduser('~')
DATADIR =  HOME + '/JMA/DATA/GSM/'
FILE1 = 'Z__C_RJTD_{year:04d}{month:02d}{day:02d}{hour:02d}0000_GSM_GPV_Rjp_L-pall_FD0000-0312_grib2.bin'
FILE2 = 'Z__C_RJTD_{year:04d}{month:02d}{day:02d}{hour:02d}0000_GSM_GPV_Rjp_Lsurf_FD0000-0312_grib2.bin'
FILE3 = 'Z__C_RJTD_{year:04d}{month:02d}{day:02d}120000_GSM_GPV_Rjp_L-pall_FD0318-0800_grib2.bin'
FILE4 = 'Z__C_RJTD_{year:04d}{month:02d}{day:02d}120000_GSM_GPV_Rjp_L-pall_FD0806-1100_grib2.bin'
FILE5 = 'Z__C_RJTD_{year:04d}{month:02d}{day:02d}120000_GSM_GPV_Rjp_Lsurf_FD0315-0800_grib2.bin'
FILE6 = 'Z__C_RJTD_{year:04d}{month:02d}{day:02d}120000_GSM_GPV_Rjp_Lsurf_FD0803-1100_grib2.bin'

download_que = queue.Queue()

num_thread = 2

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
        url = download_que.get()
        fp = dir + '/' + url.split('/')[-1]
        if os.path.isfile(fp):
            logger.debug('{}は取得済みです。'.format(url.split('/')[-1]))
            download_que.task_done()
            continue
        try:
            if os.path.exists(fp + '.tmp'):
                os.unlink(fp + '.tmp')

            res = requests.get(url, stream=True, timeout=60)
            if res.status_code == 200 or res.status_code == 206:
                with open(fp + '.tmp', "wb") as f:
                    for chunk in res.iter_content(2 * 1024 * 1024):
                        f.write(chunk)
                os.rename(fp + '.tmp', fp)
            logger.debug('{}を取得しました。'.format(url.split('/')[-1]))
            download_que.task_done()
        except:
            logger.error("{} の取得に失敗しました。".format(url.split('/')[-1]))
            download_que.put(url)
            time.sleep(60)
            download_que.task_done()
            continue

def make_que(init):
    dir = DATADIR + init.strftime('%Y%m%d%H')
    if not os.path.isdir(dir):
        os.makedirs(dir)

    urlb = URLBASE.format(year=init.year, month=init.month, day=init.day)
    download_que.put(urlb + FILE1.format(year=init.year, month=init.month, day=init.day, hour=init.hour))
    download_que.put(urlb + FILE2.format(year=init.year, month=init.month, day=init.day, hour=init.hour))
    if init.hour == 12:
        download_que.put(urlb + FILE3.format(year=init.year, month=init.month, day=init.day, hour=init.hour))
        download_que.put(urlb + FILE4.format(year=init.year, month=init.month, day=init.day, hour=init.hour))
        download_que.put(urlb + FILE5.format(year=init.year, month=init.month, day=init.day, hour=init.hour))
        download_que.put(urlb + FILE6.format(year=init.year, month=init.month, day=init.day, hour=init.hour))



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GFS Getter')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time')

    args = parser.parse_args()
    
    init_slack()
    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')

    make_que(init)
    logger.debug('GSM ({})の取得を開始しました。'.format(init.strftime('%Y/%m/%d %H:00:00')))
    for i in range(num_thread):
        worker = Thread(target=downloader, args=(init,))
        worker.setDaemon(True)
        worker.start()
        
    download_que.join()
    logger.debug('GSMの取得を終了しました。')

#!/usr/bin/env python3
import os
import datetime
import time
import json
import logging
import argparse
import subprocess
import sys

from slack_log_handler import SlackLogHandler
import jinja2

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


HOME = os.path.expanduser('~')
GSMDIR = HOME + '/JMA/DATA/GSM/{}/'
TMPDIR = HOME + '/ForecastSystem/tmp'

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

def get_init():
    now = datetime.datetime.utcnow()
    now = now.replace(second=0, microsecond=0)
    target = now - datetime.timedelta(hours=6, minutes=30)
    if 0 <= target.hour < 6:
        target = target.replace(hour=0, minute=0)
    elif 6 <= target.hour < 12:
        target = target.replace(hour=6, minute=0)
    elif 12 <= target.hour < 18:
        target = target.replace(hour=12, minute=0)
    else:
        target = target.replace(hour=18, minute=0)
    return target

def cleanup():
    os.chdir(TMPDIR)
    for f in os.listdir(TMPDIR):
        if f.startswith('0000-0312'):
            os.unlink(f)
        if f.startswith('0315-0800'):
            os.unlink(f)
        if f.startswith('0803-1100'):
            os.unlink(f)
        if f.startswith('0318-0800'):
            os.unlink(f)
        if f.startswith('0806-1100'):
            os.unlink(f)

            
def PostProcess(init):
    subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/extract_gsm.py', init.strftime('%Y%m%d%H')], shell=False)
    subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_PostProcess', HOME + '/ForecastSystem/tmp/0000-0312_pall.bin', HOME + '/ForecastSystem/tmp/0000-0312_add.bin', "0"], shell=False)
    if init.hour == 12:
        subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_PostProcess', HOME + '/ForecastSystem/tmp/0318-0800_pall.bin', HOME + '/ForecastSystem/tmp/0318-0800_add.bin', "1"], shell=False)
        subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_PostProcess', HOME + '/ForecastSystem/tmp/0806-1100_pall.bin', HOME + '/ForecastSystem/tmp/0806-1100_add.bin', "2"], shell=False)
        
    subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_pickup', HOME + '/ForecastSystem/tmp/0000-0312_surf.bin', HOME + '/ForecastSystem/etc/station.txt', HOME + '/ForecastSystem/tmp/0000-0312_surf.dat', "0", "0"], shell=False)
    subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_pickup', HOME + '/ForecastSystem/tmp/0000-0312_pall.bin', HOME + '/ForecastSystem/etc/station.txt', HOME + '/ForecastSystem/tmp/0000-0312_pall.dat', "1", "0"], shell=False)
    subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_pickup', HOME + '/ForecastSystem/tmp/0000-0312_add.bin', HOME + '/ForecastSystem/etc/station.txt', HOME + '/ForecastSystem/tmp/0000-0312_add.dat', "2", "0"], shell=False)
    if init.hour == 12:
        subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_pickup', HOME + '/ForecastSystem/tmp/0315-0800_surf.bin', HOME + '/ForecastSystem/etc/station.txt', HOME + '/ForecastSystem/tmp/0315-0800_surf.dat', "0", "1"], shell=False)
        subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_pickup', HOME + '/ForecastSystem/tmp/0318-0800_pall.bin', HOME + '/ForecastSystem/etc/station.txt', HOME + '/ForecastSystem/tmp/0318-0800_pall.dat', "1", "1"], shell=False)
        subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_pickup', HOME + '/ForecastSystem/tmp/0318-0800_add.bin', HOME + '/ForecastSystem/etc/station.txt', HOME + '/ForecastSystem/tmp/0318-0800_add.dat', "2", "1"], shell=False)

        subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_pickup', HOME + '/ForecastSystem/tmp/0803-1100_surf.bin', HOME + '/ForecastSystem/etc/station.txt', HOME + '/ForecastSystem/tmp/0803-1100_surf.dat', "0", "2"], shell=False)
        subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_pickup', HOME + '/ForecastSystem/tmp/0806-1100_pall.bin', HOME + '/ForecastSystem/etc/station.txt', HOME + '/ForecastSystem/tmp/0806-1100_pall.dat', "1", "2"], shell=False)
        subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_pickup', HOME + '/ForecastSystem/tmp/0806-1100_add.bin', HOME + '/ForecastSystem/etc/station.txt', HOME + '/ForecastSystem/tmp/0806-1100_add.dat', "2", "2"], shell=False)

    subprocess.check_call([HOME + '/ForecastSystem/bin/gsm_saveDB.py', init.strftime('%Y%m%d%H'), HOME + '/ForecastSystem/db/gsm_fcst.sqlite3'], shell=False)
    
def Guidance(init):
    pass
    
    
def main(init):
    logger.info('{}の計算を開始しました。'.format(init.strftime('%Y/%m/%d %H:00:00')))

    cleanup()
    
    logger.info('GSMの取得を開始します。')
    try:
        subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/getGSM.py', init.strftime('%Y%m%d%H')], shell=False)
    except:
        logger.error('GSMの取得に失敗しました。')
        sys.exit(-1)
    logger.info('GSMの取得を完了しました。')

    logger.info('PostProcessを実行しています。')
    try:
        PostProcess(init)
    except:
        logger.error('PostProcessの実行に失敗しました。')
        sys.exit(-4)
    try:
        subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/chart_gsm.py', init.strftime('%Y%m%d%H')], shell=False)
    except:
        logger.error('GSM Chartsの作成に失敗しました。')
    

    logger.info('Guidanceの作成を開始しました。')
    try:
        Guidance(init)
    except:
        logger.error('Guidanceの作成に失敗しました。')
        sys.exit(-5)
    logger.info('Guidanceの作成を完了しました。')
        
    logger.info('PostProcessを終了しました。')
    logger.info('{}の計算を完了しました。'.format(init.strftime('%Y/%m/%d %H:00:00')))

    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GSM Executor')
    parser.add_argument('-i', '--init', metavar='INIT', type=str, help='Initial Time', nargs="?", default=None)

    args = parser.parse_args()

    if args.init is None:
        init = get_init()
    else:
        init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    init_slack()
    main(init)

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
TMPDIR = HOME + '/ForecastSystem/tmp'
GSMDIR = HOME + '/JMA/DATA/GSM/{year:04d}{month:02d}{day:02d}{hour:02d}/'
FILE1 = ('Z__C_RJTD_{year:04d}{month:02d}{day:02d}{hour:02d}0000_GSM_GPV_Rjp_L-pall_FD0000-0312_grib2.bin', '0000-0312_pall.bin')
FILE2 = ('Z__C_RJTD_{year:04d}{month:02d}{day:02d}{hour:02d}0000_GSM_GPV_Rjp_Lsurf_FD0000-0312_grib2.bin', '0000-0312_surf.bin')
FILE3 = ('Z__C_RJTD_{year:04d}{month:02d}{day:02d}120000_GSM_GPV_Rjp_L-pall_FD0318-0800_grib2.bin', '0318-0800_pall.bin')
FILE4 = ('Z__C_RJTD_{year:04d}{month:02d}{day:02d}120000_GSM_GPV_Rjp_L-pall_FD0806-1100_grib2.bin', '0806-1100_pall.bin')
FILE5 = ('Z__C_RJTD_{year:04d}{month:02d}{day:02d}120000_GSM_GPV_Rjp_Lsurf_FD0315-0800_grib2.bin', '0315-0800_surf.bin')
FILE6 = ('Z__C_RJTD_{year:04d}{month:02d}{day:02d}120000_GSM_GPV_Rjp_Lsurf_FD0803-1100_grib2.bin', '0803-1100_surf.bin')

WGRIB2 = '/usr/local/bin/wgrib2'

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


def main(init):
    os.chdir(TMPDIR)
    fn = (GSMDIR + FILE1[0]).format(year=init.year, month=init.month, day=init.day, hour=init.hour)
    p = subprocess.Popen([WGRIB2, fn, '-no_header', '-bin', FILE1[1]], shell=False, stdout=subprocess.PIPE)
    stdout_data, _ = p.communicate()
    if p.returncode != 0:
        sys.exit(-1)
    with open(FILE1[1] + '.txt', 'w') as f:
        f.write(stdout_data.decode('utf-8'))


    fn = (GSMDIR + FILE2[0]).format(year=init.year, month=init.month, day=init.day, hour=init.hour)
    p = subprocess.Popen([WGRIB2, fn, '-no_header', '-bin', FILE2[1]], shell=False, stdout=subprocess.PIPE)
    stdout_data, _ = p.communicate()
    if p.returncode != 0:
        sys.exit(-1)
    with open(FILE2[1] + '.txt', 'w') as f:
        f.write(stdout_data.decode('utf-8'))

    if init.hour == 12:
        fn = (GSMDIR + FILE3[0]).format(year=init.year, month=init.month, day=init.day, hour=init.hour)
        p = subprocess.Popen([WGRIB2, fn, '-no_header', '-bin', FILE3[1]], shell=False, stdout=subprocess.PIPE)
        stdout_data, _ = p.communicate()
        if p.returncode != 0:
            sys.exit(-1)
        with open(FILE3[1] + '.txt', 'w') as f:
            f.write(stdout_data.decode('utf-8'))


        fn = (GSMDIR + FILE4[0]).format(year=init.year, month=init.month, day=init.day, hour=init.hour)
        p = subprocess.Popen([WGRIB2, fn, '-no_header', '-bin', FILE4[1]], shell=False, stdout=subprocess.PIPE)
        stdout_data, _ = p.communicate()
        if p.returncode != 0:
            sys.exit(-1)
        with open(FILE4[1] + '.txt', 'w') as f:
            f.write(stdout_data.decode('utf-8'))

        fn = (GSMDIR + FILE5[0]).format(year=init.year, month=init.month, day=init.day, hour=init.hour)
        p = subprocess.Popen([WGRIB2, fn, '-no_header', '-bin', FILE5[1]], shell=False, stdout=subprocess.PIPE)
        stdout_data, _ = p.communicate()
        if p.returncode != 0:
            sys.exit(-1)
        with open(FILE5[1] + '.txt', 'w') as f:
            f.write(stdout_data.decode('utf-8'))


        fn = (GSMDIR + FILE6[0]).format(year=init.year, month=init.month, day=init.day, hour=init.hour)
        p = subprocess.Popen([WGRIB2, fn, '-no_header', '-bin', FILE6[1]], shell=False, stdout=subprocess.PIPE)
        stdout_data, _ = p.communicate()
        if p.returncode != 0:
            sys.exit(-1)
        with open(FILE6[1] + '.txt', 'w') as f:
            f.write(stdout_data.decode('utf-8'))
    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GSM Executor')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time')

    args = parser.parse_args()
    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    init_slack()
    main(init)

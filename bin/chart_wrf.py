#!/usr/bin/env python3
import os
import datetime
import json
import logging
import argparse
import subprocess
import sys

from slack_log_handler import SlackLogHandler
import jinja2

HOME = os.path.expanduser('~')
TEMPLATEDIR = HOME + '/ForecastSystem/template'
TMPDIR = HOME + '/ForecastSystem/tmp'
DATADIR = HOME + '/WRF/DATA/output/{}/'
IMGDIR = HOME + '/WRF/DATA/images/WRF/'

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

def main(init):
    wrf = DATADIR.format(init.strftime('%Y%m%d_%H0000'))
    os.chdir(wrf)
    outd = IMGDIR + '/{}'.format(init.strftime('%Y%m%d%H'))
    if os.path.exists(outd) is False:
        os.makedirs(outd)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATEDIR, encoding='utf8'))
    tmpl = env.get_template('wrf.gs.template')
    for ft in range(0, 85, 1):
        valid = init + datetime.timedelta(hours=ft)        
        with open(TMPDIR + '/wrf.gs', 'w') as f:
            f.write(tmpl.render({'inits': init.strftime('%Y/%m/%d %H'), 'valids': valid.strftime('%Y/%m/%d %H'), 'outd': outd, 'ft': '{:03d}'.format(ft), 'fts': ft + 1}))
        subprocess.check_call(['/usr/bin/grads', '-blc', TMPDIR + '/wrf.gs'], shell=False)
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WRF Charts maker')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time', default=None)

    args = parser.parse_args()

    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    init_slack()
    main(init)

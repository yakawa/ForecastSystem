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
GFSDIR = HOME + '/WRF/DATA/GFS/{}/'
IMGDIR = HOME + '/WRF/DATA/images/GFS/'

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
    os.chdir(TMPDIR)
    outd = IMGDIR + '/{}'.format(init.strftime('%Y%m%d%H'))
    if os.path.exists(outd) is False:
        os.makedirs(outd)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATEDIR, encoding='utf8'))
    tmpl = env.get_template('gfs.gs.template')
    for ft in range(0, 87, 3):
        gfs = GFSDIR.format(init.strftime('%Y%m%d%H')) + 'gfs.t{}z.pgrb2.0p50.f{:03d}'.format(init.strftime('%H'), ft)
        valid = init + datetime.timedelta(hours=ft)
        p = subprocess.Popen(['/usr/local/bin/g2ctl', gfs], stdout=subprocess.PIPE, shell=False)
        p.wait()
        with open(TMPDIR + '/gfs.ctl', 'w') as f:
            for l in p.stdout.readlines():
                f.write(l.decode('utf-8'))
        subprocess.check_call(['/usr/bin/gribmap', '-i', TMPDIR + '/gfs.ctl'], shell=False)
        with open(TMPDIR + '/gfs.gs', 'w') as f:
            f.write(tmpl.render({'inits': init.strftime('%Y/%m/%d %H'), 'valids': valid.strftime('%Y/%m/%d %H'), 'outd': outd, 'ft': '{:03d}'.format(ft)}))
        subprocess.check_call(['/usr/bin/grads', '-blc', TMPDIR + '/gfs.gs'], shell=False)
        
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GFS Charts maker')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time', default=None)

    args = parser.parse_args()

    init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    init_slack()
    main(init)

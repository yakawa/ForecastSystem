#!/usr/bin/env python3
import os
import datetime
import json
import logging
import argparse

from slack_log_handler import SlackLogHandler

HOME = os.path.expanduser('~')

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

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='GFS Getter')
    parser.add_argument('init', metavar='INIT', type=str, help='Initial Time')

    args = parser.parse_args()
    

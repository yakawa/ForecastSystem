#!/usr/bin/env python3
import logging
import sys
import re
import datetime
import argparse
import sqlite3

from pyquery import PyQuery as pq
from slack_log_handler import SlackLogHandler
import requests

logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


_re_station = re.compile("javascript:viewPoint\((?P<info>.+)\);")

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

def dict_factory(cursor, row):
  d = {}
  for idx, col in enumerate(cursor.description):
    d[col[0]] = row[idx]
  return d

def setupDB(DB):
  with sqlite3.connect(DB) as con:
    con.row_factory = dict_factory
    cur = con.cursor()

    sql = '''
    CREATE TABLE IF NOT EXISTS JMAStation (
      Type       TEXT,
      BlockNo    TEXT,
      StationNo  TEXT,
      Name       TEXT,
      Kana       TEXT,
      Lat        DOUBLE,
      Lon        DOUBLE,
      Height     DOUBLE,
      IsPrec     UNSIGNED INT DEFAULT 0,
      IsWind     UNSIGNED INT DEFAULT 0,
      IsTemp     UNSIGNED INT DEFAULT 0,
      IsSun      UNSIGNED INT DEFAULT 0,
      IsSnow     UNSIGNED INT DEFAULT 0,
      End        DATE,
      Date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      UNIQUE     (BlockNo, StationNo)
    );
    '''
    cur.execute(sql)


def getPage(block):
  URL = "http://www.data.jma.go.jp/obd/stats/etrn/select/prefecture.php?prec_no={}".format(block)

  logger.debug('Getting {}'.format(URL))
  req = requests.get(URL)
  logger.debug('Response: {}'.format(req.status_code))
  if req.status_code != 200:
    return None
  req.encoding = 'UTF-8'
  return req.text.encode('UTF-8')

def parsePage(block, page):
  ret = []
  root = pq(page)
  for i, m in enumerate(root('map area').items()):
    if i % 2 == 0:
      continue
    s = m.attr['onmouseover']
    if s is None:
      continue
    _m = _re_station.match(s)
    if _m is None:
      logger.error('?')
    info = _m.group('info').replace("'", "")
    w = info.split(',')
    stn = {
      'Type': w[0],
      'BlockNo': block,
      'StationNo': w[1],
      'Name': w[2],
      'Kana': w[3],
      'Lat': int(w[4]) + float(w[5]) / 60.,
      'Lon': int(w[6]) + float(w[7]) / 60.,
      'Height': float(w[8]),
      'IsPrec': True if w[9] == '1' else False,
      'IsWind': True if w[10] == '1' else False,
      'IsTemp': True if w[11] == '1' else False,
      'IsSun': True if w[12] == '1' else False,
      'IsSnow': True if w[13] == '1' else False,
      'End': datetime.date(year=9999, month=12, day=31) if w[14] == '9999' else datetime.date(year=int(w[14]), month=int(w[15]), day=int(w[16]))
    }
    ret.append(stn)
  return ret

def saveDB(DB, stations):
  saved = []
  with sqlite3.connect(DB) as con:
    con.row_factory = dict_factory
    cur = con.cursor()

    sql = '''
    SELECT
     Type,
     BlockNo,
     StationNo
    FROM
     JMAStation
    '''
    cur.execute(sql)

    rows = cur.fetchall()
    for r in rows:
      if r['Type'] == 's':
        sno = r['StationNo']
      else:
        sno = "{}-{}".format(r['BlockNo'], r['StationNo'])
      saved.append(sno)

    sql = '''
    INSERT OR REPLACE INTO JMAStation
     (Type, BlockNo, StationNo, Name, Kana, Lat, Lon, Height, IsPrec, IsWind, IsTemp, IsSun, IsSnow, End)
    VALUES
     (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    '''

    n_new = 0
    for stn in stations:
      if stn['Type'] == 's':
        if stn['StationNo'] not in saved:
          n_new += 1
          logger.info("{} is new Station".format(stn['Name']))
        else:
          saved.remove(stn['StationNo'])
          logger.debug("{} is updated".format(stn['Name']))
      else:
        s = "{}-{}".format(stn['BlockNo'], stn['StationNo'])
        if s not in saved:
          n_new += 1
          logger.info("{} is new Station".format(stn['Name']))
        else:
          saved.remove(s)
          logger.debug("{} is updated".format(stn['Name']))
      cur.execute(sql, (stn['Type'], stn['BlockNo'], stn['StationNo'], stn['Name'], stn['Kana'], stn['Lat'], stn['Lon'], stn['Height'],
                        stn['IsPrec'], stn['IsWind'], stn['IsTemp'], stn['IsSun'], stn['IsSnow'], stn['End']))
    n_end = len(saved)
    if n_end != 0:
      for s in saved:
        logger.info("{} is over".format(s))

    logger.info('New Station: {}, Terminate Station: {}'.format(n_new, n_end))
    con.commit()


if __name__ == '__main__':
  init_slack()
  parser = argparse.ArgumentParser(description='Crawler')
  parser.add_argument('db', metavar='DB', type=str, help='DataBase Name')

  args = parser.parse_args()

  blocks = [
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24",
    "31", "32", "33", "34", "35", "36",
    "40", "41", "42", "43", "44", "45", "46", "48", "49",
    "50", "51", "52", "53", "54", "55", "56", "57",
    "60", "61", "62", "63", "64", "65", "66", "67", "68", "69",
    "71", "72", "73", "74",
    "81", "82", "83", "84", "85", "86", "87", "88",
    "91", "99",
  ]

  setupDB(args.db)

  stations = []
  for block in blocks:
    body = getPage(block)
    if body is None:
      logger.error('Cannot get page')
      sys.exit(1)
    stn = parsePage(block, body)
    for s in stn:
      stations.append(s)

  saveDB(args.db, stations)

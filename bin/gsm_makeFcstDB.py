#!/usr/bin/env python3
import os
import logging
import argparse
import sqlite3


def makeDB(db):
    with sqlite3.connect(db) as con:
        cur = con.cursor()

        sql = '''
        CREATE TABLE IF NOT EXISTS GSMFcst (
          Station    TEXT NOT NULL,
          init       DATETIME NOT NULL,
          ft         INTEGER NOT NULL,
          msl        REAL, press      REAL, uwind      REAL, vwind      REAL, temp       REAL, rh         REAL,
          lcld       REAL, mcld       REAL, hcld       REAL, tcld       REAL, prec       REAL,
          ssi        REAL, ssi850_700 REAL, ssi925_850 REAL, ept_850    REAL, td_850     REAL, td_700     REAL,
          h_1000     REAL, uwind_1000 REAL, vwind_1000 REAL, t_1000     REAL, wwind_1000 REAL, rh_1000    REAL,
          h_975      REAL, uwind_975  REAL, vwind_975  REAL, t_975      REAL, wwind_975  REAL, rh_975     REAL,
          h_950      REAL, uwind_950  REAL, vwind_950  REAL, t_950      REAL, wwind_950  REAL, rh_950     REAL,
          h_925      REAL, uwind_925  REAL, vwind_925  REAL, t_925      REAL, wwind_925  REAL, rh_925     REAL,
          h_900      REAL, uwind_900  REAL, vwind_900  REAL, t_900      REAL, wwind_900  REAL, rh_900     REAL,
          h_850      REAL, uwind_850  REAL, vwind_850  REAL, t_850      REAL, wwind_850  REAL, rh_850     REAL,
          h_800      REAL, uwind_800  REAL, vwind_800  REAL, t_800      REAL, wwind_800  REAL, rh_800     REAL,
          h_700      REAL, uwind_700  REAL, vwind_700  REAL, t_700      REAL, wwind_700  REAL, rh_700     REAL,
          h_600      REAL, uwind_600  REAL, vwind_600  REAL, t_600      REAL, wwind_600  REAL, rh_600     REAL,
          h_500      REAL, uwind_500  REAL, vwind_500  REAL, t_500      REAL, wwind_500  REAL, rh_500     REAL,
          h_400      REAL, uwind_400  REAL, vwind_400  REAL, t_400      REAL, wwind_400  REAL, rh_400     REAL,
          h_300      REAL, uwind_300  REAL, vwind_300  REAL, t_300      REAL, wwind_300  REAL, rh_300     REAL,
          h_250      REAL, uwind_250  REAL, vwind_250  REAL, t_250      REAL, wwind_250  REAL,
          h_200      REAL, uwind_200  REAL, vwind_200  REAL, t_200      REAL, wwind_200  REAL,
          h_150      REAL, uwind_150  REAL, vwind_150  REAL, t_150      REAL, wwind_150  REAL,
          h_100      REAL, uwind_100  REAL, vwind_100  REAL, t_100      REAL, wwind_100  REAL,        
        UNIQUE(Station, init, ft)
        );
        '''
        cur.execute(sql)

        sql = '''
        CREATE INDEX idx_stn ON GSMFcst (Station);
        '''
        cur.execute(sql)

        sql = '''
        CREATE INDEX idx_stn_init ON GSMFcst(Station, init);
        '''
        cur.execute(sql)
        con.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make DB')
    parser.add_argument('db', metavar='DB', type=str, help='DB Path')

    args = parser.parse_args()
    makeDB(args.db)

    

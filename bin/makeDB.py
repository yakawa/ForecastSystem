#!/usr/bin/env python3
import os
import logging
import argparse
import sqlite3


def makeDB(db):
    with sqlite3.connect(db) as con:
        cur = con.cursor()

        sql = '''
        CREATE TABLE IF NOT EXISTS WRFFcst (
          Station    TEXT NOT NULL,
          init       DATETIME NOT NULL,
          ft         INTEGER NOT NULL,
          t2         REAL, td2        REAL, rh2        REAL, u10        REAL, v10        REAL, tpw        REAL, ssi        REAL, ssi700_500 REAL, ssi925_850 REAL, 
          sdown      REAL, rain_c     REAL, rain_rc    REAL, rain_nc    REAL, rain_rnc   REAL, cld_lo     REAL, cld_mo     REAL, cld_hi     REAL,
          msl        REAL, cape       REAL, cin        REAL, lcl        REAL, lfc        REAL, dbz        REAL,
          uwind_1000 REAL, uwind_925  REAL, uwind_900  REAL, uwind_850  REAL, uwind_800  REAL, uwind_700  REAL, uwind_600  REAL, uwind_500  REAL, uwind_400  REAL, uwind_300  REAL, uwind_200  REAL, uwind_100  REAL,
          vwind_1000 REAL, vwind_925  REAL, vwind_900  REAL, vwind_850  REAL, vwind_800  REAL, vwind_700  REAL, vwind_600  REAL, vwind_500  REAL, vwind_400  REAL, vwind_300  REAL, vwind_200  REAL, vwind_100  REAL,
          wwind_1000 REAL, wwind_925  REAL, wwind_900  REAL, wwind_850  REAL, wwind_800  REAL, wwind_700  REAL, wwind_600  REAL, wwind_500  REAL, wwind_400  REAL, wwind_300  REAL, wwind_200  REAL, wwind_100  REAL,
          temp_1000  REAL, temp_925   REAL, temp_900   REAL, temp_850   REAL, temp_800   REAL, temp_700   REAL, temp_600   REAL, temp_500   REAL, temp_400   REAL, temp_300   REAL, temp_200   REAL, temp_100   REAL,
          td_1000    REAL, td_925     REAL, td_900     REAL, td_850     REAL, td_800     REAL, td_700     REAL, td_600     REAL, td_500     REAL, td_400     REAL, td_300     REAL, td_200     REAL, td_100     REAL,
          rh_1000    REAL, rh_925     REAL, rh_900     REAL, rh_850     REAL, rh_800     REAL, rh_700     REAL, rh_600     REAL, rh_500     REAL, rh_400     REAL, rh_300     REAL, rh_200     REAL, rh_100     REAL,
          qv_1000    REAL, qv_925     REAL, qv_900     REAL, qv_850     REAL, qv_800     REAL, qv_700     REAL, qv_600     REAL, qv_500     REAL, qv_400     REAL, qv_300     REAL, qv_200     REAL, qv_100     REAL,
          th_1000    REAL, th_925     REAL, th_900     REAL, th_850     REAL, th_800     REAL, th_700     REAL, th_600     REAL, th_500     REAL, th_400     REAL, th_300     REAL, th_200     REAL, th_100     REAL,
          qc_1000    REAL, qc_925     REAL, qc_900     REAL, qc_850     REAL, qc_800     REAL, qc_700     REAL, qc_600     REAL, qc_500     REAL, qc_400     REAL, qc_300     REAL, qc_200     REAL, qc_100     REAL,
          qr_1000    REAL, qr_925     REAL, qr_900     REAL, qr_850     REAL, qr_800     REAL, qr_700     REAL, qr_600     REAL, qr_500     REAL, qr_400     REAL, qr_300     REAL, qr_200     REAL, qr_100     REAL,
          ept_1000   REAL, ept_925    REAL, ept_900    REAL, ept_850    REAL, ept_800    REAL, ept_700    REAL, ept_600    REAL, ept_500    REAL, ept_400    REAL, ept_300    REAL, ept_200    REAL, ept_100    REAL,
          geoh_1000  REAL, geoh_925   REAL, geoh_900   REAL, geoh_850   REAL, geoh_800   REAL, geoh_700   REAL, geoh_600   REAL, geoh_500   REAL, geoh_400   REAL, geoh_300   REAL, geoh_200   REAL, geoh_100   REAL,
        UNIQUE(Station, init, ft)
        );
        '''
        cur.execute(sql)

        sql = '''
        CREATE INDEX idx_stn ON WRFFcst (Station);
        '''
        cur.execute(sql)

        sql = '''
        CREATE INDEX idx_stn_init ON WRFFcst(Station, init);
        '''
        cur.execute(sql)
        con.commit()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Make DB')
    parser.add_argument('db', metavar='DB', type=str, help='DB Path')

    args = parser.parse_args()
    makeDB(args.db)

    

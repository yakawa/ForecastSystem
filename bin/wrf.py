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
WRFBASE = HOME + '/WRF/WRFV3'
WPSBASE = HOME + '/WRF/WPS'
ARWpost = HOME + '/WRF/ARWpost'
GEOG = HOME + '/WRF/geog/'
TEMPLATEDIR = HOME + '/ForecastSystem/template'
SSTDIR = HOME + '/WRF/DATA/SST/{}/'
GFSDIR = HOME + '/WRF/DATA/GFS/{}/'
OUTPUTDIR = HOME + '/WRF/DATA/output/{}/'
RUN_HOUR = 84

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
    target = now - datetime.timedelta(hours=3, minutes=30)
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
    for fp in os.listdir(WPSBASE):
        if fp.startswith('FILE:'):
            os.remove(WPSBASE + '/' + fp)
        if fp.startswith('SST:'):
            os.remove(WPSBASE + '/' + fp)

        if fp.startswith('met_em.'):
            os.remove(WPSBASE + '/' + fp)
        if fp.startswith('GRIBFILE.'):
            os.remove(WPSBASE + '/' + fp)

    for fp in os.listdir(WRFBASE + '/run'):
        if fp.startswith('met_em.'):
            os.remove(WRFBASE + '/run/' + fp)
        if fp.startswith('wrfinput_d'):
            os.remove(WRFBASE + '/run/' + fp)
        if fp.startswith('wrfbdy_d'):
            os.remove(WRFBASE + '/run/' + fp)
        if fp.startswith('auxhist3_'):
            os.remove(WRFBASE + '/run/' + fp)
        if fp.startswith('wrfrst_d'):
            os.remove(WRFBASE + '/run/' + fp)
        if fp.startswith('wrfout_d'):
            os.remove(WRFBASE + '/run/' + fp)
            

def SST(init):
    os.chdir(WPSBASE)
    for fp in os.listdir(WPSBASE):
        if fp.startswith('GRIBFILE.'):
            os.remove(WPSBASE + '/' + fp)
    d = SSTDIR.format(init.strftime('%Y%m%d%H'))
    if os.path.exists(WPSBASE + '/Vtable'):
        os.remove(WPSBASE + '/Vtable')
    os.symlink(WPSBASE + '/ungrib/Variable_Tables/Vtable.SST', WPSBASE + '/Vtable')
    subprocess.check_call(['./link_grib.csh', d])
    subprocess.check_call(['./ungrib.exe',])

def GFS(init):
    os.chdir(WPSBASE)
    for fp in os.listdir(WPSBASE):
        if fp.startswith('GRIBFILE.'):
            os.remove(WPSBASE + '/' + fp)
    d = GFSDIR.format(init.strftime('%Y%m%d%H'))
    if os.path.exists(WPSBASE + '/Vtable'):
        os.remove(WPSBASE + '/Vtable')
    os.symlink(WPSBASE + '/ungrib/Variable_Tables/Vtable.GFS', WPSBASE + '/Vtable')
    subprocess.check_call(['./link_grib.csh', d])
    subprocess.check_call(['./ungrib.exe',])

def WRF():
    os.chdir(WRFBASE + '/run')
    for fp in os.listdir(WPSBASE):
        if fp.startswith('met_em.'):
            os.symlink(WPSBASE + '/' + fp, WRFBASE + '/run/' + fp)
    subprocess.check_call(['./real.exe',])
    subprocess.check_call(['./wrf.exe',])
                                           
def PostProcess(init):
    os.chdir(ARWpost)
    subprocess.check_call(['./ARWpost.exe'])
    
    inf = OUTPUTDIR.format(init.strftime('%Y%m%d_%H0000')) + '/wrf_output_element.dat'
    outf1 = OUTPUTDIR.format(init.strftime('%Y%m%d_%H0000')) + '/wrf_output.dat'
    outf2 = OUTPUTDIR.format(init.strftime('%Y%m%d_%H0000')) + '/station.dat'
    subprocess.check_call([HOME + '/ForecastSystem/bin/wrf_PostProcess', inf, outf1], shell=False)
    os.unlink(inf)

    subprocess.check_call([HOME + '/ForecastSystem/bin/wrf_pickup', outf1, HOME + '/ForecastSystem/etc/station.txt', outf2], shell=False)
    subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/wrf_saveDB.py', init.strftime('%Y%m%d%H'), HOME + '/ForecastSystem/db/fcst.sqlite3'], shell=False)
    os.unlink(outf2)
    os.unlink(OUTPUTDIR.format(init.strftime('%Y%m%d_%H0000')) + '/wrf_output_element.ctl')
    
def Guidance(init):
    subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/guidance_wrf_make_db.py', init.strftime('%Y%m%d%H'), HOME + '/ForecastSystem/etc/station.txt', HOME + '/ForecastSystem/db/fcst.sqlite3'], shell=False)
    subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/guidance_wrf_temp.py', init.strftime('%Y%m%d%H'), HOME + '/ForecastSystem/db/fcst.sqlite3', HOME + '/ForecastSystem/guidance/'], shell=False)
    subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/guidance_wrf_rh.py', init.strftime('%Y%m%d%H'), HOME + '/ForecastSystem/db/fcst.sqlite3', HOME + '/ForecastSystem/guidance/'], shell=False)
    subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/guidance_wrf_wind.py', init.strftime('%Y%m%d%H'), HOME + '/ForecastSystem/db/fcst.sqlite3', HOME + '/ForecastSystem/guidance/'], shell=False)

    subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/guidance_wrf_pop2.py', init.strftime('%Y%m%d%H'), HOME + '/ForecastSystem/db/fcst.sqlite3', HOME + '/ForecastSystem/guidance/'], shell=False)
    subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/guidance_wrf_prec.py', init.strftime('%Y%m%d%H'), HOME + '/ForecastSystem/db/fcst.sqlite3', HOME + '/ForecastSystem/guidance/'], shell=False)
    
    subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/guidance_wrf_wx.py', init.strftime('%Y%m%d%H'), HOME + '/ForecastSystem/db/fcst.sqlite3', HOME + '/ForecastSystem/guidance/'], shell=False)
    
    
def main(init):
    sst_init = (init - datetime.timedelta(hours=24)).replace(hour=0, minute=0, second=0, microsecond=0)

    logger.info('{}の計算を開始しました。'.format(init.strftime('%Y/%m/%d %H:00:00')))

    cleanup()
    
    logger.info('GFSの取得を開始します。')
    try:
        subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/getGFS.py', init.strftime('%Y%m%d%H')], shell=False)
    except:
        logger.error('GFSの取得に失敗しました。')
        sys.exit(-1)
    logger.info('GFSの取得を完了しました。')

    try:
        subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/chart_gfs.py', init.strftime('%Y%m%d%H')], shell=False)
    except:
        logger.error('GFS Chartsの作成に失敗しました。')
    
    logger.info('SSTの取得を開始します。')
    try:
        subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/getSST.py', sst_init.strftime('%Y%m%d%H')], shell=False)
    except:
        logger.error('SSTの取得に失敗しました。')
        sys.exit(-1)
    logger.info('SSTの取得を完了しました。')

    
    # WPS
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATEDIR, encoding='utf8'))
    run_hour = RUN_HOUR

    start_time = init.strftime('%Y-%m-%d_%H:%M:00')
    end_time = (init + datetime.timedelta(hours=run_hour)).strftime('%Y-%m-%d_%H:%M:00')
    sst_time = sst_init.strftime('%Y-%m-%d_%H:%M:00')
    sst_fn = sst_init.strftime('%Y-%m-%d_%H')
    geog = GEOG
    
    wps_tmpl = env.get_template('namelist.wps.template')
    wps_sst_tmpl = env.get_template('namelist.wps.sst.template')
    wrf_i_tmpl = env.get_template('namelist.input.template')
    post_tmpl = env.get_template('namelist.ARWpost.template')
    ctl_tmpl = env.get_template('arwpost.ctl.template')

    logger.info('SSTの処理を実行しています。')
    with open(WPSBASE + '/namelist.wps', 'w') as fn:
        fn.write(wps_sst_tmpl.render({'start_time':start_time, 'end_time':end_time, 'sst_time': sst_time, 'geog': geog, 'run_hour': run_hour}))
    try:
        SST(sst_init)
    except:
        logger.error('SSTの処理に失敗しました。')
        sys.exit(-2)

    logger.info('GFSの処理を実行しています。')
    with open(WPSBASE + '/namelist.wps', 'w') as fn:
        fn.write(wps_tmpl.render({'start_time':start_time, 'end_time':end_time, 'sst_time': sst_fn, 'geog': geog, 'run_hour': run_hour}))
    try:
        GFS(init)
    except:
        logger.error('GFSの処理に失敗しました。')
        sys.exit(-2)


    logger.info('PreProcessを実行します。')
    with open(WRFBASE + '/run/namelist.input', 'w') as fn:
        fn.write(wrf_i_tmpl.render({'init':init, 'endt': init + datetime.timedelta(hours=run_hour), 'run_hour': run_hour }))

    try:
        os.chdir(WPSBASE)
        subprocess.check_call(['./metgrid.exe',])
    except:
        logger.error('PreProcessの実行に失敗しました。')
        sys.exit(-2)
        
    logger.info('WRFを実行しています。')
    try:
        WRF()
    except:
        logger.error('WRFの実行に失敗しました。')
        sys.exit(-3)
    logger.info('WRFの実行が完了しました。')

    logger.info('PostProcessを実行しています。')
    try:
        if not os.path.isdir(OUTPUTDIR.format(init.strftime('%Y%m%d_%H0000'))):
            os.makedirs(OUTPUTDIR.format(init.strftime('%Y%m%d_%H0000')))

        of_nc = WRFBASE + '/run/wrfout_d01_' + start_time 
        out = OUTPUTDIR.format(init.strftime('%Y%m%d_%H0000')) + '/wrf_output_element'

        with open(ARWpost + '/namelist.ARWpost', 'w') as fn:
            fn.write(post_tmpl.render({'start_time':start_time, 'end_time':end_time, 'of_nc': of_nc, 'out': out }))
        with open(OUTPUTDIR.format(init.strftime('%Y%m%d_%H0000')) + '/wrf_output.ctl', 'w') as fn:
            fn.write(ctl_tmpl.render({'init_str':init.strftime('%HZ%d%b%Y'), 'START_DATE': init.strftime('%Y-%m-%d_%H:%M:%S') }))
            
        PostProcess(init)
    except:
        logger.error('PostProcessの実行に失敗しました。')
        sys.exit(-4)

    logger.info('Guidanceの作成を開始しました。')
    try:
        Guidance(init)
    except:
        logger.error('Guidanceの作成に失敗しました。')
        sys.exit(-5)
    logger.info('Guidanceの作成を完了しました。')
    try:
        subprocess.check_call(['/usr/bin/env', 'python3', HOME + '/ForecastSystem/bin/chart_wrf.py', init.strftime('%Y%m%d%H')], shell=False)
    except:
        logger.error('WRF Chartsの作成に失敗しました。')
        
    logger.info('PostProcessを終了しました。')
    logger.info('{}の計算を完了しました。'.format(init.strftime('%Y/%m/%d %H:00:00')))

    
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='WRF Executor')
    parser.add_argument('-i', '--init', metavar='INIT', type=str, help='Initial Time', nargs="?", default=None)

    args = parser.parse_args()

    if args.init is None:
        init = get_init()
    else:
        init = datetime.datetime.strptime(args.init, '%Y%m%d%H')
    init_slack()
    main(init)

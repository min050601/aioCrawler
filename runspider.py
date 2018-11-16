import os,sys
import time
import signal
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)
from aioCrawler.log import messages,SpiderLog
from aioCrawler.actuator import LoadSpiders
import multiprocessing
from aioCrawler.worker import request_run,insert_run
log=SpiderLog(level_str='INFO')
spider_status = multiprocessing.Array('i', [1, 1])
def run(name,args=None):
    spiders=LoadSpiders()._spiders
    Spider=spiders.get(name,None)
    q = multiprocessing.Queue()
    assert Spider!=None,'the moulde %s has not exist'%name
    p1 = multiprocessing.Process(target=request_run,args=(Spider,spider_status,q,args))
    p1.daemon=True
    p2 = multiprocessing.Process(target=insert_run,args=(Spider,spider_status,args))
    p2.daemon=True
    p1.start()
    p2.start()
    while 1:
        try:
            mess={}
            if spider_status[0]==0 and spider_status[1]==0:
                while not q.empty():
                    mess.update(q.get())
                log.logging.info(messages(mess))
                print('任务完成，爬虫停止')
                return
            else:
                time.sleep(10)
        except KeyboardInterrupt:
            control=input('请选择程序停止方式：\n1：立即停止\n2：停止消费后停止\n3：取消\n')
            if control.strip()=='1':
                exit(0)
            elif control.strip()=='2':
                log.logging.info('正在保存未完成的任务，请稍等。。。。')
                if spider_status[0] == 1:spider_status[0]=2
                if spider_status[1] == 1:spider_status[1] = 2
            else:
                continue




# def stopspider(signum=None, frame=None):
#     print(signum,frame)
#     log.logging.info('正在停止任务，请稍等。。。。')
#
#     global spider_status
#     # if spider_status[0] == 1:spider_status[0]=2
#     # if spider_status[1] == 1:spider_status[1] = 2
#     time.sleep(20)
#     exit()





if __name__=="__main__":
    import argparse
    from argparse import ArgumentDefaultsHelpFormatter
    parser = argparse.ArgumentParser(prog="AioSpider", description='Knownsec Interview Spider By Docopt.',
                                     formatter_class=ArgumentDefaultsHelpFormatter)

    parser.add_argument('-c', dest='computer', action='store', required=True,choices=['m','s'], help='the master or slave spider begins with')
    parser.add_argument('-n', dest='spidername', action='store', required=True,
                        help='the spider name of run')
    parser.add_argument('-f', dest='forbidden_startrequest', action='store',choices=['yes','no'],default='no', help='is forbidden_startrequest ')
    parser.add_argument('-r', dest='roles', action='store', choices=['all','worker','customer'],default='all', help='part of zhe spider run')
    args=parser.parse_args()
    # signal.signal(signal.SIGINT, stopspider)

    run(name=args.spidername,args=args)

    # assert len(argv) == 2, 'func run need 1 parmas,%s given' % (len(argv) - 1)
    # run(argv[-1])
    # run('court_wenshu')


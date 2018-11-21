import os,sys
import time
import signal
import datetime
import pymysql
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)
from aioCrawler.log import messages,SpiderLog
from aioCrawler.actuator import LoadSpiders
import multiprocessing
from aioCrawler.worker import request_run,insert_run


connect = pymysql.Connect(
            host='127.0.0.1',
            port=3306,
            user='root',
            passwd='root',
            db='aioCrawler',
            charset='utf8',
            use_unicode=True
        )


spider_status = multiprocessing.Array('i', [1, 1])
def run(name,plan='once',id=None,scheduler_id=None,args=None):
    spiders=LoadSpiders()._spiders
    Spider=spiders.get(name,None)
    log = Spider(start=True).log
    q = multiprocessing.Queue()
    assert Spider!=None,'the moulde %s has not exist'%name
    p1 = multiprocessing.Process(target=request_run,args=(Spider,spider_status,q,args))
    log.logging.info('request:%s'%p1.pid)
    print(p1.pid)
    p1.daemon=True
    p2 = multiprocessing.Process(target=insert_run,args=(Spider,spider_status,args))
    log.logging.info('response:%s' % p2.pid)
    print(p2.pid)
    p2.daemon=True
    p1.start()
    p2.start()

    modify_pid_status(name,1,id,plan,scheduler_id)
    while 1:
        try:
            mess={}
            if spider_status[0]==0 and spider_status[1]==0:
                while not q.empty():
                    mess.update(q.get())
                log.logging.info(messages(mess))
                print('任务完成，爬虫停止')
                modify_pid_status(name, 0,id,plan,scheduler_id)
                return
            else:
                time.sleep(10)
                if not get_ospid_status():
                    p1.terminate()
                    p2.terminate()
                    print('强制结束')
                    return
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



def get_ospid_status():
    #pidstatus=1 运行中
    # pidstatus=0 停止
    cursor = connect.cursor()
    cursor.execute(
        "select running_status from aioCrawler.spiderStatus where pid=%s",(os.getpid(),))

    connect.commit()
    result = cursor.fetchall()
    print('查询成功')
    for i in result:
        print(i[0],'!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        return i[0]

def modify_pid_status(spider,status,id,plan,scheduler_id):
    cursor = connect.cursor()

    if id:
        cursor.execute('''update spiderStatus set pid=%s,running_status=%s,start_time=%s where id=%s''',(os.getpid(),status,datetime.datetime.now(),id))
    else:
        cursor.execute(
            "insert into aioCrawler.spiderStatus(pid,spider,running_status,plan,planned_status,start_time,scheduler_id) VALUES (%s,%s,%s,%s,%s,%s,%s) on duplicate key update pid=%s,spider=%s,running_status=%s,start_time=%s", (os.getpid(),spider,status,plan,1,datetime.datetime.now(),scheduler_id,os.getpid(),spider,status,datetime.datetime.now()))
    connect.commit()





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


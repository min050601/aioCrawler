import threading
from aioCrawler.log import SpiderLog
from aioCrawler.base_roles.worker import Base_worker
from aioCrawler.base_roles.customer import Base_customer
import time


class Worker(Base_worker):
    ippool_updatetime=time.time()
    ippool={}


    # def get_ippool(self):
    #     if time.time()-self.ippool_updatetime>10 or not self.ippool:
    #         while 1:
    #             try:
    #                 items=redis_conn.lrange("aio_proxylist", 0, -1)
    #                 if items:
    #                     self.ippool_updatetime=time.time()
    #                     return [i.decode('utf-8') for i in items]
    #                 else:
    #                     time.sleep(5)
    #                     continue
    #             except Exception as e:
    #                 print(e)
    #     else:
    #         return self.ippool
    # async def get_ippool(self,ippool_name):
    #     if not self.ippool.get(ippool_name):
    #         print('更新ip池')
    #         while 1:
    #             try:
    #                 items = await self.redis_conn.zrangebyscore(ippool_name, 0, int(time.time() - self.spider.settings['IP_SLEEP']))
    #                 # items=redis_conn.lrange("https_proxylist", 0, -1)
    #                 # items = redis_conn.zrange("alive_ips", 0, -1)
    #                 # items = redis_conn.lrange("https_wei", 0, -1)
    #                 # items = redis_conn.smembers("zdysm_ip")
    #                 if items:
    #                     self.pause = False
    #                     if len(items)<200:
    #                         self.ippool[ippool_name]=[i.decode('utf-8') for i in items][0:len(items)]
    #                     else:
    #                         self.ippool[ippool_name] = [i.decode('utf-8') for i in items][-200:-1]
    #                     print('%sip池有%s个可用代理'%(ippool_name,len(self.ippool.get(ippool_name))))
    #                     for i in self.ippool[ippool_name]:
    #                         await self.redis_conn.zadd(self.spider.name,int(time.time())*10, i)
    #                         # redis_conn.zrem(self.spider.name,i)
    #
    #                     return
    #                 else:
    #                     self.pause = True
    #                     print('ip池暂无可用代理，休眠')
    #                     return
    #             except Exception as e:
    #                 print(e)
    #     else:
    #         print('%sip池可用ip个数：%s'%(ippool_name,len(self.ippool.get(ippool_name))))
    #         return




class Customer(Base_customer):
    pass



#请求启动函数
def request_run(Spider,spider_status,q,args):
    if args and args.roles=='customer':
        spider_status[0] = 0
        return
    spider = Spider()
    worker = Worker(spider,spider_status,q)
    t = threading.Thread(target=worker.run)
    t.start()
    t.join()
    print('请求启动函数退出')


#入库启动函数
def insert_run(Spider,spider_status,args):
    if args and args.roles == 'worker':
        spider_status[1]=0
        return
    from twisted.internet import reactor
    spider = Spider()
    if not args or (args.forbidden_startrequest=='no' and args.computer=='m'):
        t = threading.Thread(target=spider.start_request)
        t.start()
    spider.start_insert()
    customer = Customer(spider,spider_status)
    t = threading.Thread(target=customer.start)
    t.start()
    reactor.run()







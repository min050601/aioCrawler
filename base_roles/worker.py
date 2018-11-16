from aiorequest import Request
from aioresponse import Response
import aioamqp
from aioamqp.properties import Properties
import random
import time
import asyncio
from aiohttp import ClientSession
import pickle
import aioredis
import threading
import requests
from yarl import URL
import socket
from base64 import b64encode
import json
from aiohttp import TCPConnector
#try:
#    import uvloop
#    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
#except:
#    pass
look=threading.Lock()

class Base_worker(object):
    def __init__(self,spider,spider_status,q):
        self.monitor_conn=requests.Session()
        self.sleeptime=(spider.settings['REQUEST_DELAY'] or 1)        
        self.breakup=False
        self.last_see=time.time()
        self.spider_status = spider_status
        self.spider=spider
        self.sem = asyncio.Semaphore(self.spider.settings['CONCURRENT_NUMS'])
        self.log=spider.log
        self.success_count=0
        self.spider_messages=q
        self.spider_messages_copy = {}
        self.username = self.spider.settings['MQ_USER']
        self.pwd = self.spider.settings['MQ_PWD']
        if self.spider.settings['DNS_CACHE']:
            self._dnscache = {}
            self._setDNSCache()

    def monitor(self):
        return
        # while 1:
        #     try:
        #         Authorization=b64encode(b'%s:%s'%(self.spider.settings['MQ_USER'].encode(),self.spider.settings['MQ_PWD'].encode())).decode()
        #         headers = {'Authorization': 'Basic %s'%Authorization}
        #         response = self.monitor_conn.get(
        #             url='http://localhost:15672/api/queues?page=1&page_size=100&name=&use_regex=false&pagination=true',
        #             headers=headers)
        #         if response.status_code==200:
        #             messages=json.loads(response.text)
        #             for i in messages.get('items'):
        #                 if i.get('name')==self.spider.routing_key:
        #                     mq_request_count=i.get('messages')
        #                     mq_request_memory = round(i.get('message_bytes')/(1024*1024.0),2)
        #                 if i.get('name')=='%s_response' % self.spider.name:
        #                     mq_response_count = i.get('messages')
        #                     mq_response_memory = round(i.get('message_bytes')/(1024*1024.0),2)
        #             self.log.logging.info('\n请求队列任务量：%s\n请求队列大小：%sM\n消费队列任务量：%s\n消费队列大小：%sM\n'%(mq_request_count,mq_request_memory,mq_response_count,mq_response_memory))
        #             if mq_request_count>1000:
        #                 self.spider.startsleep+=0.1
        #                 self.sleeptime=self.sleeptime*0.9
        #             if mq_request_count<=1000:
        #                 self.spider.startsleep=self.spider.settings['START_SLEEP']
        #                 self.sleeptime = (self.spider.settings['REQUEST_DELAY'] or 1)
        #             return
        #         else:
        #             pass
        #     except Exception as e:
        #         print(e)
        #         time.sleep(30)
        #         self.monitor_conn = requests.Session()







    def start_loop(self,loop):        
        while 1:
            try:
                asyncio.set_event_loop(loop)
                print(111111111111111111111111111)
                loop.run_forever()
            except Exception as e:                               
                print(e)
                print(asyncio.Task.all_tasks())
                for task in asyncio.Task.all_tasks():
                    print(task.cancel())
                print('重启启动')
                


    async def worker(self,request,loop):
        with (await self.sem):
            connector = TCPConnector(loop=loop,verify_ssl=False)

            properties =Properties(priority=request.priority,delivery_mode = 2,)
            if request.method=='POST':
                cookies = request.cookies
                cookie_jar=request.cookie_jar
                session = None
                try:
                    async with ClientSession(cookies=cookies,conn_timeout=self.spider.settings['TIMEOUT'],connector=connector) as session:
                        if cookie_jar: session.cookie_jar.update_cookies(cookie_jar,URL(request.url))
                        if cookies: session.cookie_jar.update_cookies(cookies, URL(request.url))
                        url=request.url
                        data=request.data
                        headers=request.headers
                        proxy=request.proxy
                        async with session.post(url=url,data=data,headers=headers,proxy=proxy,timeout=self.spider.settings['TIMEOUT'],allow_redirects=request.allow_redirects) as response:
                            if response.status in self.spider.settings['ALLOW_STATUS']:

                                content = await response.read()
                                if response.cookies: session.cookie_jar.update_cookies(response.cookies)
                                sesson_cookies = {}
                                for i in session.cookie_jar:
                                    sesson_cookies[i.key] = i.value
                                url=response.url
                                headers=dict(response.headers)
                                cookies = response.cookies
                                status =response.status
                                charset = response.charset
                                signal={'startsleep':self.spider.startsleep}
                                _response=Response(url=url,headers=headers,request=request,content=content,cookies=cookies,status=status,charset=charset,signal=signal,proxy=proxy,sesson_cookies=sesson_cookies)
                                _response=await self.middleware(response=_response)


                                await self.response_push(_response,properties)

                                self.log.logging.debug(
                                    'response status:%s from POST url:%s' % (response.status, response.url))
                                self.success_count+=1
                                self.spider_messages_copy[response.status]=self.spider_messages_copy.get(response.status,0)+1


                            else:
                                self.log.logging.warning(
                                    'response status:%s from POST url:%s proxy:%s data:%s' % (
                                    response.status, response.url, proxy,data))
                                await self.ip_remove(proxy,self.spider.settings['POOL_NAME'])
                                request.retry += 1
                                if request.allow_proxy:
                                    request.proxy = None
                                result=await self.request_push(request)
                                if not result:
                                    self.spider_messages_copy[response.status] = self.spider_messages_copy.get(response.status,
                                                                                                           0) + 1
                except Exception as e:
                    self.log.logging.warning(e)
                    if session:
                        await session.close()
                    await self.ip_remove(request.proxy, self.spider.settings['POOL_NAME'])
                    request.retry += 1
                    if request.allow_proxy:
                        request.proxy = None
                    result=await self.request_push(request)
                    if not result:
                        self.spider_messages_copy['error'] = self.spider_messages_copy.get('error', 0) + 1

            elif request.method=='GET':
                cookies = request.cookies
                cookie_jar = request.cookie_jar
                session=None
                try:
                    async with ClientSession(cookies=cookies,connector=connector,conn_timeout=self.spider.settings['TIMEOUT']) as session:
                        if cookie_jar: session.cookie_jar.update_cookies(cookie_jar,URL(request.url))
                        if cookies: session.cookie_jar.update_cookies(cookies, URL(request.url))
                        url = request.url
                        params = request.params
                        headers = request.headers
                        proxy = request.proxy
                        async with session.get(url=url,params=params,headers=headers,proxy=proxy,timeout=self.spider.settings['TIMEOUT'],allow_redirects=request.allow_redirects) as response:
                            if response.status in self.spider.settings['ALLOW_STATUS']:
                                content = await response.read()
                                if response.cookies: session.cookie_jar.update_cookies(response.cookies)
                                sesson_cookies={}
                                for i in session.cookie_jar:
                                    sesson_cookies[i.key]=i.value
                                url=response.url
                                headers = dict(response.headers)
                                cookies = response.cookies
                                status =response.status
                                charset = response.charset
                                signal = {'startsleep': self.spider.startsleep}
                                _response=Response(url=url,headers=headers,request=request,content=content,cookies=cookies,status=status,charset=charset,signal=signal,proxy=proxy,sesson_cookies=sesson_cookies)
                                _response = await self.middleware(response=_response)
                                await self.response_push(_response, properties)
                                self.log.logging.debug(
                                    'response status:%s from GET url:%s' % (response.status, response.url))
                                self.success_count += 1
                                self.spider_messages_copy[response.status] = self.spider_messages_copy.get(response.status,
                                                                                                           0) + 1
                            else:
                                self.log.logging.warning(
                                    'response status:%s from GET url:%s proxy:%s' % (response.status, response.url,proxy))
                                await self.ip_remove(proxy, self.spider.settings['POOL_NAME'])
                                request.retry += 1
                                if request.allow_proxy:
                                    request.proxy=None
                                result = await self.request_push(request)
                                if not result:
                                    self.spider_messages_copy[response.status] = self.spider_messages_copy.get(
                                        response.status,
                                        0) + 1

                except Exception as e:
                    self.log.logging.warning(e)
                    if session:
                        await session.close()
                    await self.ip_remove(request.proxy, self.spider.settings['POOL_NAME'])
                    request.retry += 1
                    if request.allow_proxy:
                        request.proxy = None
                    result = await self.request_push(request)
                    if not result:
                        self.spider_messages_copy['error'] = self.spider_messages_copy.get('error', 0) + 1
            
            self.heartbeat_check()

    async def middleware(self,request=None,response=None):
        if request:
            if request.allow_proxy and  not request.proxy:
                request.proxy=await self.get_ip(request.url)
            return request
        if response :
            if response.request.allow_proxy:
                response.request.proxy=None
            if response.proxy:
                if response.status in self.spider.settings['ACTIVE_PROXYCODE']:
                    await self.ip_push(response.proxy,self.spider.settings['POOL_NAME'])
                else:
                    await self.ip_remove(response.proxy,self.spider.settings['POOL_NAME'])
            return response




    async def ip_push(self,ip,pool_name=None):
        if ip:
            ip=ip[7:]
            if pool_name:
                await self.redis_conn.zadd(pool_name, int(time.time()), ip)

            else:
                await self.redis_conn.zadd(self.spider.name, int(time.time()), ip)
    async def ip_remove(self,ip,pool_name=None):
        if ip:
            ip=ip[7:]
            if pool_name:
                await self.redis_conn.zrem(pool_name,ip)
            else:
                await self.redis_conn.zrem(self.spider.name,ip)

    async def get_ip(self,url):
        if self.spider.settings['ALLOW_PROXY']:
            ip_list=await self.get_ippool()
            if url.startswith('https'):
                return 'http://'+random.choice(ip_list)
            else:
                return 'http://' + random.choice(ip_list)
        else:
            return None

    async def get_ippool(self):
        ip_list =['106.12.192.6:8089','106.12.203.241:8089','106.12.88.84:8089','182.61.58.206:8089','106.12.120.235:8089','106.12.192.251:8089','106.12.10.251:8089','106.12.85.4:8089',
'182.61.22.107:8089','134.175.187.209:8089','140.143.140.196:8089','140.143.33.121:8089','129.28.68.157:8089','132.232.45.158:8089','94.191.9.189:8089',
   '94.191.4.160:8089','115.159.209.40:8089','118.89.156.161:8089','106.12.199.35:8089','106.12.199.151:8089','106.12.199.161:8089','106.12.128.78:8089','106.12.128.102:8089',
   '106.12.31.86:8089','106.12.83.54:8089','106.12.133.155:8089','106.12.128.176:8089','106.12.89.102:8089','106.12.199.170:8089','106.12.128.179:8089','106.12.133.218:8089',
   '106.12.133.222:8089','106.12.199.214:8089','106.12.134.168:8089','106.12.134.175:8089','106.12.85.211:8089','106.12.133.224:8089','106.12.101.33:8089','106.12.210.101:8089',
   '106.12.202.115:8089', '106.12.101.239:8089','106.12.89.250:8089','106.12.90.57:8089','182.61.27.83:8089','106.12.204.18:8089','106.12.90.3:8089','182.61.49.100:8089',
   '106.12.204.65:8089','182.61.30.168:8089','106.12.199.181:8089','106.12.8.69:8089']
        return ip_list






    # 创建将request压入队列的channel
    async def newrequest_channel(self, protocol):
        channel = await protocol.channel()
        await channel.queue_declare(queue_name=self.spider.routing_key,
                                    arguments={'x-max-priority': (self.spider.settings['X_MAX_PRIORITY'] or 0)},durable=True)
        self.requestchannel = channel

    # 创建将response压入队列的channel
    async def newresponse_channel(self, protocol):
        channel = await protocol.channel()
        await channel.queue_declare(queue_name=self.spider.name + '_response',
                                    arguments={'x-max-priority': (self.spider.settings['X_MAX_PRIORITY'] or 0)},durable=True)
        self.responsechannel = channel

    async def request_push(self, request):
        while 1:
            assert isinstance(request, Request), 'Request is need,%s is given' % type(request)
            if not self.spider.settings['RETRY'] or request.retry <= self.spider.settings['RETRY']:
                properties = Properties(priority=request.priority, delivery_mode=2, )
                try:
                    await self.requestchannel.basic_publish(exchange_name='',
                                                            routing_key=self.spider.routing_key,
                                                            properties=properties.keys(),
                                                            payload=pickle.dumps(request))  # 消息内容
                    return 1
                except Exception as e:
                    print(e)
                    return

            else:
                print('_________________________________________________________________')
                return 0

    async def response_push(self, response, properties):
        while 1:
            assert isinstance(response, Response), 'Response is need,%s is given' % type(response)
            try:
                await self.responsechannel.basic_publish(exchange_name='',
                                                         routing_key='%s_response' % self.spider.name,  # queue名字
                                                         properties=properties.keys(),
                                                         payload=pickle.dumps(response))  # 消息内容
                return
            except Exception as e:
                print(e)
                return


    async def redis_pool(self,loop):
                
        if self.spider.settings['ALLOW_PROXY']:
            redis = await aioredis.create_redis_pool(
               'redis://127.0.0.1:6379',
                minsize=5, maxsize=10,
                loop=loop)
            self.redis_conn=redis


    def run(self):


        @asyncio.coroutine
        def callback(channel, body, envelope, properties):
            
            if self.spider_status[0]==2:
                self.breakup=True
                while 1:
                    yield from asyncio.sleep(3)

                    print('还有%s个请求没返回'%((self.spider.settings['CONCURRENT_NUMS'] - self.sem._value)))
                    if (self.spider.settings['CONCURRENT_NUMS'] - self.sem._value)==0:
                        self.spider_status[0]=0
                        self.spider_messages.put(self.spider_messages_copy)
                        new_loop.stop()
            while self.sem._value<=3:
                print('self.sem._value:%s'%self.sem._value)
                yield from asyncio.sleep(3)
            yield from channel.basic_client_ack(delivery_tag=envelope.delivery_tag)
            request=pickle.loads(body)
            request=yield from self.middleware(request)
            asyncio.run_coroutine_threadsafe(self.worker(request, new_loop), new_loop)









        async def mqworker():
           
           try:
                while 1:
                    try:
                        self.transport, self.protocol = await aioamqp.connect('127.0.0.1', 5672)
                        break
                    except aioamqp.AmqpClosedConnection:
                        print("closed connections")
                        #return
                await self.newrequest_channel(self.protocol)
                await self.newresponse_channel(self.protocol)
                
                channel = await self.protocol.channel()
                print('8888888888888888888888888888')
                await channel.queue(queue_name=self.spider.routing_key, durable=True,arguments={'x-max-priority':(self.spider.settings['X_MAX_PRIORITY'] or 0)})
                await channel.basic_qos(prefetch_count=1)
                self.log.logging.info('生产者启动成功')
                await channel.basic_consume(callback, queue_name=self.spider.routing_key)
           except Exception as e:
               print(123,e)

        
        new_loop = asyncio.new_event_loop()
        
        t1 = threading.Thread(target=self.start_loop, args=(new_loop,))
        t2=threading.Thread(target=self.heartbeat)
        
        
        t1.start()
        t2.start()
               
        asyncio.run_coroutine_threadsafe(self.redis_pool(new_loop), new_loop)
        
        asyncio.run_coroutine_threadsafe(mqworker(), new_loop)
        t1.join()
        t2.join() 








    def heartbeat_check(self):
        if not self.spider.debug:
            if time.time()-self.last_see>self.spider.settings['HEART_BEAT']-3 and not (self.spider.settings['CONCURRENT_NUMS'] - self.sem._value):
                self.spider_status[0] = 0
                self.spider_messages.put(self.spider_messages_copy)
                self.last_see = time.time()
            elif not self.breakup:
                self.last_see=time.time()
                if not self.spider_status[0]:
                    self.spider_status[0]=1

    def heartbeat(self):
        while 1:
            time.sleep(self.spider.settings['HEART_BEAT'])
            if self.spider_status[0]:
                self.log.logging.info('\nthe success request speed is %s/min\n'%(int(self.success_count/self.spider.settings['HEART_BEAT']*60)))
                self.success_count=0
            self.heartbeat_check()
            self.monitor()
            print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')



    def _setDNSCache(self):
        """ DNS缓存 """
        def _getaddrinfo(*args, **kwargs):
            if args in self._dnscache:
                return self._dnscache[args]
            else:
                self._dnscache[args] = socket._getaddrinfo(*args, **kwargs)
                return self._dnscache[args]
        if not hasattr(socket, '_getaddrinfo'):
            socket._getaddrinfo = socket.getaddrinfo
            socket.getaddrinfo = _getaddrinfo

import queue
import json
import pickle
from fake_useragent import UserAgent
from aiorequest import Request
from aioresponse import Response
from loaditems import MysqlTwistedPipeline
import pika
from aioCrawler.base_settings import Settings
from aioCrawler.log import SpiderLog
import redis
import time
class Spider(object):
    name = None
    custom_settings=None
    debug = False

    def __init__(self):
        if self.name==None:
            raise KeyError

        self.settings=Settings()
        self.settings.setmodule('aioCrawler.settings', priority='project')
        self.update_settings(self.settings)
        self.startsleep = self.settings['START_SLEEP']
        self.username=self.settings['MQ_USER']
        self.pwd=self.settings['MQ_PWD']
        self.mq_user_pwd=pika.PlainCredentials(self.username, self.pwd)
        self.connection_T = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', port=5672,credentials=self.mq_user_pwd,heartbeat=0,socket_timeout=30) # 默认端口5672，可不写
        )
        self.channel_T = self.connection_T.channel()
        self.channel_T.queue_declare(queue='%s_request'%self.name,arguments={'x-max-priority':(self.settings['X_MAX_PRIORITY'] or 0)},durable=True)
        self.channel_R = self.connection_T.channel()
        self.channel_R.queue_declare(queue='%s_response'%self.name,arguments={'x-max-priority':(self.settings['X_MAX_PRIORITY'] or 0)},durable=True)
        self.channel_S=self.connection_T.channel()
        self.channel_S.queue_declare(queue='%s_request' % self.name,
                                     arguments={'x-max-priority': (self.settings['X_MAX_PRIORITY'] or 0)},durable=True)
        self.log=SpiderLog(level_str=self.settings['LOG_LEVEL'],filename=self.settings['LOG_FILE'])
        redis_pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
        self.redis_conn = redis.StrictRedis(connection_pool=redis_pool)

    @classmethod
    def update_settings(cls, settings):
        settings.setdict(cls.custom_settings or {}, priority='spider')

    def start_request(self):
        pass

    def start_insert(self):
        self.Pipeline = MysqlTwistedPipeline(self)

    def parse(self,response):
        pass


    def push(self,request):
        while 1:
            assert isinstance(request,Request),'Request is need,%s is given'%type(request)
            if not self.settings['RETRY'] or request.retry<=self.settings['RETRY']:
                properties = pika.BasicProperties(priority=request.priority,delivery_mode = 2,)
                try:
                    self.channel_T.basic_publish(exchange='',
                                         routing_key=self.routing_key,
                                         properties=properties,
                                         body=pickle.dumps(request))  # 消息内容
                    return 1
                except Exception as e:
                    print(e)
                    if not self.connection_T.is_open:
                        self.reconnect()
                        self.newchannel(channel='request')
                    if not self.channel_T.is_open:
                        self.newchannel(channel='request')
            else:
                print('_________________________________________________________________')
                return 0


    def start_push(self,request):
        while 1:
            assert isinstance(request, Request), 'Request is need,%s is given' % type(request)
            properties = pika.BasicProperties(priority=request.priority,delivery_mode = 2)
            try:
                self.channel_S.basic_publish(exchange='',
                                             routing_key=self.routing_key,
                                             properties=properties,
                                             body=pickle.dumps(request))  # 消息内容
                return
            except Exception as e:
                print(e)
                if not self.connection_T.is_open:
                    self.reconnect()
                    self.newchannel(channel='start')
                if not self.channel_S.is_open:
                    self.newchannel(channel='start')


    def response_push(self,response,properties):
        while 1:
            assert isinstance(response, Response), 'Response is need,%s is given' % type(response)
            try:
                self.channel_R.basic_publish(exchange='',
                                                    routing_key='%s_response' % self.name,  # queue名字
                                                    properties=properties,
                                                    body=pickle.dumps(response))  # 消息内容
                return
            except Exception as e:
                print(e)
                if not self.connection_T.is_open:
                    self.reconnect()
                    self.newchannel(channel='response')
                if not self.channel_R.is_open:
                    self.newchannel(channel='response')


    def reconnect(self):
        self.connection_T = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', port=5672, credentials=self.mq_user_pwd, heartbeat=0,
                                      socket_timeout=30)  # 默认端口5672，可不写
        )


    def newchannel(self,channel):
        if channel=='start':
            self.channel_S = self.connection_T.channel()
            self.channel_S.queue_declare(queue='%s_request' % self.name,
                                         arguments={'x-max-priority': (self.settings['X_MAX_PRIORITY'] or 0)},durable=True)
        elif channel=='request':
            self.channel_T = self.connection_T.channel()
            self.channel_T.queue_declare(queue='%s_request' % self.name,
                                         arguments={'x-max-priority': (self.settings['X_MAX_PRIORITY'] or 0)},durable=True)
        elif channel == 'response':
            self.channel_R = self.connection_T.channel()
            self.channel_R.queue_declare(queue='%s_response' % self.name,
                                         arguments={'x-max-priority': (self.settings['X_MAX_PRIORITY'] or 0)},durable=True)

    def ip_push(self,ip,pool_name=None):
        if ip:
            ip=ip[7:]
            if pool_name:
                self.redis_conn.zadd(pool_name, int(time.time()), ip)
            else:
                self.redis_conn.zadd(self.name, int(time.time()), ip)
    def ip_remove(self,ip,pool_name=None):
        if ip:
            ip=ip[7:]
            if pool_name:
                self.redis_conn.zrem(pool_name,ip)
            else:
                self.redis_conn.zrem(self.name,ip)






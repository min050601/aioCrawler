import time
import pickle
import pika
import threading
import requests
import json
from pika.exceptions import ChannelClosed
from pika.exceptions import ConnectionClosed


class Base_customer(object):
    def __init__(self,spider,spider_status,q):
        self.balance=0
        self.breakup=False
        self.last_see = time.time()
        self.spider_status=spider_status
        self.spider_messages = q
        self.spider_messages_copy = {}
        self.spider=spider
        self.log = spider.log
        self.username = self.spider.settings['MQ_USER']
        self.pwd = self.spider.settings['MQ_PWD']
        self.mq_user_pwd = pika.PlainCredentials(self.username, self.pwd)
        self.connection_W = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', port=5672, credentials=self.mq_user_pwd,heartbeat=0,socket_timeout=30,)  # 默认端口5672，可不写
        )
        self.channel_R = self.connection_W.channel()
        self.channel_R.queue_declare(queue='%s_response'%self.spider.name,arguments={'x-max-priority':(self.spider.settings['X_MAX_PRIORITY'] or 0)},durable=True)


    def reconnect(self):
        self.connection_W = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost', port=5672, credentials=self.mq_user_pwd, heartbeat=0,
                                      socket_timeout=30, )  # 默认端口5672，可不写
        )


    def newchannel(self):
        self.channel_R = self.connection_W.channel()
        self.channel_R.queue_declare(queue='%s_response' % self.spider.name,
                                     arguments={'x-max-priority': (self.spider.settings['X_MAX_PRIORITY'] or 0)},durable=True)


    def heartbeat_check(self):
        if not self.spider.debug:
            if time.time()-self.last_see>self.spider.settings['HEART_BEAT']-3:
                self.spider_status[1]=0
                self.last_see = time.time()

            elif not self.breakup:
                self.last_see=time.time()
                if not self.spider_status[1]:
                    self.spider_status[1]=1


    def heartbeat(self):
        while 1:
            time.sleep(self.spider.settings['HEART_BEAT'])
            if self.spider_status[1]:
                self.log.logging.info(
                    '\nthe success insert speed is %s/min\n' % (int(self.spider.Pipeline.success_count / self.spider.settings['HEART_BEAT'] * 60)))
                self.spider.Pipeline.success_count=0
            self.heartbeat_check()





    def start(self):
        t=threading.Thread(target=self.heartbeat)
        t.start()
        def callback(ch, method, properties, body):  # 四个参数为标准格式
            # print(ch, method, properties)  # 打印看一下是什么
            # 管道内存对象
            if self.spider_status[1]==2:
                self.breakup=True
                while 1:
                    time.sleep(3)
                    print('还剩%s个任务'%self.balance)
                    if self.balance==0:
                        self.spider_status[1]=0
                        self.balance = -1


            self.balance+=1
            if self.spider_status[3]==0:
                self.spider_messages_copy['commit'] = self.spider.commit
                self.spider_messages_copy['failure'] = self.spider.failure
                self.spider_messages.put(self.spider_messages_copy)

            response = pickle.loads(body)
            res_callback=response.request.callback
            try:
                if response.signal.get('startsleep'):self.spider.startsleep=response.signal.get('startsleep')
                self.spider.__getattribute__(res_callback)(response)
                #ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                self.log.logging.exception(e)
            ch.basic_ack(delivery_tag=method.delivery_tag)    

            self.heartbeat_check()
            self.balance -= 1




        while 1:
            try:
                self.channel_R.basic_consume(  # 消费消息
                    callback,  # 如果收到消息，就调用callback函数来处理消息
                    queue='%s_response'%self.spider.name,  # 你要从那个队列里收消息
                    # no_ack=True  # 写的话，如果接收消息，机器宕机消息就丢了
                    # 一般不写。宕机则生产者检测到发给其他消费者
                )
                self.log.logging.info('消费者启动成功')
                self.channel_R.basic_qos(prefetch_count=1)
                self.channel_R.start_consuming()

            except ConnectionClosed as e:
                self.reconnect()
            except ChannelClosed as e:
                self.newchannel()
            except Exception as e:
                print(e)
                #if not self.connection_W.is_open:
                #    self.reconnect()
                #if not self.channel_R.is_open:
                #    self.newchannel()

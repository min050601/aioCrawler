import aiohttp
import asyncio
from urllib.parse import parse_qs
from aiohttp import web
from aiohttp import ClientSession
import time
import json
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,BASE_DIR)
import redis
import datetime
import hashlib
import aiomysql
import math
from actuator import LoadSpiders
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ProcessPoolExecutor
from runspider import run
import aiohttp_jinja2
import jinja2
import aiofiles
from aiohttp_session import get_session, setup
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from base64 import b64encode
os.environ["TF_CPP_MIN_LOG_LEVEL"]='3'
redis_pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
redis_conn = redis.StrictRedis(connection_pool=redis_pool)
job_defaults = {'coalesce': True,'max_instances':10}
executors = {'default': ProcessPoolExecutor(10)}
scheduler = BackgroundScheduler(executors=executors, job_defaults=job_defaults)
scheduler.add_jobstore('sqlalchemy', url='mysql+pymysql://root:root@127.0.0.1/sqlalchemy')


def get_sha1(salt):
    m=hashlib.sha1()
    if isinstance(salt,str):
        salt=salt.encode('utf-8')
    m.update(salt)
    return m.hexdigest()

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                session = await get_session(request)
                if session.get('AUTHORIZATIONUSERS'):
                    params=json.loads(msg.data)
                    filename=params.get('spider')
                    async with aiofiles.open('./logs/%s.log'%filename,'r') as file:
                    # file=open('./logs/%s.log'%filename,'r')
                        await file.seek(0, 2)
                        while 1:
                            ms=await file.readline()
                            if ms:
                                await ws.send_str(ms)
                            await asyncio.sleep(0.1)
                else:
                    await ws.send_str('请登录后查看！！！')
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws

async def mqwebsocket_handler(request):
    qws = web.WebSocketResponse()
    await qws.prepare(request)
    Authorization = b64encode(b'%s:%s' % ('wander'.encode(), 'Elements123'.encode())).decode()
    headers = {'Authorization': 'Basic %s' % Authorization}
    async for msg in qws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await qws.close()
            else:
                params=json.loads(msg.data)
                page=params.get('page')
                async with aiohttp.request(method='get',url='http://127.0.0.1:15672/api/queues?page=%s&page_size=100&name=&use_regex=false'%page,headers=headers) as resp:
                    if resp.status==200:
                        text = await resp.text()
                        result=json.loads(text)
                        item_count = result.get('item_count')
                        items=result.get('items',[])
                        resp_list=[]
                        for item in items:
                            mq_dict={}
                            mq_dict['name']=item.get('name')
                            features=''
                            if item.get('durable'):
                                features+='D'
                            if item.get('arguments').get('x-max-priority'):
                                features+='|Pri'
                            mq_dict['features']=features
                            mq_dict['state']=item.get('state')
                            mq_dict['ready'] = item.get('messages_ready')
                            mq_dict['unacked'] = item.get('messages_unacknowledged')
                            mq_dict['total'] = item.get('messages')
                            mq_dict['incoming'] = ('%s/s' if item.get('message_stats',{}).get('publish_details',{}).get('rate',0) else '%s')%item.get('message_stats',{}).get('publish_details',{}).get('rate',0)
                            mq_dict['deliver'] = ('%s/s' if item.get('message_stats', {}).get('deliver_get_details', {}).get('rate',0) else '%s')%item.get('message_stats', {}).get('deliver_get_details', {}).get('rate',0)
                            mq_dict['ack'] = ('%s/s' if item.get('message_stats', {}).get('ack_details', {}).get('rate',0) else '%s')%item.get('message_stats', {}).get('ack_details', {}).get('rate',0)
                            resp_list.append(mq_dict)
                        await qws.send_json({"items": resp_list, "totalPage": math.ceil(item_count/ 100)})


        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  qws.exception())

    print('websocket connection closed')

    return qws


async def detetemq(request):
    session = await get_session(request)
    if session.get('AUTHORIZATIONUSERS'):
        data = await request.post()
        name=data.get('name')
        if name:
            Authorization = b64encode(b'%s:%s' % ('wander'.encode(), 'Elements123'.encode())).decode()
            headers = {'Authorization': 'Basic %s' % Authorization}
            params = {"vhost": "/", "name": name, "mode": "delete"}
            async with aiohttp.request(method='delete', url='http://127.0.0.1:15672/api/queues/%2F/{}'.format(name),json=json.dumps(params),headers=headers) as resp:
                if resp.status == 204:
                    return web.Response(
                        body=json.dumps({'msg': 'true','remark':None}, ensure_ascii=False),
                        content_type='text/html')
                elif resp.status==404:
                    text = await resp.text()
                    result=json.loads(text)
                    return web.Response(
                        body=json.dumps({'msg': 'true','remark':result}, ensure_ascii=False),
                        content_type='text/html')


async def tasks(request):
    data = await request.post()
    page=int(data.get('page','1'))
    global __pool
    async with __pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT pid,spider,running_status,planned_status,start_time,id,plan,scheduler_id from spiderStatus")
            tasks = []
            result = await cur.fetchall()
            if (page-1)*20<len(result):
                for i in result[(page-1)*20:min(page*20,len(result))]:
                    tasks.append({'id':i[5],'pid': i[0], 'spider': i[1], 'running_status': i[2],
                                  'planned_status':i[3],'start_time': i[4].strftime('%Y-%m-%d:%H:%M:%S'),
                                  'spider_process':'结束' if i[2] else '启动','plan':i[6],'scheduler_id':i[7],'plan_process':'暂停' if i[3] else '恢复'})
                return web.Response(body=json.dumps({"result": tasks,"totalPage":math.ceil(len(result)/20)}, ensure_ascii=False), content_type='text/html')
            else:
                return web.Response(body=json.dumps({"result": tasks, "totalPage": 0}, ensure_ascii=False), content_type='text/html')


async def get_spiders(request):
    session = await get_session(request)
    if session.get('AUTHORIZATIONUSERS'):
        spiders = LoadSpiders()._spiders
        tasks = []
        for k,v in spiders.items():
            tasks.append({'spider':k})
        return web.Response(body=json.dumps(tasks, ensure_ascii=False), content_type='text/html')


async def runspider(request):
    session = await get_session(request)
    if session.get('AUTHORIZATIONUSERS'):
        data = await request.post()
        spider=data.get('spider')
        rule=data.get('rule')
        id=data.get('id')
        scheduler_id=spider+datetime.datetime.now().strftime('%Y-%m-%d:%H:%M:%S')
        print(spider,rule)
        if rule=='once':
            scheduler.add_job(func=run, args=(spider,rule,id,scheduler_id),trigger='date', run_date=datetime.datetime.now()+datetime.timedelta(seconds=1),id=scheduler_id)
        elif rule=='day':
            scheduler.add_job(func=run, args=(spider, rule, id,scheduler_id), trigger='date', run_date=datetime.datetime.now())
            scheduler.add_job(func=run, args=(spider, rule, id,scheduler_id), trigger='interval', days=1,id=scheduler_id)
        elif rule=='week':
            scheduler.add_job(func=run, args=(spider, rule, id,scheduler_id), trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=1))
            scheduler.add_job(func=run, args=(spider,rule,id,scheduler_id), trigger='interval', weeks=1,id=scheduler_id)
        elif rule=='month':
            scheduler.add_job(func=run, args=(spider, rule, id,scheduler_id), trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=1))
            scheduler.add_job(func=run, args=(spider,rule,id,scheduler_id), trigger='interval', days=30,id=scheduler_id)

        await asyncio.sleep(3)


        return web.Response(
                body=json.dumps({'msg': 'true', 'url': '/user'}, ensure_ascii=False),
                content_type='text/html')


async def plan_process(request):
    session = await get_session(request)
    if session.get('AUTHORIZATIONUSERS'):
        data = await request.post()
        id = data.get('id')
        status = data.get('status')
        global __pool
        async with __pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("select plan from spiderStatus where scheduler_id=%s", (id,))
                result = await cur.fetchone()
                if result[0]!='once':
                    if int(status):
                        if scheduler.get_job(id):
                            scheduler.pause_job(id)
                    else:
                        if scheduler.get_job(id):
                            scheduler.resume_job(id)
                    await cur.execute("update spiderStatus set planned_status=%s where scheduler_id=%s", (0 if int(status) else 1,id))
                return web.Response(body=json.dumps({"msg": "true", "url": "/user"}, ensure_ascii=False), content_type='text/html')



async def spider_process(request):
    session = await get_session(request)
    if session.get('AUTHORIZATIONUSERS'):
        data = await request.post()
        id=data.get('id')
        status=data.get('status')
        global __pool
        if int(status):

            async with __pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("update spiderStatus set running_status=%s where id=%s",(0,id))
                    return web.Response(body=json.dumps({"msg": "true", "url": "/user"}, ensure_ascii=False), content_type='text/html')
        else:

            async with __pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("select spider,plan,scheduler_id from spiderStatus where id=%s", (id,))
                    result = await cur.fetchone()
                    scheduler_id=result[2]
                    rule=result[1]
                    spider=result[0]
                    if rule == 'once':
                        scheduler.add_job(func=run, args=(spider, rule, id), trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=1),id=scheduler_id)
                    elif rule == 'day':
                        if scheduler.get_job(scheduler_id):
                            scheduler.remove_job(scheduler_id)
                        scheduler.add_job(func=run, args=(spider, rule, id), trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=1))
                        scheduler.add_job(func=run, args=(spider, rule, id), trigger='interval', days=1,id=scheduler_id)
                    elif rule == 'week':
                        if scheduler.get_job(scheduler_id):
                            scheduler.remove_job(scheduler_id)
                        scheduler.add_job(func=run, args=(spider, rule, id), trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=1))
                        scheduler.add_job(func=run, args=(spider, rule, id), trigger='interval', weeks=1,id=scheduler_id)
                    elif rule == 'month':
                        if scheduler.get_job(scheduler_id):
                            scheduler.remove_job(scheduler_id)
                        scheduler.add_job(func=run, args=(spider, rule, id), trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=1))
                        scheduler.add_job(func=run, args=(spider, rule, id), trigger='interval', days=30,id=scheduler_id)
                    await asyncio.sleep(3)
                    return web.Response(body=json.dumps({"msg": "true", "url": "/user"}, ensure_ascii=False), content_type='text/html')


async def deletespider(request):
    session = await get_session(request)
    if session.get('AUTHORIZATIONUSERS'):
        data = await request.post()
        id=data.get('id')
        scheduler_id=data.get('scheduler_id')
        if scheduler_id:
            if scheduler.get_job(scheduler_id):
                scheduler.remove_job(scheduler_id)
        if id:
            global __pool
            async with __pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("delete from spiderStatus where id=%s", (id,))
                    # await conn.commit()
                    return web.Response(body=json.dumps({"msg": "true", "url": "/user"}, ensure_ascii=False), content_type='text/html')


@aiohttp_jinja2.template('home.html')
async def home(request):
    session = await get_session(request)
    if session.get('AUTHORIZATIONUSERS'):
        return {"__user__":{'name': session['AUTHORIZATIONUSERS']}}
    else:
        return {}

@aiohttp_jinja2.template('signin.html')
async def login(request):
    return


async def login1(request):
    session = await get_session(request)
    data = await request.post()
    email=data.get('email')
    passwd=data.get('passwd')
    global __pool
    async with __pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("select email from authorizationusers where passwd=%s", (passwd,))
            result = await cur.fetchone()
            if result[0]==email:
                session['AUTHORIZATIONUSERS'] = email
                return web.Response(body=json.dumps({'msg': 'true', 'url': '/user'}, ensure_ascii=False), content_type='text/html')
            else:
                return web.Response(body=json.dumps({'msg': 'false'}, ensure_ascii=False), content_type='text/html')

async def logout(request):
    session = await get_session(request)
    session['AUTHORIZATIONUSERS'] = None
    return web.Response(body=json.dumps({'msg': 'true', 'url': '/login'}, ensure_ascii=False), content_type='text/html')


async def create_pool(loop, **kw):
    global __pool
    __pool = await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port', 3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset', 'utf8'),
        autocommit=kw.get('autocommit', True),
        maxsize=kw.get('maxsize', 10),
        minsize=kw.get('minsize', 1),
        loop=loop
    )

async def init(loop,port):
    app = web.Application(loop=loop)
    setup(app,
          EncryptedCookieStorage(b'Thirty  two  length  bytes  key.'))
    aiohttp_jinja2.setup(app,
                         loader=jinja2.FileSystemLoader('D:/aioCrawler/aioCrawler/template'))

    app.router.add_route('POST', '/runspider', runspider)

    app.router.add_route('POST', '/spider_process', spider_process)
    app.router.add_route('POST', '/tasks', tasks)
    app.router.add_route('POST', '/plan_process', plan_process)

    app.router.add_route('GET', '/user', home)
    app.router.add_route('POST', '/get_spiders', get_spiders)
    app.router.add_route('POST','/deletemq',detetemq)
    app.router.add_route('POST','/deletespider',deletespider)
    app.router.add_route('GET', '/login', login)
    app.router.add_route('POST', '/api/login', login1)
    app.router.add_route('POST', '/logout', logout)
    app.router.add_route('GET', '/', login)
    app.router.add_static('/static/',
                        path='D:/aioCrawler/aioCrawler/static',
                        name='static')
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/qws', mqwebsocket_handler)
    database = {
        'host': '127.0.0.1',  # 数据库的地址
        'user': 'root',
        'password': 'root',
        'db': 'aioCrawler'
    }
    await create_pool(loop=loop,**database)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', int(port))
    print('Server started at http://127.0.0.1:%s...'%port)
    scheduler.start()
    return srv


if __name__=="__main__":
    # import argparse
    # from argparse import ArgumentDefaultsHelpFormatter
    #
    # parser = argparse.ArgumentParser(prog="aiohttpWeb", description='the website for geetest',
    #                                  formatter_class=ArgumentDefaultsHelpFormatter)
    #
    # parser.add_argument('-p', dest='port', action='store', required=True, default=8000,
    #                     help='the port listen')
    #
    # args = parser.parse_args()
    # loop = asyncio.get_event_loop()
    # loop.run_until_complete(init(loop,args.port))
    # loop.run_forever()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init(loop, 8000))
    loop.run_forever()

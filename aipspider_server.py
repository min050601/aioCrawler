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
from runspider import run
import aiohttp_jinja2
import jinja2
import aiofiles
os.environ["TF_CPP_MIN_LOG_LEVEL"]='3'
redis_pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
redis_conn = redis.StrictRedis(connection_pool=redis_pool)
scheduler = BackgroundScheduler()
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
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                  ws.exception())

    print('websocket connection closed')

    return ws




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
    spiders = LoadSpiders()._spiders
    tasks = []
    for k,v in spiders.items():
        tasks.append({'spider':k})
    return web.Response(body=json.dumps(tasks, ensure_ascii=False), content_type='text/html')


async def runspider(request):
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
                    scheduler.pause_job(id)
                else:
                    scheduler.resume_job(id)
                await cur.execute("update spiderStatus set planned_status=%s where scheduler_id=%s", (0 if int(status) else 1,id))
            return web.Response(body=json.dumps({"msg": "true", "url": "/user"}, ensure_ascii=False), content_type='text/html')



async def spider_process(request):
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
                    scheduler.remove_job(scheduler_id)
                    scheduler.add_job(func=run, args=(spider, rule, id), trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=1))
                    scheduler.add_job(func=run, args=(spider, rule, id), trigger='interval', days=1,id=scheduler_id)
                elif rule == 'week':
                    scheduler.remove_job(scheduler_id)
                    scheduler.add_job(func=run, args=(spider, rule, id), trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=1))
                    scheduler.add_job(func=run, args=(spider, rule, id), trigger='interval', weeks=1,id=scheduler_id)
                elif rule == 'month':
                    scheduler.remove_job(scheduler_id)
                    scheduler.add_job(func=run, args=(spider, rule, id), trigger='date', run_date=datetime.datetime.now() + datetime.timedelta(seconds=1))
                    scheduler.add_job(func=run, args=(spider, rule, id), trigger='interval', days=30,id=scheduler_id)
                await asyncio.sleep(3)
                return web.Response(body=json.dumps({"msg": "true", "url": "/user"}, ensure_ascii=False), content_type='text/html')


@aiohttp_jinja2.template('home.html')
async def home(request):
    return







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
    aiohttp_jinja2.setup(app,
                         loader=jinja2.FileSystemLoader('/root/wander/git_local/aioCrawler/template'))

    app.router.add_route('POST', '/runspider', runspider)

    app.router.add_route('POST', '/spider_process', spider_process)
    app.router.add_route('POST', '/tasks', tasks)
    app.router.add_route('POST', '/plan_process', plan_process)

    app.router.add_route('GET', '/user', home)
    app.router.add_route('POST', '/get_spiders', get_spiders)
    # app.router.add_static('/static/',
    #                      path='D:/aioCrawler/aioCrawler/static',
    #                      name='static')
    app.router.add_get('/ws', websocket_handler)
    database = {
        'host': '127.0.0.1',  # 数据库的地址
        'user': 'root',
        'password': 'Elements123',
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
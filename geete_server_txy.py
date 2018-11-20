
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
from scrapy import Selector
from yarl import URL
from actuator import LoadSpiders
from apscheduler.schedulers.background import BackgroundScheduler
from runspider import run
import aiohttp_jinja2
import jinja2
os.environ["TF_CPP_MIN_LOG_LEVEL"]='3'
redis_pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
redis_conn = redis.StrictRedis(connection_pool=redis_pool)
# detecotr = TOD()
challenge_session=ClientSession()
scheduler = BackgroundScheduler()
scheduler.add_jobstore('sqlalchemy', url='mysql+pymysql://root:root@127.0.0.1/sqlalchemy')
scheduler.start()
def get_sha1(salt):
    m=hashlib.sha1()
    if isinstance(salt,str):
        salt=salt.encode('utf-8')
    m.update(salt)
    return m.hexdigest()





async def getkey(request):
    #客户端ip
    user_ip=request.remote
    qs = request.query_string
    if qs:
        kw = dict()
        for k, v in parse_qs(qs, True).items():
            kw[k] = v[0]
        #账户
        user=kw.get('user')
        #密码
        passwd=kw.get('passwd')
        #时间戳
        timestamp=kw.get('t')
        #验证账户是否有效，并获取剩余调用次数
        pass
        global __pool
        async with __pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id,account from usersrecord where `user`=%s and passwd=%s",(user,passwd))
                result= await cur.fetchone()
                if not result:
                    return web.Response(body=json.dumps(
                                {"userkey": None, "status": "fail",
                                 "log": "无效账户"},
                                ensure_ascii=False).encode(
                                'utf-8'), content_type='text/html', charset='UTF-8')
                else:
                    id=result[0]
                    account=result[1]
                    userkey=get_sha1(user+passwd+str(timestamp))
                    redis_conn.set(userkey,json.dumps({'id':id,'user':user,'passwd':passwd,'user_ip':user_ip,'account':account},ensure_ascii=False))
                    #设置key失效时间为一小时
                    redis_conn.expire(userkey,3600)
                    return web.Response(body=json.dumps(
                        {"userkey": userkey, "status": "success",'account':account,
                         "log": "请用相同的ip调用api"},
                        ensure_ascii=False).encode(
                        'utf-8'), content_type='text/html', charset='UTF-8')
                print(result)
    if challenge_session.closed:
        challenge_session=ClientSession()
    headers = {'Accept': 'application/json, text/javascript, */*; q=0.01',
               'Accept-Encoding': 'gzip, deflate, sdch',
               'Accept-Language': 'zh-CN,zh;q=0.8',
               'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:21.0) Gecko/20100101 Firefox/21.0',
               'Connection': 'keep-alive',
               'Referer':'http://www.gsxt.gov.cn/index.html',
               'X-Requested-With':'XMLHttpRequest'}

    cookie={}
    while 1:
        if cookie:challenge_session.cookie_jar.update_cookies(cookie, URL('http://www.gsxt.gov.cn/'))
        url='http://www.gsxt.gov.cn/SearchItemCaptcha?t=%s' % (int(time.time() * 1000))
        print(url)
        async with challenge_session.get(
                url=url,
                headers=headers,proxy='http://127.0.0.1:8888') as resp:
            if resp.status == 521:
                response = await resp.text()
                selector = Selector(text=response)
                js_content = selector.xpath("//script/text()").extract_first('')
                __jsl_clearance = ex_js(js_content).split('=')[-1]
                cookie = {'__jsl_clearance':__jsl_clearance}
            elif resp.status==200:
                response = await resp.text()
                return web.Response(body=response, content_type='text/html')

@aiohttp_jinja2.template('register.html')
async def register(request):
    return

async def register1(request):
    info = await request.text()
    kw = dict()
    for k, v in parse_qs(info, True).items():
        kw[k] = v[0]
    email=kw.get('email')
    passwd=kw.get('passwd')
    if redis_conn.hexists('users_pool',email):
        return web.Response(body=json.dumps({'msg':'用户已存在'},ensure_ascii=False),content_type='text/html')
    redis_conn.hset('users_pool',email,passwd)
    redis_conn.hset('gsxt_users', passwd, 0)
    log={'today_cross': 0, 'today_get': 0, 'hist_get': 0, 'hist_cross': 0, 'cross_rate': 0}
    redis_conn.hset('gsxt_usersLog', passwd, json.dumps(log, ensure_ascii=False))
    return web.Response(body=json.dumps({'msg':'true'},ensure_ascii=False),content_type='text/html')

async def login1(request):
    info = await request.text()
    kw = dict()
    for k, v in parse_qs(info, True).items():
        kw[k] = v[0]
    email=kw.get('email')
    passwd=kw.get('passwd')
    if redis_conn.hexists('users_pool',email):
        check_passwd=redis_conn.hget('users_pool',email)
        if check_passwd.decode()!=passwd:
            return web.Response(body=json.dumps({'msg':'false'},ensure_ascii=False),content_type='text/html')
        else:
            return web.Response(body=json.dumps({'msg': 'true','url':'/user?email=%s&userkey=%s'%(email,passwd)}, ensure_ascii=False), content_type='text/html')
    return web.Response(body=json.dumps({'msg':'false'},ensure_ascii=False),content_type='text/html')

@aiohttp_jinja2.template('signin.html')
async def login(request):
    return


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
    global __pool
    async with __pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT pid,spider,running_status,planned_status,start_time from spiderStatus")
            tasks=[]
            result = await cur.fetchall()
            for i in result:
                tasks.append({'pid':i[0],'spider':i[1],'running_status':i[2],'planned_status':i[3],'start_time':i[4]})
            return {"result": tasks}

    qs = request.query_string
    if qs:
        kw = dict()
        for k, v in parse_qs(qs, True).items():
            kw[k] = v[0]
        userkey = kw.get('userkey')
        email = kw.get('email')
        account=redis_conn.hget('gsxt_users',userkey)
        if account==None:
            account=b'0'
        return {'__user__':{'name':email},'userkey': userkey, 'account': account.decode(),'logUrl':'/log?email=%s&userkey=%s'%(email,userkey),'userUrl':'/user?email=%s&userkey=%s'%(email,userkey)}



@aiohttp_jinja2.template('blogs.html')
async def log(request):
    qs = request.query_string
    if qs:
        kw = dict()
        for k, v in parse_qs(qs, True).items():
            kw[k] = v[0]
        userkey = kw.get('userkey')
        email = kw.get('email')
        log = json.loads((redis_conn.hget('gsxt_usersLog', userkey) or '{}'))
        if log.get('today') != datetime.datetime.now().strftime("%Y-%m-%d"):
            log['today_get'] = 0
            log['today_cross'] = 0
            log['today'] = datetime.datetime.now().strftime("%Y-%m-%d")
        log['__user__']={'name':email}
        log['logUrl'] = '/log?email=%s&userkey=%s'%(email,userkey)
        log['userUrl'] = '/user?email=%s&userkey=%s'%(email,userkey)
        return log


@aiohttp_jinja2.template('admin.html')
async def admin(request):
    return

async def admin1(request):
    info = await request.text()
    kw = dict()
    for k, v in parse_qs(info, True).items():
        kw[k] = v[0]
    email=kw.get('email')
    passwd=kw.get('passwd')
    if email=='min050601@163.com' and passwd=='8eb3fb9e2825b3674805b7ee20c04e4f7ad44dbb':
        return web.Response(
            body=json.dumps({'msg': 'true', 'url': '/adminUser?email=%s&userkey=%s' % (email, passwd)}, ensure_ascii=False),
            content_type='text/html')
    else:
        return web.Response(body=json.dumps({'msg': 'false'}, ensure_ascii=False), content_type='text/html')

@aiohttp_jinja2.template('adminUser.html')
async def adminUser(request):
    qs = request.query_string
    if qs:
        kw = dict()
        for k, v in parse_qs(qs, True).items():
            kw[k] = v[0]
        userkey = kw.get('userkey')
        email = kw.get('email')
        if email == 'min050601@163.com' and userkey == '8eb3fb9e2825b3674805b7ee20c04e4f7ad44dbb':
            params=redis_conn.hgetall('gsxt_users')
            if params:
                result=[]
                for k,v in params.items():
                    result.append({'userkey':k.decode(),'account':v.decode()})
                return {"result":result,'__user__':{'name':'admin'},'changeAccount':'/changeAccount?email=%s&userkey=%s'%(email,userkey)}

        # account=redis_conn.hget('gsxt_users',userkey)
        # if account==None:
        #     account=b'0'
        # return {'__user__':{'name':email},'userkey': userkey, 'account': account.decode(),'logUrl':'/log?email=%s&userkey=%s'%(email,userkey),'userUrl':'/user?email=%s&userkey=%s'%(email,userkey)}


@aiohttp_jinja2.template('changeAccount.html')
async def changeAccount(request):
    qs = request.query_string
    if qs:
        kw = dict()
        for k, v in parse_qs(qs, True).items():
            kw[k] = v[0]
        userkey = kw.get('userkey')
        email = kw.get('email')
    return {'url1':'/changeAccount1?email=%s&userkey=%s'%(email,userkey)}

async def changeAccount1(request):
    qs = request.query_string
    if qs:
        kw = dict()
        for k, v in parse_qs(qs, True).items():
            kw[k] = v[0]
        userkey = kw.get('userkey')
        email = kw.get('email')
        if email=='min050601@163.com' and userkey=='8eb3fb9e2825b3674805b7ee20c04e4f7ad44dbb':
            info = await request.text()
            kw1 = dict()
            for k, v in parse_qs(info, True).items():
                kw1[k] = v[0]
            userkey1=kw1.get('userkey')
            nums = kw1.get('nums')
            account = redis_conn.hincrby('gsxt_users', userkey1, int(nums))
            return web.Response(
                body=json.dumps({'msg': 'true', 'url': '/adminUser?email=%s&userkey=%s' % (email, userkey)}, ensure_ascii=False),
                content_type='text/html')
        else:
            return web.Response(body=json.dumps({'msg': 'false'}, ensure_ascii=False), content_type='text/html')


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
                         loader=jinja2.FileSystemLoader(r'D:\aioCrawler\aioCrawler\template'))
    app.router.add_route('GET', '/', register)
    app.router.add_route('POST', '/runspider', runspider)
    app.router.add_route('GET', '/adminUser', adminUser)
    app.router.add_route('POST', '/spider_process', spider_process)
    app.router.add_route('POST', '/tasks', tasks)
    app.router.add_route('POST', '/plan_process', plan_process)
    app.router.add_route('GET', '/log', log)
    app.router.add_route('GET', '/getkey', getkey)
    app.router.add_route('GET', '/user', home)
    app.router.add_route('POST', '/api/users', register1)
    app.router.add_route('POST', '/get_spiders', get_spiders)
    app.router.add_static('/static/',
                         path='D:/aioCrawler/aioCrawler/static',
                         name='static')
    app.router.add_route('GET', '/register', register)
    app.router.add_route('GET', '/login', login)
    database = {
        'host': '127.0.0.1',  # 数据库的地址
        'user': 'root',
        'password': 'root',
        'db': 'aiocrawler'
    }
    await create_pool(loop=loop,**database)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', int(port))
    print('Server started at http://127.0.0.1:%s...'%port)
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
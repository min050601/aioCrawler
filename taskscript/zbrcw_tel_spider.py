# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from fake_useragent import UserAgent
import json
import time
user_agent=UserAgent()



class ZbrcwTelSpiderSpider(Spider):
    name = 'zbrcw_tel_spider'
    routing_key='zbrcw_tel_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 20, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}


    def start_request(self):
        for i in range(626207,0,-1):
            url = 'https://m.jobcn.com/wxapp/getComInfo.ujson?m.comId=%s'%i
            data = {'page': i}
            headers = {'User-Agent': user_agent.random}
            request=Request(url=url,method='GET',headers=headers,data=data,callback='parse',allow_proxy=False,allow_redirects=False,timeout=30)
            self.start_push(request)
            time.sleep(0.06)



    def parse(self,response):
        if response.status==200:
            result=json.loads(response.content)
            body=result.get('body',{})
            comInfo=body.get('comInfo',{})
            entname=comInfo.get('comName')
            if not entname:
                print(response.request.url,None)
                return
            address=comInfo.get('address')
            email=comInfo.get('email')
            logoUrl=comInfo.get('logoUrl')
            tel=comInfo.get('tel')
            website=comInfo.get('homePage')
            contact=comInfo.get('contactPerson')
            insert_sql='''insert into zbrcw_tel (entname,contact,tel,email,address,website,logoUrl,url)VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (entname,contact,tel,email,address,website,logoUrl,response.request.url)))

        pass

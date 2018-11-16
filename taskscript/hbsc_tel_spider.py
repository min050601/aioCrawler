# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from fake_useragent import UserAgent
import json
import time
from w3lib.html import remove_tags
user_agent=UserAgent()


class HbscTelSpiderSpider(Spider):
    name = 'hbsc_tel_spider'
    routing_key='hbsc_tel_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 20, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}


    def start_request(self):
        for i in range(2140000,1,-1):
            url = 'http://www.hbsc.cn/ashx/Corp/GetContact.ashx?id=%s&_=0.7466502927798564'%i

            headers = {
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'http://www.hbsc.cn/corp/corpinfo-%s.html'%i,
                'User-Agent': user_agent.random}
            request=Request(url=url,method='GET',headers=headers,callback='parse',allow_redirects=False,allow_proxy=False,timeout=40)
            self.start_push(request)
            time.sleep(0.03)



    def parse(self,response):
        if response.status==200:
            print(response.request.url)
            if response.content:
                result=json.loads(response.content.decode('gbk'))
                entname=result.get('corpname')
                contact=result.get('linkman')
                tel=result.get('phone')
                fax=result.get('fax')
                address=result.get('address')
                website=result.get('website')
                if website:
                    website=remove_tags(website)
                email=result.get('email')
                if email:
                    email=remove_tags(email)
                insert_sql='''insert into hbsc_tel(entname,contact,tel,fax,address,website,email,url) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''
                self.Pipeline.process_item((insert_sql, (entname,contact,tel,fax,address,website,email,response.request.url)))
        pass

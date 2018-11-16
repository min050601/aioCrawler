# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from scrapy import Selector
from fake_useragent import UserAgent
import time
user_agent=UserAgent()



class CjolSpiderSpider(Spider):
    name = 'cjol_spider'
    routing_key='cjol_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.03, 'REQUEST_DELAY': 0.03, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 20, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}


    def start_request(self):
        #return
        for i in range(417972,700000):
            url = 'http://www.cjol.com/jobs/company-%s'%i
            headers={'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                     'Accept-Encoding':'gzip, deflate, sdch',
                     'Accept-Language':'zh-CN,zh;q=0.8',
                     'Upgrade-Insecure-Requests':'1',
                     'User-Agent': user_agent.random}

            request=Request(url=url,method='GET',headers=headers,callback='parse',meta={'id':i},allow_proxy=False,allow_redirects=False)
            self.start_push(request)
            time.sleep(0.03)



    def parse(self,response):
        if response.status!=200:
            print(response.status,response.request.url)
        if response.status==200:
            selector=Selector(text=response.content)
            hidPhone=selector.xpath("//input[@id='hidPhone']/@value").extract_first('')
            hidCompanyDizhi=selector.xpath("//input[@id='hidCompanyDizhi']/@value").extract_first('')
            hidCompanyName=selector.xpath("//input[@id='hidCompanyName']/@value").extract_first('')
            insert_sql='''insert into cjol_tel(entname,tel,address,url)VALUES (%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (hidCompanyName,hidPhone,hidCompanyDizhi,response.request.url)))
            print(response.request.url,hidCompanyName,hidPhone)
        pass

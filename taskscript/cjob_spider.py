# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from fake_useragent import UserAgent
from scrapy import Selector
import time
user_agent=UserAgent()



class CjobSpiderSpider(Spider):
    name = 'cjob_spider'
    routing_key='cjob_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.01, 'REQUEST_DELAY': 0.01, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 30, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}


    def start_request(self):
        for i in range(11919613,1,-1):
            url = 'http://www.cjob.gov.cn/cjobs/htmls/cb21dwPages/%s.html'%i
            headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                       'Accept-Encoding': 'gzip, deflate, sdch',
                       'Accept-Language': 'zh-CN,zh;q=0.8',
                       'Upgrade-Insecure-Requests': '1',
                       'User-Agent': user_agent.random}
            request=Request(url=url,method='GET',headers=headers,callback='parse',meta={'id':i},allow_redirects=False,allow_proxy=False)
            self.start_push(request)
            time.sleep(0.02)



    def parse(self,response):
        if response.status!=200:
            print(response.status,response.request.url)
        if response.status==200:
            id=response.request.meta['id']
            selector=Selector(text=response.content)
            entname=selector.xpath("//h1/text()").extract_first('').strip()
            address=selector.xpath("//span[text()='单位地址：']/../text()").extract_first('').strip()
            contact=selector.xpath("//dt[contains(text(),'联系方式')]/following-sibling::dd[1]/text()").extract_first('').strip()
            tel=selector.xpath("//dt[contains(text(),'联系方式')]/following-sibling::dd[2]/text()").extract_first('').strip()
            city=selector.xpath("//span[contains(text(),'所属区域：')]/../text()").extract_first('').strip()
            insert_sql='''insert into cjob_tel(entname,contact,tel,city,address,url)VALUES (%s,%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (entname,contact,tel,city,address,response.request.url)))
            print(id,entname, tel)
        pass

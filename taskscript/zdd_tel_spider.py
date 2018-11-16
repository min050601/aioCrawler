# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from fake_useragent import UserAgent
from scrapy import Selector
import time
user_agent=UserAgent()



class ZddTelSpiderSpider(Spider):
    name = 'zdd_tel_spider'
    routing_key='zdd_tel_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 10, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 60}


    def start_request(self):
        for i in range(1,11654):
            url = 'http://zhaogong.chinalao.com/%s/'%i
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': 'http://zhaogong.chinalao.com/4/',
                'Upgrade-Insecure-Requests':'1',
                'User-Agent': user_agent.random}
            request=Request(url=url,method='GET',headers=headers,callback='parse',allow_proxy=False,allow_redirects=False)
            self.start_push(request)
            time.sleep(0.1)



    def parse(self,response):
        print(response.url,response.status)
        if response.status==200:
            selector=Selector(text=response.content)
            items=selector.xpath("//h2[@class='wtit']")
            for item in items:
                url=item.xpath("./a/@href").extract_first('')
                if 'nzp' not in url:
                    headers = {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, sdch',
                        'Accept-Language': 'zh-CN,zh;q=0.8',
                        'X-Requested-With': 'XMLHttpRequest',
                        'Referer': 'http://zhaogong.chinalao.com/4/',
                        'Upgrade-Insecure-Requests': '1',
                        'User-Agent': user_agent.random}
                    request = Request(url=url, method='GET', headers=headers, callback='info_parse', allow_proxy=False, allow_redirects=False)
                    self.push(request)
        pass

    def info_parse(self,response):
        if response.status==200:
            selector=Selector(text=response.content)
            entname=selector.xpath("//span[text()='发布者：']/../text()").extract_first('').strip()
            ent_img=selector.xpath("//span[text()='发布者：']/../a/@href").extract_first('').strip()
            contact=selector.xpath("//span[text()='联系人：']/../text()").extract_first('').strip()
            tel = selector.xpath("//span[text()='联系电话：']/../text()").extract_first('').strip()
            insert_sql='''insert into zdd_tel(entname,contact,tel,ent_img,url)VALUES (%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (entname,contact,tel,ent_img,response.request.url)))

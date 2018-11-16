# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from scrapy import Selector
from fake_useragent import UserAgent
user_agent=UserAgent()



class ZggjrcwSpiderSpider(Spider):
    name = 'zggjrcw_spider'
    routing_key='zggjrcw_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 10, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 60}


    def start_request(self):
        url = 'http://jobs.newjobs.com.cn/Jobs/SearchResult?name='
        headers = {
            'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding':'gzip, deflate, sdch',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Upgrade-Insecure-Requests':'1',
            'User-Agent': user_agent.random}
        request=Request(url=url,method='GET',headers=headers,callback='parse',allow_proxy=False,allow_redirects=False,timeout=50)
        self.start_push(request)



    def parse(self,response):
        print(response.url)
        if response.status==200:
            selector=Selector(text=response.content)
            items=selector.xpath("//ul[@class='result_list_box_cpy']")
            for item in items:
                entname=item.xpath("./li[1]/a/h2/text()").extract_first('')
                url=item.xpath("./li[1]/a/@href").extract_first('')
                insert_sql='''insert ignore into zggjrcw_entname(entname,url)VALUES (%s,%s)'''
                self.Pipeline.process_item((insert_sql, (entname, url)))
            next_url=selector.xpath("//a[text()='下一页']/@href").extract_first('')
            if next_url:
                url='http://jobs.newjobs.com.cn/Jobs/SearchResult'+next_url
                response.request.url=url
                self.push(response.request)
        pass

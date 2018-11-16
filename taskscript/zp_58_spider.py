# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from fake_useragent import UserAgent
from scrapy import Selector
user_agent=UserAgent()



class Zp58SpiderSpider(Spider):
    name = 'zp_58_spider'
    routing_key='zp_58_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 40, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}


    def start_request(self):
        url = 'https://qy.58.com/citylist/'
        headers = {
            'accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'accept-encoding':'gzip, deflate, sdch, br',
            'accept-language':'zh-CN,zh;q=0.8',
            'upgrade-insecure-requests':'1',
            'User-Agent': user_agent.random}
        request=Request(url=url,method='GET',headers=headers,callback='parse',priority=1,allow_redirects=False,
                                  allow_proxy=False)
        self.start_push(request)



    def parse(self,response):
        if response.status==200:
            selector=Selector(text=response.content)
            items=selector.xpath("//dl[@id='clist']/dd/a")
            for item in items:
                url=item.xpath("./@href").extract_first('')
                city=item.xpath("./text()").extract_first('')
                next_url='https:'+url+'pn1'
                headers = {
                    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'accept-encoding': 'gzip, deflate, sdch, br',
                    'accept-language': 'zh-CN,zh;q=0.8',
                    'upgrade-insecure-requests': '1',
                    'User-Agent': user_agent.random}
                request = Request(url=next_url, method='GET', headers=headers, callback='next_parse', priority=2,
                                  allow_redirects=False, meta={'city': city},
                                  allow_proxy=False)
                self.push(request)


        pass

    def next_parse(self,response):
        if response.status==200:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'accept-encoding': 'gzip, deflate, sdch, br',
                'accept-language': 'zh-CN,zh;q=0.8',
                'upgrade-insecure-requests': '1',
                'User-Agent': user_agent.random}

            city=response.request.meta['city']
            selector=Selector(text=response.content)
            items=selector.xpath("//dl[@class='selIndCate']/dd/span/a")
            for item in items:
                url = item.xpath("./@href").extract_first('')
                next_url = 'https:' + url + 'pn1'
                request = Request(url=next_url, method='GET', headers=headers, callback='info_parse', priority=2,
                                  allow_redirects=False, meta={'city': city, 'page': 1, 'model_url': 'https:' + url},
                                  allow_proxy=False)
                self.push(request)








    def info_parse(self,response):
        if response.status==200:
            print(response.request.meta['page'])
            city = response.request.meta['city']
            selector = Selector(text=response.content)
            items = selector.xpath("//div[@class='compList']/ul/li/span/a")
            for item in items:
                entname = item.xpath("./text()").extract_first('').strip()
                url = 'https:' + item.xpath("./@href").extract_first('')
                insert_sql = '''insert ignore into zp_58_urls (entname,city,url) VALUES (%s,%s,%s)'''
                self.Pipeline.process_item(
                    (insert_sql, (entname, city, url)))
                print(entname, city, url)
            if items:
                next_url = response.request.meta['model_url'] + 'pn%s' % (response.request.meta['page'] + 1)
                response.request.meta['page'] += 1
                response.request.url = next_url
                self.push(response.request)


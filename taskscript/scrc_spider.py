# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from fake_useragent import UserAgent
from scrapy import Selector
import time
user_agent=UserAgent()



class ScrcSpiderSpider(Spider):
    name = 'scrc_spider'
    routing_key='scrc_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 10, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 60}


    def start_request(self):
        for i in range(71110,1,-1):
            url = 'http://www.scrc168.com/PersonalJobs/CompanyInfo.aspx?companyid=%s'%i
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': user_agent.random}
            request=Request(url=url,method='GET',headers=headers,callback='parse',allow_redirects=False,allow_proxy=False)
            self.start_push(request)
            time.sleep(0.1)



    def parse(self,response):
        if response.status==200:
            selector=Selector(text=response.content)
            entname=selector.xpath("//li[@class='unit_view_wd1']/text()").extract_first('')
            if not entname:
                print(response.request.url,None)
                return
            contact=selector.xpath("//td[text()='联系人：']/following-sibling::td[1]/text()").extract_first('').strip()
            tel=selector.xpath("//td[text()='联系电话：']/following-sibling::td[1]/text()").extract_first('').strip()
            email=selector.xpath("//td[text()='电子邮箱：']/following-sibling::td[1]/text()").extract_first('').strip()
            address=selector.xpath("//td[text()='单位地址：']/following-sibling::td[1]/text()").extract_first('').strip()
            insert_sql='''insert into scrc_tel(entname,contact,tel,email,address,url) VALUES (%s,%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (entname,contact,tel,email,address,response.request.url)))
        pass

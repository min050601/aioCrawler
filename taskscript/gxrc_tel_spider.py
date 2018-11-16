# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from scrapy import Selector
import time


class GxrcTelSpiderSpider(Spider):
    name = 'gxrc_tel_spider'
    routing_key='gxrc_tel_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.05, 'REQUEST_DELAY': 0.05, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 20, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 40}


    def start_request(self):
        for i in range(1599324,0,-1):
            url = 'http://www.gxrc.com/WebPage/Company.aspx?EnterpriseID=%s'%i
            headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                       'Accept-Encoding':'gzip, deflate, sdch',
                       'Accept-Language':'zh-CN,zh;q=0.8',
                       'Upgrade-Insecure-Requests':'1',
                       'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            request=Request(url=url,method='GET',headers=headers,callback='parse',allow_redirects=False,allow_proxy=False,timeout=40)
            self.start_push(request)
            time.sleep(0.1)



    def parse(self,response):
        if response.status!=200:
            print(response.request.url,response.status)
        if response.status==200:
            selector=Selector(text=response.content.decode('gbk'))
            entname = selector.xpath("//div[@class='companyName']/span/text()").extract_first('')
            tel_img = selector.xpath("//table[@id='table_add']/tbody/tr[1]/td/img/@src").extract_first('')
            contact = selector.xpath("//table[@id='table_add']/tbody/tr[2]/td/text()").extract_first('').strip()
            email = selector.xpath("//table[@id='table_add']/tbody/tr[3]/td/text()").extract_first('').strip()
            website = selector.xpath("//table[@id='table_add']/tbody/tr[4]/td/text()").extract_first('').strip()
            address = selector.xpath("//table[@id='table_add']/tbody/tr[5]/td/text()").extract_first('').strip()
            insert_sql='''insert into gxrc_tel(entname,contact,email,website,address,tel_img,url)VALUES (%s,%s,%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (entname,contact,email,website,address,tel_img,response.request.url)))
        pass

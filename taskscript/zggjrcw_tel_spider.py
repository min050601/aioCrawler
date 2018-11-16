# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from fake_useragent import UserAgent
from scrapy import Selector
import time
import pymysql
user_agent=UserAgent()


class ZggjrcwTelSpiderSpider(Spider):
    name = 'zggjrcw_tel_spider'
    routing_key='zggjrcw_tel_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 10, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301,500], 'TIMEOUT': 60}


    def start_request(self):
        connect = pymysql.Connect(
            host='localhost',
            port=3306,
            user='root',
            passwd='Elements123',
            db=self.custom_settings['MYSQL_DBNAME'],
            charset='utf8',
            use_unicode=True
        )
        print('开始查询')
        cursor = connect.cursor()
        cursor.execute(
            "select id,url from zggjrcw_entname WHERE label=9")
        connect.commit()
        result = cursor.fetchall()
        for i in result:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'accept-encoding': 'gzip, deflate, sdch, br',
                'accept-language': 'zh-CN,zh;q=0.8',
                'upgrade-insecure-requests': '1',
                'User-Agent': user_agent.random}
            request = Request(url='http://jobs.newjobs.com.cn'+i[1], method='GET', headers=headers, callback='parse', priority=1, meta={'id': i[0]}, allow_redirects=False)
            self.start_push(request)
            time.sleep(0.07)



    def parse(self,response):
        if response.status==200:
            id=response.request.meta['id']
            selector=Selector(text=response.content)
            entname=selector.xpath("//div[@class='cpy_jies_body_top']/ul[1]/li[1]/text()").extract_first('').strip()
            if not entname:
                update_sql='''update zggjrcw_entname set label=%s where id=%s'''
                self.Pipeline.process_item((update_sql, (0, id)))
                return
            logo_url=selector.xpath("//div[@class='cpy_jies_body_top_logo']/img/@src").extract_first('')
            if logo_url:
                logo_url='http://jobs.newjobs.com.cn'+logo_url
            contact=selector.xpath("//span[text()='联系人：']/../text()").extract_first('').strip()
            tel=selector.xpath("//span[text()='联系电话：']/../text()").extract_first('').strip()
            address=selector.xpath("//span[text()='联系地址：']/../text()").extract_first('').strip()
            insert_sql='''insert into zggjrcw_tel(id,entname,contact,tel,address,logo_url,url) VALUES (%s,%s,%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (id,entname,contact,tel,address,logo_url,response.request.url)))
            update_sql = '''update zggjrcw_entname set label=%s where id=%s'''
            self.Pipeline.process_item((update_sql, (1, id)))
        pass

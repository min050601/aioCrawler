# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
import pymysql
from fake_useragent import UserAgent
from scrapy import Selector
user_agent=UserAgent()


class Zp58ContactSpiderSpider(Spider):
    name = 'zp_58_contact_spider'
    routing_key='zp_58_contact_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 40, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}


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
            "select id,url from zp_58_urls WHERE label=9")
        connect.commit()
        result = cursor.fetchall()
        for i in result:
            headers = {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'accept-encoding': 'gzip, deflate, sdch, br',
                'accept-language': 'zh-CN,zh;q=0.8',
                'upgrade-insecure-requests': '1',
                'User-Agent': user_agent.random}
            request = Request(url=i[1], method='GET', headers=headers, callback='parse',priority=1,meta={'id':i[0]},allow_redirects=False)
            self.start_push(request)



    def parse(self,response):
        if response.status==200:
            id=response.request.meta['id']
            selector=Selector(text=response.content)
            entname=selector.xpath("//a[@class='businessName fl']/@title").extract_first('')
            contact_name=selector.xpath("//span[text()='联系人：']/../text()").extract_first('').strip()
            img_url=selector.xpath("//span[text()='联系电话：']/following-sibling::img/@src").extract_first('')
            if img_url:
                insert_sql='''insert into zp_58_contact(id,entname,contact_name,img_url) VALUES (%s,%s,%s,%s)'''
                update_sql='''update zp_58_urls set label=%s where id=%s'''
                self.Pipeline.process_item(
                    (insert_sql, (id,entname,contact_name,img_url)))
                self.Pipeline.process_item(
                    (update_sql, (1,id)))
            else:
                update_sql = '''update zp_58_urls set label=%s where id=%s'''
                self.Pipeline.process_item(
                    (update_sql, (0, id)))


# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from scrapy import Selector
from fake_useragent import UserAgent
import pymysql
from urllib.request import urljoin
from PIL import Image
from io import BytesIO
import time
import json
import re
#from aioCrawler.cnn_train.bxw_test import Check_Cnn
user_agent=UserAgent()


class BxwTelSpiderSpider(Spider):
    name = 'bxw_tel_spider'
    routing_key='bxw_tel_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.05, 'REQUEST_DELAY': 0.05, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 30, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}
    #model = Check_Cnn()


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
            "select city,url from bxw_city_url")
        connect.commit()
        result = cursor.fetchall()
        for i in result:
            url = i[1]
            headers = {
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding':'gzip, deflate, sdch',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Upgrade-Insecure-Requests':'1',
                'User-Agent': user_agent.random}
            request=Request(url=url,method='GET',headers=headers,callback='parse',meta={'city':i[0]},allow_redirects=True,allow_proxy=False,priority=1)
            self.start_push(request)



    def parse(self,response):
        if response.status!=200:
            print(response.status,response.url)
        if response.status==200:
            selector = Selector(text=response.content)
            if '系统检测到异常行为，请先进行九宫格验证' in response.text():
                im_url = selector.xpath("//script[contains(@src,'verify.baixing.com.cn/')]/@src").extract_first('')
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, sdch',
                    'Accept-Language': 'zh-CN,zh;q=0.8',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': user_agent.random}
                response.request.meta['img_url']=im_url.replace('.js','.jpg')
                response.request.meta['check_url'] = im_url.replace('.js', '.valid')
                response.request.meta['url'] = response.request.url
                request=Request(url=im_url,method='GET',headers=headers,callback='js_parse',meta=response.request.meta,allow_redirects=True,allow_proxy=False,priority=3)
                self.push(request)
                return
            items=selector.xpath("//a[@class='ad-title']/@href").extract()
            for i in items:
                insert_sql='''insert ignore into bxw_url_new(city,url) VALUES (%s,%s)'''
                self.Pipeline.process_item((insert_sql, (response.request.meta['city'],i)))

            next_url=selector.xpath("//a[text()='下一页']/@href").extract_first('')
            if next_url:
                response.request.url=urljoin(response.request.url,next_url)
                response.request.priority=3
                self.push(response.request)

        pass
    def js_parse(self,response):
        if response.status==200:
            re_tag='请在下方的键盘中依次点击 <i>(.*)</i>'
            match=re.findall(re_tag,response.text())
            if match:
                check=[i.strip() for i in match[0].split('-')]
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, sdch',
                    'Accept-Language': 'zh-CN,zh;q=0.8',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': user_agent.random}
                response.request.meta['check']=check
                request = Request(url=response.request.meta['img_url'], method='GET', headers=headers, callback='im_parse', meta=response.request.meta, allow_redirects=True, allow_proxy=False, priority=4)
                self.push(request)
                return

    def im_parse(self,response):
        if response.status==200:
            code=self.model.get_code(response.content)
            code1='|'.join([code.get(i) for i in response.request.meta['check']])
            print(code,code1)

            params={'data':code1,
                    'callback':'jQuery111309236942442398923_%s'%time.time()*1000,
                    '_':'%s'%time.time()*1000}
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': user_agent.random}
            request = Request(url=response.request.meta['check_url'], method='GET',params=params,headers=headers, callback='check_parse', meta=response.request.meta, allow_redirects=True,
                              allow_proxy=False, priority=5)
            self.push(request)
            return

    def check_parse(self,response):
        if response.status==200:
            result=json.loads(response.text().split('(')[-1].split(')')[0])
            code=result.get('code')
            if code:
                headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, sdch',
                    'Accept-Language': 'zh-CN,zh;q=0.8',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': user_agent.random}
                params={'ez_verify_code':response.request.params['data'],
                        'ez_verify_sign':code,
                        'timestamp':'%s'%time.time()*1000,
                        'identity':'spider',
                        'redirect':response.request.meta['url'],
                        'scene':'spider'}
                request = Request(url=response.request.meta['check_url'], method='GET',params=params,headers=headers, callback='parse', meta=response.request.meta, allow_redirects=True,
                                  allow_proxy=False, priority=5)
                self.push(request)
                return





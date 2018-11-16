# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
import datetime
from scrapy import Selector
from fake_useragent import UserAgent
user_agent=UserAgent()
import time


class GsmlSpiderSpider(Spider):
    name = 'gsml_spider'
    routing_key='gsml_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 20, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}


    def start_request(self):
        area={'北京':'/beijing','天津':'/tianjin','河北':'/hebei','内蒙古':'/neimenggu','山西':'/shanxi','上海':'/shanghai','安徽':'/anhui',
              '江苏':'/jiangsu','浙江':'/zhejiang','山东':'/shandong','江西':'/jiangxi','福建':'/fujian','广东':'/guangdong','广西':'/guangxi',
              '海南':'/hainan','河南':'/henan','湖北':'/hubei','湖南':'/hunan','黑龙江':'/heilongjiang','吉林':'/jilin','辽宁':'/liaoning',
              '陕西':'/shaanxi','甘肃':'/gansu','宁夏':'/ningxia','青海':'/qinghai','新疆':'/xinjiang','重庆':'/chongqing','四川':'/sichuan','云南':'/yunnan',
              '贵州':'/guizhou','西藏':'/xizang'}
        spider_date = datetime.datetime.strptime('2018-03-20', '%Y-%m-%d')
        while 1:
            print(spider_date)
            if spider_date>datetime.datetime.now():
                return
            time_model=spider_date.strftime('%Y-%m-%d')
            for p,u in area.items():
                url = 'https://gongshang.mingluji.com%s/riqi/%s&page=0'%(u,time_model)
                headers = {
                    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding':'gzip, deflate, sdch, br',
                    'Accept-Language':'zh-CN,zh;q=0.8',
                    'Upgrade-Insecure-Requests':'1',
                    'User-Agent': user_agent.random}
                request=Request(url=url,method='GET',headers=headers,meta={'province':p,'Regdate':spider_date},callback='parse',allow_proxy=False,allow_redirects=False,timeout=30,priority=1)
                self.start_push(request)
                time.sleep(0.5)
            spider_date=spider_date+datetime.timedelta(days=1)
            time.sleep(10)



    def parse(self,response):
        if response.status!=200:
            print(response.status,response.url)
        if response.status==200:
            selector=Selector(text=response.content)
            items=selector.xpath("//table[@class='views-table cols-2']/tbody/tr")
            for item in items:
                entname=item.xpath("./td[1]/a/text()").extract_first('')
                url=item.xpath("./td[1]/a/@href").extract_first('')
                if url:
                    url='https://gongshang.mingluji.com'+url
                area=item.xpath("./td[2]/a/text()").extract_first('')
                insert_sql='''insert into gsml_url(entname,province,area,url,Regdate) VALUES (%s,%s,%s,%s,%s)'''
                self.Pipeline.process_item((insert_sql, (entname,response.request.meta['province'],area,url,response.request.meta['Regdate'])))
            next_url=selector.xpath("//li[@class='pager-next last']/a/@href").extract_first('')
            if next_url:
                next_url='https://gongshang.mingluji.com'+next_url
                response.request.url=next_url
                response.request.priority=2
                self.push(response.request)
                time.sleep(0.5)
        pass

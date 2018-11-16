# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from fake_useragent import UserAgent
import re
import json
import time
import random
user_agent=UserAgent()


class ZlzpCompanySpiderSpider(Spider):
    name = 'zlzp_company_spider'
    routing_key='zlzp_company_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.05, 'REQUEST_DELAY': 0.05, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 140, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}
    ip_list=['192.144.150.152:8089','118.24.49.142:8089','111.231.189.211:8089','118.24.230.54:8089','192.144.153.89:8089','119.27.181.180:8089']


    def start_request(self):
        #return
        for i in range(80003887,90000000):
            url = 'https://company.zhaopin.com/CZ%s0.htm'%('%08d' % i)
            headers = {
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding':'gzip, deflate, sdch, br',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Upgrade-Insecure-Requests':'1',
                'User-Agent': user_agent.random}
            request=Request(url=url,method='GET',headers=headers,callback='parse',allow_redirects=False,allow_proxy=False)
            self.start_push(request)
            time.sleep(0.01)



    def parse(self,response):
        if response.status!=200:
            print(response.status,response.request.url)
        if response.status==200:
            re_tag='<script>__INITIAL_STATE__=({.*})</script>'
            match=re.findall(re_tag,response.text())
            if not match:
                print(response.request.url,None)
            if match:
                items = json.loads(match[0])
                company_params = items.get('company', {})
                if not company_params:
                    print(response.request.url,None)
                    return 
                companyId=company_params.get('companyId')                
                city = company_params.get('city')
                entname = company_params.get('title')
                introduceUrl = company_params.get('introduceUrl')
                companyUrl = company_params.get('companyUrl')
                logoUrl = company_params.get('logoUrl')
                tel = company_params.get('companyTelephone')
                url=response.request.url
                insert_sql='''insert into zlzp_company_info(companyId,entname,city,tel,introduceUrl,companyUrl,logoUrl,url) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''
                self.Pipeline.process_item((insert_sql, (companyId,entname,city,tel,introduceUrl,companyUrl,logoUrl,url)))
                print(entname)


        pass

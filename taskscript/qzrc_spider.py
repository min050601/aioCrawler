# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
import json



class QzrcSpiderSpider(Spider):
    name = 'qzrc_spider'
    routing_key='qzrc_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.03, 'REQUEST_DELAY': 0.03, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 30, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 60}


    def start_request(self):
        for i in range(1,51):
            url = 'http://www.qzrc.com/Search.ashx?action=c&rnd=0.16554745083462485'
            data = {'stype': 'k',
                    'p':1,
                    'k':'公司',
                    'pn':'150',
                    'urlfrom':'http://www.qzrc.com/companyList.shtml',
                    'ps':'25'}
            headers = {
                'Accept':'application/json, text/javascript, */*; q=0.01',
                'Accept-Encoding':'gzip, deflate',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With':'XMLHttpRequest',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            request=Request(url=url,method='POST',headers=headers,data=data,callback='parse',allow_proxy=False,allow_redirects=False)
            self.start_push(request)



    def parse(self,response):
        if response.status==200:
            print(response.request.data['p'])
            result=json.loads(response.content.decode('gbk'))
            pageNumber=result.get('pageNumber')
            items=result.get('table',[])
            for item in items:
                CompanyID=item.get('CompanyID')
                entname=item.get('CompanyName')
                email=item.get('Email')
                contact=item.get('LinkMan')
                tel=item.get('Tel')
                address=item.get('Address')
                insert_sql='''insert ignore into qzrc_tel(CompanyID,entname,contact,tel,email,address)VALUES (%s,%s,%s,%s,%s,%s)'''
                self.Pipeline.process_item((insert_sql, (CompanyID,entname,contact,tel,email,address)))
            if int(pageNumber)>response.request.data['p']:
                response.request.data['p']+=1
                self.push(response.request)

        pass

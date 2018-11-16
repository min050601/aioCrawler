# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
import json



class NbrcTelSpiderSpider(Spider):
    name = 'nbrc_tel_spider'
    routing_key='nbrc_tel_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 20, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}


    def start_request(self):
        url = 'https://www.nbrc.com.cn/baseApp/app/search/job'
        data = {'pageNumber': 1,
                'pageSize':20,
                'lieBieIds':'',
                'name':'',
                'jobTypeId':'',
                'cityId':'',
                'salaryId':'',
                'xingZhiId':'',
                'gongLingIds':'',
                'xueLiId':'',
                'guiMoId':'',
                'order':''}
        headers = {
            'Accept':'application/json, text/javascript, */*; q=0.01',
            'Accept-Encoding':'gzip, deflate, br',
            'Accept-Language':'zh-CN,zh;q=0.8',
            'Content-Type':'application/x-www-form-urlencoded; charset=UTF-8',
            'jsonType':'jsonType',
            'keyid':'bb5259528637fe5466a8d77128dd01c2',
            'nbrcafter':'d5e6332262e2426f810677d6abb191c9',
            'nbrcbefore':'1540447660000',
            'nbrctoken':'',
            'Referer':'https://www.nbrc.com.cn/job/list.html',
            'X-Requested-With':'XMLHttpRequest',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        request=Request(url=url,method='POST',headers=headers,data=data,callback='parse',allow_proxy=False,allow_redirects=False)
        self.start_push(request)



    def parse(self,response):
        if response.status==200:
            result=json.loads(response.content)
            datas=result.get('data')
            items=datas.get('list')
            for item in items:
                id=item.get('id')
                url='https://www.nbrc.com.cn/baseApp/app/job/getJobDetail'
                data={'jobId':id}
                headers = {
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Accept-Language': 'zh-CN,zh;q=0.8',
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'jsonType': 'jsonType',
                    'keyid': 'bb5259528637fe5466a8d77128dd01c2',
                    'nbrcafter': 'd5e6332262e2426f810677d6abb191c9',
                    'nbrcbefore': '1540447660000',
                    'nbrctoken': '',
                    'Referer': 'https://www.nbrc.com.cn/job/list.html',
                    'X-Requested-With': 'XMLHttpRequest',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
                request = Request(url=url, method='POST', headers=headers, data=data, callback='info_parse', allow_proxy=False, allow_redirects=False)
                self.push(request)
            pager=datas.get('page')
            totalPage=pager.get('totalPage')
            if response.request.data['pageNumber']<totalPage:
                response.request.data['pageNumber']+=1
                self.push(response.request)
        pass

    def info_parse(self,response):
        if response.status==200:
            result=json.loads(response.content)
            datas=result.get('data')
            fullJobVo=datas.get('fullJobVo')
            companyVo=fullJobVo.get('companyVo')
            contact=companyVo.get('lianXiRen')
            address=companyVo.get('address')
            tel=companyVo.get('dianHua')
            email=companyVo.get('email')
            id=companyVo.get('id')
            entname=companyVo.get('name')
            phone=companyVo.get('shouJi')
            url='https://www.nbrc.com.cn/job/detail.html?jobId=%s'%response.request.data['jobId']
            insert_sql='''insert into nbrc_tel(id,entname,contact,tel,phone,email,address,url)VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (id,entname,contact,tel,phone,email,address,url)))


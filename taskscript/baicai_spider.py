# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from scrapy import Selector
import time



class BaicaiSpiderSpider(Spider):
    name = 'baicai_spider'
    routing_key='baicai_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.03, 'REQUEST_DELAY': 0.03, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 30, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 60}


    def start_request(self):
        for i in range(50016110,51397988):
            url = 'http://shanghai.baicai.com/company/%s/'%i
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, sdch',
                'Accept-Language': 'zh-CN,zh;q=0.8',
                'Cookie': 'baicai_p=0ghp5s5hruu3lv6ndhfub367g4828; baicai_u=0gejb5b66ih6r4s8iujeieikj3272; baicai_uID=p_15643299; baicai_area=shanghai; PHPSESSID=q2f4brenaqmotmenl6k5q6npo7; bdshare_firstime=1540355107811; baicai_s=hcnr00t3r4ma2f4l67067njkb7; __utmt=1; BC_VisitCookie=61; BC_VisitNum=61; Hm_lvt_2cb4ec3f3a8343adb1703d1115ec562b=1540353836; Hm_lpvt_2cb4ec3f3a8343adb1703d1115ec562b=1540380599; __utma=104663071.661557839.1540353837.1540353837.1540380084.2; __utmb=104663071.25.10.1540380084; __utmc=104663071; __utmz=104663071.1540353837.1.1.utmcsr=hao123.com|utmccn=(referral)|utmcmd=referral|utmcct=/zhaopin/wangzhi',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            request=Request(url=url,method='GET',headers=headers,callback='parse',allow_redirects=True,allow_proxy=False,timeout=60)
            self.start_push(request)
            time.sleep(0.02)



    def parse(self,response):
        if response.status!=200:
            print(response.request.url,None)
        if response.status==200:
            selector=Selector(text=response.content)
            entname=selector.xpath("//p[@class='info-siteMap']/span[last()]/text()").extract_first('')
            if not entname:
                print(response.request.url,None)
            contact=selector.xpath("//h3[@class='HRB-name']/text()").extract_first('')
            tel=selector.xpath("//dt[text()='联系电话：']/following-sibling::dd[1]/text()").extract_first('').strip()
            address=selector.xpath("//dt[text()='公司地址：']/following-sibling::dd[1]/text()").extract_first('').strip()
            insert_sql='''insert into baicai_tel(entname,contact,tel,address,url)VALUES (%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (entname,contact,tel,address,str(response.url))))

        pass

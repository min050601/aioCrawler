# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from scrapy import Selector
import re
import json
import time



class StzpTelSpiderSpider(Spider):
    name = 'stzp_tel_spider'
    routing_key='stzp_tel_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.05, 'REQUEST_DELAY': 0.05, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 20, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 20}


    def start_request(self):
        #return
        for i in range(1847270,2100000):
            url = 'http://www.stzp.cn/jw/showent_%s.aspx'%i
            headers = {
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding':'gzip, deflate, sdch',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Cookie':'GeolocationTimeOutName_2=1; Geolocation_1=%7B%22bczp_CityCN%22%3A%22%u6DC4%u535A%22%2C%22bczp_citycode%22%3A291600%2C%22city%22%3A%22%u6DC4%u535A%u5E02%22%2C%22geodist%22%3Anull%2C%22geodist_int%22%3A0%2C%22lat%22%3A36.80468485%2C%22lng%22%3A118.05913428%2C%22province%22%3A%22%u5C71%u4E1C%u7701%22%2C%22reftime%22%3A%222018-10-24%2014%3A38%3A33%22%2C%22street%22%3A%22%22%2C%22street_number%22%3A%22%22%7D; hidePtAD_1=1; ASP.NET_SessionId=ynldhjyeobvt4prquncvgylo; route=c8088b91cb0f2fbcbdf107bd31e3d195; UM_distinctid=166a49655510-025ae9911e2cdb-474f0820-1fa400-166a49655528a6; bdshare_firstime=1540359621817; Jw_UserName=bczp78663707d; Jw_PassWord=qaw0%2b7P4aWPp0ju05uA%2bDw%3d%3d; Admin_SN=0; Jw_LogIP=218.247.217.98; EntSearchCookies=%cf%fa%ca%db; Hm_lvt_9c09fb6bb32d4dafc6fd4ec18d310d5b=1540359607; Hm_lpvt_9c09fb6bb32d4dafc6fd4ec18d310d5b=1540437667; CNZZDATA49160=cnzz_eid%3D374406922-1540359096-null%26ntime%3D1540434052; bchatjw7866370=0',
                'Upgrade-Insecure-Requests':'1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            request=Request(url=url,method='GET',headers=headers,callback='parse',allow_redirects=False,allow_proxy=False,timeout=40)
            self.start_push(request)
            time.sleep(0.05)



    def parse(self,response):
        if response.status!=200:
            print(response.request.url,response.status)
        if response.status==200:
            if 'window.location.href' in response.content.decode('gbk'):
                print(response.request.url,None)
                return
            selector = Selector(text=response.content.decode('gbk'))
            entname1 = selector.xpath("//a[@id='EntNameL']/text()").extract_first('')
            address1 = selector.xpath("//span[@id='ContactAddress']/text()").extract_first('')
            tel1 = selector.xpath("//span[@id='ContactPhone1']/text()").extract_first('')
            sContent_tag = r'sContent: "(.*)",'
            entname_tag = r'entname: "(.*)",'
            sContent_match = re.findall(sContent_tag, response.content.decode('gbk'))
            entname_match = re.findall(entname_tag, response.content.decode('gbk'))
            entname2=''
            address2=''
            tel2=''
            if sContent_match:
                re_selector = Selector(text=sContent_match[0])
                items = re_selector.xpath("//div/text()").extract()
                if len(items) == 2:
                    address2 = items[0].split('：')[-1]
                    tel2 = items[1].split('：')[-1]
            if entname_match:
                entname2 = entname_match[0]
            tel_img1 = selector.xpath("//img[@id='ContactPhone']/@src").extract_first('')
            website1=selector.xpath("//a[@id='Homepage1']/text()").extract_first('')
            tel_img2 = selector.xpath("//img[@id='ctl00_ContentPlaceHolder1_ContactPhone']/@src").extract_first('')
            website2 = selector.xpath("//a[@id='ctl00_ContentPlaceHolder1_Homepage1']/text()").extract_first('')
            entname3=selector.xpath("//a[@id='ctl00_ContentPlaceHolder1_V3ucenttop_new_hlEntName']/text()").extract_first('')
            address3=selector.xpath("//span[@class='address']/text()").extract_first('')
            entname = (entname1 or entname2 or entname3)
            if not entname:
                return
            address = (address1 or address2 or address3)
            tel_img = (tel_img1 or tel_img2)
            website = (website1 or website2)
            tel=(tel1 or tel2)
            insert_sql='''insert into stzp_tel(entname,address,tel,tel_img,website,url)VALUES (%s,%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (entname,address,tel,tel_img,website,response.request.url)))


            pass

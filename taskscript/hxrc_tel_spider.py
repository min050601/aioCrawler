# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from scrapy import Selector



class HxrcTelSpiderSpider(Spider):
    name = 'hxrc_tel_spider'
    routing_key='hxrc_tel_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 10, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 60}


    def start_request(self):
        url = 'http://www.hxrc.com/rcnew/SeniorSearchJobInFront.aspx?SearchKind=1&KeyWord=&area='

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, sdch',
            'Accept-Language': 'zh-CN,zh;q=0.8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
        request=Request(url=url,method='GET',headers=headers,callback='parse',allow_redirects=False,allow_proxy=False,timeout=40)
        self.start_push(request)



    def parse(self,response):
        if response.status==200:
            selector=Selector(text=response.content)
            items=selector.xpath("//a[contains(@id,'_HyperLink1')]")
            for item in items:
                url=item.xpath("./@href").extract_first('')
                if url:
                    headers = {
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Encoding': 'gzip, deflate, sdch',
                        'Accept-Language': 'zh-CN,zh;q=0.8',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
                    request = Request(url=url, method='GET', headers=headers, callback='info_parse', allow_redirects=False, allow_proxy=False, timeout=40)
                    self.push(request)
            next_page=selector.xpath("//a[text()='下一页']/@href").extract_first('')
            if next_page:
                page=eval(next_page.split('__doPostBack')[-1])[-1]
                __VIEWSTATE=selector.xpath("//input[@id='__VIEWSTATE']/@value").extract_first('')
                __VIEWSTATEGENERATOR=selector.xpath("//input[@id='__VIEWSTATEGENERATOR']/@value").extract_first('')
                __EVENTTARGET=selector.xpath("//input[@id='__EVENTTARGET']/@value").extract_first('')
                AspNetPager1_input=selector.xpath("//input[@id='AspNetPager1_input']/@value").extract_first('')
                hidGzddRequired=selector.xpath("//input[@id='hidGzddRequired']/@value").extract_first('')
                hidDateDiff=selector.xpath("//input[@id='hidDateDiff']/@value").extract_first('')
                hidZpxs=selector.xpath("//input[@id='hidZpxs']/@value").extract_first('')
                hidXlRequired=selector.xpath("//input[@id='hidXlRequired']/@value").extract_first('')
                hidXbRequired=selector.xpath("//input[@id='hidXbRequired']/@value").extract_first('')
                hidGzLeix=selector.xpath("//input[@id='hidGzLeix']/@value").extract_first('')
                hidiszzhr=selector.xpath("//input[@id='hidiszzhr']/@value").extract_first('')
                data={'__VIEWSTATE':__VIEWSTATE,
                      '__VIEWSTATEGENERATOR':__VIEWSTATEGENERATOR,
                      '__EVENTTARGET':'AspNetPager1',
                      '__EVENTARGUMENT':page,
                      'TextBox5':'请输入关键字',
                      'RadioButtonList1':'2',
                      'TextBox6':'请输入关键字',
                      'txtgzzl':'',
                      'txtgzzlhid':'',
                      'txtgshy':'',
                      'txtgshyhid':'',
                      'txtgzdd':'',
                      'txtgzddhid':'',
                      'ddlsalary':'-1',
                      'ddlxueliBegin':'-1',
                      'ddlxueliEnd':'-1',
                      'ddlJobNature':'-1',
                      'hidDateDiff':hidDateDiff,
                      'hidZpxs':hidZpxs,
                      'hidXlRequired':hidXlRequired,
                      'hidXbRequired':hidXbRequired,
                      'hidGzLeix':hidGzLeix,
                      'hidGzddRequired':hidGzddRequired,
                      'AspNetPager1_input':AspNetPager1_input,
                      'hidiszzhr':hidiszzhr
                      }
                headers={'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                         'Accept-Encoding':'gzip, deflate',
                         'Accept-Language':'zh-CN,zh;q=0.8',
                         'Content-Type':'application/x-www-form-urlencoded',
                         'Referer':'http://www.hxrc.com/rcnew/SeniorSearchJobInFront.aspx?SearchKind=2&KeyWord=&area=',
                         'Origin':'http://www.hxrc.com',
                         'Upgrade-Insecure-Requests':'1',
                         'User-Agent':'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
                request = Request(url='http://www.hxrc.com/rcnew/SeniorSearchJobInFront.aspx?SearchKind=2&KeyWord=&area=', method='POST', headers=headers, data=data,callback='parse', allow_redirects=False, allow_proxy=False, timeout=40)
                self.push(request)
        pass

    def info_parse(self,response):
        if response.status==200:
            selector=Selector(text=response.content)
            entname=selector.xpath("//li[@class='t3']/text()").extract_first('').strip()
            url=selector.xpath("//a[@id='hyl_LtdUrl']/@href").extract_first('')
            if url:
                url='http://www.hxrc.com/'+url
            tel=selector.xpath("//span[id='lbl_OrganLinkPhone']/text()").extract_first('').strip()
            phone=selector.xpath("//span[@id='lbl_OrganMobile']/text()").extract_first('').strip()
            fax=selector.xpath("//span[@id='lbl_OrganFax']/text()").extract_first('').strip()
            email=selector.xpath("//span[@id='lbl_OrganEmail']/a/text()").extract_first('').strip()
            website=selector.xpath("//span[@id='lbl_OrganWebSite']/a/text()").extract_first('').strip()
            address = selector.xpath("//span[id='lbl_OrganAddress']/text()").extract_first('').strip()
            insert_sql='''insert ignore into hxrc_tel(entname,tel,phone,fax,email,address,website,url) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (entname,tel,phone,fax,email,address,website,url)))


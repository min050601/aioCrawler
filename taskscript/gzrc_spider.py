# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
from scrapy import Selector



class GzrcSpiderSpider(Spider):
    name = 'gzrc_spider'
    routing_key='gzrc_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 0.1, 'REQUEST_DELAY': 0.1, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 10, 'MYSQL_DBNAME': 'wander', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404, 302, 301], 'TIMEOUT': 60}


    def start_request(self):
        for i in range(15604,69749):
            url = 'http://www.gzrc.gov.cn/Company_Detail.php?CompanyDetail=%s'%i

            headers = {
                'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Encoding':'gzip, deflate, sdch',
                'Accept-Language':'zh-CN,zh;q=0.8',
                'Cookie':'PHPSESSID=dd26d6f6a6ea77e4dd0559b4c53f8f6a; bdshare_firstime=1540376231389; c_job1001UserId=1305216; c_pesonAbc=4b09a359b042e122aae10d4af058a2b1; normalLogin=7c3f39f31bf111dc3c6f97f8025e27f9; zw_view_history_str=205075%252B%252B%25D1%25AA%25D4%25B4%25B9%25DC%25C0%25ED%25C4%25DA%25C7%25DA%252B%252B%252FJob_Detail.php%253FCompanyDetail%253D44794%2526ZhoaPinDetail%253D205075%252B%252B1540376015%252C%252C323374%252B%252B%25D1%25D0%25B7%25A2%25BC%25BC%25CA%25F5%25D4%25B1%252B%252B%252FJob_Detail.php%253FCompanyDetail%253D44794%2526ZhoaPinDetail%253D323374%252B%252B1540375991%252C%252C342893%252B%252B%25B8%25DF%25D0%25BD%25C6%25B8%25B1%25CF%25D2%25B5%25C9%25FA10%25C3%25FB%252B%252B%252FJob_Detail.php%253FCompanyDetail%253Dcm1446524860432%2526ZhoaPinDetail%253D342893%252B%252B1540375811',
                'Upgrade-Insecure-Requests':'1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            request=Request(url=url,method='GET',headers=headers,callback='parse',allow_proxy=False,allow_redirects=False)
            self.start_push(request)



    def parse(self,response):
        if response.status==200:
            selector=Selector(text=response.content.decode('gbk'))
            entname=selector.xpath("//h1[@class='company-na']/text()").extract_first('').strip()
            if not entname:
                print(response.request.url,None)
                return
            contact=selector.xpath("//div[@class='contact-intro']/p[1]/text()").extract_first('').split('：')[-1]
            tel=selector.xpath("//div[@class='contact-intro']/p[2]/text()").extract_first('').split('：')[-1]
            address=selector.xpath("//div[@class='contact-intro']/p[3]/text()").extract_first('').split('：')[-1]
            insert_sql='''insert into gzrc_tel(entname,contact,tel,address,url) VALUES (%s,%s,%s,%s,%s)'''
            self.Pipeline.process_item((insert_sql, (entname,contact,tel,address,response.request.url)))
        pass

# -*- coding: utf-8 -*-
from aiorequest import Request
import pymysql
from aioCrawler.aiospider import Spider
from aioCrawler.utils.py3_bloomfilter import PyBloomFilter
from aioCrawler.Tools.mylib import get_md5
from scrapy import Selector
import datetime
import json
import time
import re
import redis
redis_pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
redis_conn = redis.StrictRedis(connection_pool=redis_pool)


class BaiduZhaopinSpider(Spider):
    name = 'baidu_zhaopin'
    routing_key='baidu_zhaopin_request'
    custom_settings = {'ALLOW_PROXY': True, 'START_SLEEP': 0.03, 'REQUEST_DELAY': 0.03, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 30,'ALLOW_STATUS': [200], 'MYSQL_DBNAME': 'el_rizhi','TIMEOUT': 20,'POOL_NAME':'meituan_new','CP_MAX':10}
    bf = PyBloomFilter(conn=redis_conn)
    dataplus_job_company_items=[]
    dataplus_job_info2_items=[]


    def start_request(self):
        #time.sleep(100)
        return
        connect = pymysql.Connect(
            host='127.0.0.1',
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
            "select city from wander.baidu_zhaopin_city")

        connect.commit()
        result = cursor.fetchall()
        print('查询成功')
        for i in result:
            url='http://zhaopin.baidu.com/quanzhi?city=%s'%i[0]
            headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                       'Accept-Encoding': 'gzip, deflate, sdch',
                       'Accept-Language': 'zh-CN,zh;q=0.8',
                       'Upgrade-Insecure-Requests': '1',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
            request = Request(url=url, method='GET', headers=headers, callback='parse', priority=1,
                              allow_redirects=False, meta={'city': i[0]}, allow_proxy=True)
            self.start_push(request)




    def parse(self,response):
        salary_items=['0_0','1_1999','2001_2999','3001_4999','5001_7999','8001_9999','10000_99999999']
        date_items=self.get_date(1)
        if response.status==200:
            print({'BAIDUID':response.cookies.get('BAIDUID').value})
            token=''
            selector=Selector(text=response.text())
            re_tag="window.zp_pc_nekot = '(.*?)';"
            match=re.findall(re_tag,response.text())
            if match:
                aa=list(match[0])
                aa.reverse()
                token=''.join(aa).replace('\\','')
            else:
                self.push(response.request)
                return
            area_items=selector.xpath("//span[@class='areaitem']/text()").extract()
            for area in area_items:
                for salary in salary_items:
                    for date in date_items:
                        url='http://zhaopin.baidu.com/api/qzasync'
                        params={'query':'',
                                'city':response.request.meta['city'],
                                'is_adq':'1',
                                'pcmod':'1',
                                'district':area,
                                'sort_type':'1',
                                'sort_key':'5',
                                'pn':0,
                                'rn':10,
                                'token':token,
                                'salary':salary,
                                'date':date}
                        headers = {
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                            'Accept-Encoding': 'gzip, deflate, sdch',
                            'Accept-Language': 'zh-CN,zh;q=0.8',
                            'Upgrade-Insecure-Requests': '1',
                            'Referer':str(response.url),
                            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
                        
                        request = Request(url=url, method='GET',cookies={'BAIDUID':response.cookies.get('BAIDUID').value}, params=params,headers=headers, callback='info_parse', priority=2,
                                          allow_redirects=False,allow_proxy=True)
                        self.push(request)

        pass

    def info_parse(self,response):
        if response.status==200:
            print('*'*300)
            if '北京融信嘉业投资担保有限公司' in response.content.decode('unicode_escape') and '销售(北京融信嘉业投资担保有限公司)' in response.content.decode('unicode_escape') and '北京理房通支付科技有限公司' in response.content.decode('unicode_escape') and '风控岗(北京理房通支付科技有限公司)' in response.content.decode('unicode_escape'):
                print('反爬出现')
                url=response.request.headers['Referer']
                headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                       'Accept-Encoding': 'gzip, deflate, sdch',
                       'Accept-Language': 'zh-CN,zh;q=0.8',
                       'Upgrade-Insecure-Requests': '1',
                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
                request = Request(url=url, method='GET', headers=headers, callback='pass_spider', priority=4,
                              allow_redirects=False, meta={'request':response.request}, allow_proxy=True)
                self.push(request)
                return
            result=json.loads(response.text())
            datas=result.get('data')
            try:
                if datas.get('errno')==-1 and response.request.meta.get('dispNum',0)<=response.request.params['pn']:
                    print(response.request.params['pn'],-1,response.request.params)
                    return
                elif datas.get('errno')==-1 and response.request.meta.get('dispNum',0)>response.request.params['pn']:
                    self.push(response.request)
                    print(response.request.params['pn'],-1,response.request.meta.get('dispNum',0))

                elif datas.get('errno')==0:
                    dispNum=datas.get('dispNum','0')
                    response.request.meta['dispNum']=int(dispNum)
                    print(response.request.params['pn'], dispNum)
                    items=datas.get('disp_data',[])
                    for item in items:

                        #(updated)
                        _update_time=item.get('start_timestamp')
                        if _update_time:
                            _update_time=time.strftime('%Y-%m-%d',time.localtime(int(_update_time)))

                        #来源平台链接(sourcelink)
                        sourcelink=item.get('sourcelink')

                        #招聘人数(renshu)
                        number=item.get('number')


                        #工作年限(experience)
                        experience=item.get('experience')

                        #企业行业(industry)
                        secondindustry=item.get('secondindustry')

                        #公司概述(content)
                        companydescription=item.get('companydescription')


                        #工作城市(city)
                        city=item.get('city')

                        #学历(education)
                        education=item.get('education')

                        #工作地区(district)
                        district=item.get('district')

                        #工作地点(place)
                        area=item.get('area')
                        company_id=item.get('company_id')


                        #来源平台(source)
                        source=item.get('source')


                        #工作性质(nature)
                        type=item.get('type')

                        #工作省份(province)
                        province=item.get('province')


                        #企业地址(dom)
                        companyaddress=item.get('companyaddress')


                        #企业规模(scale,EMPNUM)
                        size=item.get('size')

                        #年龄(ori_age)
                        ori_age=item.get('ori_age')


                        #薪资(salary)
                        salary=item.get('salary')

                        #职位(position)
                        name=item.get('name')

                        #原始页面链接(mobile_url)
                        url=item.get('url')
                        startdate=item.get('startdate')

                        #招聘标题(招聘标题)
                        title=item.get('title')

                        #性别(ori_sex)
                        ori_sex=item.get('ori_sex')


                        #职位标签(tags)
                        jobtag=item.get('jobtag')


                        #招聘企业名(ENTNAME)
                        company=self.replace_item(item.get('company',''))
                        if not company:
                            continue

                        #要求(requirement)
                        requirements=item.get('requirements')

                        #福利(weal)
                        welfare='、'.join(item.get('welfare',[]))

                        #原始PC页面链接(url)
                        pc_url=item.get('pc_url')

                        #info_md5
                        dataplus_job_info2_md5=get_md5((company or '')+(title or '')+(name or '')+(requirements or '')+(url or '')+(_update_time or ''))
                        #company_md5
                        dataplus_job_company_md5=get_md5((company or '')+(size or '')+(companyaddress or '')+(companydescription or ''))
                        if not self.bf.is_exist(dataplus_job_info2_md5):
                            self.bf.add(dataplus_job_info2_md5)
                            dataplus_job_info2_data={'ENTNAME':company,'cid':company_id,'title':title,'position':name,'salary':salary,'requirement':requirements,'renshu':number,'education':education,'ori_age':ori_age,'ori_sex':ori_sex,'experience':experience,'province':province,'city':city,'district':district,'place':area,'nature':type,'weal':welfare,'scale':size,'industry':secondindustry,'tags':jobtag,'dom':source,'sourcelink':sourcelink,'url':url,'pc_url':pc_url,'url_md5':dataplus_job_info2_md5,'updated':_update_time}
                            dataplus_job_company_data={'source':source,'cid':company_id,'ENTNAME':company,'EMPNUM':size,'city':city,'addr':companyaddress,'content':companydescription,'md5':dataplus_job_company_md5,'updated':_update_time}
                            headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                       'Accept-Encoding': 'gzip, deflate, sdch',
                                       'Accept-Language': 'zh-CN,zh;q=0.8',
                                       'Upgrade-Insecure-Requests': '1',
                                       'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'}
                            request = Request(url='http://alpha.elecredit.com/get_entid/', method='POST', headers=headers,data={'key':company}, callback='get_entid', priority=5,
                                              allow_redirects=False, meta={'dataplus_job_info2_data': dataplus_job_info2_data,'dataplus_job_company_data':dataplus_job_company_data}, allow_proxy=True)
                            self.push(request)
                            print(city, company, title)




                        # #详情表插入
                        # insert_sql1='''insert ignore into dataplus_job_info2(ENTNAME,cid,title,position,salary,requirement,renshu,education,ori_age,ori_sex,experience,province,city,district,place,nature,weal,scale,industry,tags,dom,source,sourcelink,url,pc_url,url_md5,updated)
                        #               values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,md5(concat(ifnull(%s,''),ifnull(%s,''),ifnull(%s,''),ifnull(%s,''),ifnull(%s,''),ifnull(%s,''))),%s)'''
                        # params1=(company,company_id,title,name,salary,requirements,number,education,ori_age,ori_sex,experience,province,city,district,area,type,welfare,size,secondindustry,jobtag,companyaddress,source,sourcelink,url,pc_url,company,title,name,requirements,url,_update_time,_update_time)
                        # self.Pipeline.process_item((insert_sql1, params1))
                        # #企业表插入
                        # insert_sql2='''insert ignore into dataplus_job_company(source,cid,ENTNAME,EMPNUM,city,addr,content,md5,updated)values(%s,%s,%s,%s,%s,%s,%s,md5(concat(ifnull(%s,''),ifnull(%s,''),ifnull(%s,''),ifnull(%s,''))),%s)'''
                        # params2=(source,company_id,company,size,city,companyaddress,companydescription,company,size,companyaddress,companydescription,_update_time)
                        # self.Pipeline.process_item((insert_sql2, params2))
                        # print(city,company,title)
                    if response.request.params['pn']<750:
                        response.request.params['pn']+=10
                        #response.request.priority=3
                        response.request.allow_proxy=True
                        self.push(response.request)
            except Exception as e:
                print(e,datas)
                self.push(response.request)
 

    def get_entid(self,response):
        if response.status==200:
            result=json.loads(response.content)
            entid=result.get('data')
            response.request.meta['dataplus_job_info2_data']['entid']=entid
            response.request.meta['dataplus_job_company_data']['entid'] = entid
            self.dataplus_job_info2_items.append(response.request.meta['dataplus_job_info2_data'])
            self.dataplus_job_company_items.append(response.request.meta['dataplus_job_company_data'])
            print(response.request.data['key'],entid)
            insert_sql = '''insert into rizhi_www_day(sql_type,sql_1,`value`,ctype,islocal,isonline) VALUES (%s,%s,%s,%s,%s,%s)'''
            if len(self.dataplus_job_info2_items)==30:
                self.Pipeline.process_item((insert_sql, ('insert_sql',
                                                         'insert ignore into el_dataplus.dataplus_job_info(ENTNAME,entid,cid,title,position,salary,requirement,renshu,education,ori_age,ori_sex,experience,province,city,district,place,nature,weal,scale,industry,tags,dom,source,sourcelink,url,pc_url,url_md5,updated) values(%(ENTNAME)s,%(entid)s,%(cid)s,%(title)s,%(position)s,%(salary)s,%(requirement)s,%(renshu)s,%(education)s,%(ori_age)s,%(ori_sex)s,%(experience)s,%(province)s,%(city)s,%(district)s,%(place)s,%(nature)s,%(weal)s,%(scale)s,%(industry)s,%(tags)s,%(dom)s,%(source)s,%(sourcelink)s,%(url)s,%(pc_url)s,%(url_md5)s,%(updated)s)',
                                                         json.dumps(self.dataplus_job_info2_items, ensure_ascii=False), '百度招聘招聘表', 0, 0)))
                self.dataplus_job_info2_items = []
            if len(self.dataplus_job_company_items)==30:
                self.Pipeline.process_item((insert_sql, ('insert_sql',
                                                         'insert ignore into el_dataplus.dataplus_job_company(source,cid,ENTNAME,EMPNUM,city,addr,content,md5,updated) values(%(source)s,%(cid)s,%(ENTNAME)s,%(EMPNUM)s,%(city)s,%(addr)s,%(content)s,%(md5)s,%(updated)s)',
                                                         json.dumps(self.dataplus_job_company_items, ensure_ascii=False), '百度招聘企业表', 0, 0)))
                self.dataplus_job_company_items=[]






    def pass_spider(self,response):
        if response.status==200:
            token = ''            
            re_tag = '"nekot":"(.*?)",'
            match = re.findall(re_tag, response.text())
            if match:
                aa = list(match[0])
                aa.reverse()
                token = ''.join(aa).replace('\\','')
            else:
                self.push(response.request)
                return
            response.request.meta['request'].params['token']=token
            response.request.meta['request'].cookies={'BAIDUID':response.cookies.get('BAIDUID').value}
            self.push(response.request.meta['request'])


    def get_date(self,pre_num=0):
        result=['%s_%s'%(datetime.datetime.now().strftime('%Y%m%d'),datetime.datetime.now().strftime('%Y%m%d'))]
        if not pre_num:
            return result
        else:
            for i in range(1,pre_num+1):
                result.append('%s_%s'%((datetime.datetime.now() + datetime.timedelta(days=-i)).strftime('%Y%m%d'),(datetime.datetime.now() + datetime.timedelta(days=-i)).strftime('%Y%m%d')))
            return result

    def replace_item(self,item):
        if not item:
            return item
        ite = item.replace('\n', '').replace("\r\n", "").strip().replace(")", "）").replace("(", "（").replace("０",
                                                                                                             "0").replace(
            "１",
            "1").replace(
            "２", "2").replace("３", "3").replace("４", "4").replace("５", "5").replace("６", "6").replace("７", "7").replace("８",
                                                                                                                        "8").replace(
            "９",
            "9").replace(
            "ａ", "a").replace("ｂ", "b").replace("ｃ", "c").replace("ｄ", "d").replace("ｅ", "e").replace("ｆ", "f").replace("ｇ",
                                                                                                                        "g").replace(
            "ｈ", "h").replace("ｉ", "i").replace("ｊ", "j").replace("ｋ", "k").replace("ｌ", "l").replace("ｍ", "m").replace("ｎ",
                                                                                                                        "n").replace(
            "ｏ", "o").replace("ｐ", "p").replace("ｑ", "q").replace("ｒ", "r").replace("ｓ", "s").replace("ｔ", "t").replace("ｕ",
                                                                                                                        "u").replace(
            "ｖ", "v").replace("ｗ", "w").replace("ｘ", "x").replace("ｙ", "y").replace("ｚ", "z").replace("Ａ", "A").replace("Ｂ",
                                                                                                                        "B").replace(
            "Ｃ", "C").replace("Ｄ", "D").replace("Ｅ", "E").replace("Ｆ", "F").replace("Ｇ", "G").replace("Ｈ", "H").replace("Ｉ",
                                                                                                                        "I").replace(
            "Ｊ", "J").replace("Ｋ", "K").replace("Ｌ", "L").replace("Ｍ", "M").replace("Ｎ", "N").replace("Ｏ", "O").replace("Ｐ",
                                                                                                                        "P").replace(
            "Ｑ", "Q").replace("Ｒ", "R").replace("Ｓ", "S").replace("Ｔ", "T").replace("Ｕ", "U").replace("Ｖ", "V").replace("Ｗ",
                                                                                                                        "W").replace(
            "Ｘ", "X").replace("Ｙ", "Y").replace("Ｚ", "Z").replace(" ", "").replace("	", "")
        return ite



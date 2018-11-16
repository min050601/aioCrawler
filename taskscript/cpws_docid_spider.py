# -*- coding: utf-8 -*-
from aiorequest import Request
from aioCrawler.aiospider import Spider
import random
import json
import time
import base64
import pymysql
class CpwsDocidSpiderSpider(Spider):
    name = 'cpws_docid_spider'
    routing_key='cpws_docid_spider_request'
    custom_settings = {'ALLOW_PROXY': False, 'START_SLEEP': 3, 'REQUEST_DELAY': 3, 'HEART_BEAT': 10000,
                       'CONCURRENT_NUMS': 10, 'MYSQL_DBNAME': 'court', 'POOL_NAME': 'meituan_new',
                       'ALLOW_STATUS': [200, 404], 'TIMEOUT': 200,'X_MAX_PRIORITY':10}
    proxy_dict={}

    def start_request(self):
        #return
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
            "select id,canshu from a_copy where id >2000000 and count=-1 limit 10")
        connect.commit()
        result = cursor.fetchall()
        for i in result:        
            url = 'http://wenshu.court.gov.cn/ValiCode/GetCode'
            guid=self.get_guid()
            data = {'guid': guid}
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest'
            }
            request=Request(url=url,method='POST',headers=headers,data=data,meta={'code':i[1],'id':i[0],'guid':guid},callback='parse',priority=1,allow_proxy=True,allow_redirects=False)
            self.start_push(request)



    def parse(self,response):
        if response.status==200:
            number=response.text()
            response.request.meta['number']=number
            guid=response.request.meta['guid']
            headers={'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                     'Accept-Encoding':'gzip, deflate, sdch',
                     'Accept-Language':'zh-CN,zh;q=0.8',
                     'Upgrade-Insecure-Requests':'1',
                     'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}
            url='http://wenshu.court.gov.cn/list/list/?sorttype=1&number={}&guid={}&conditions=searchWord+%EF%BC%882012%EF%BC%89%E8%A1%8C%E7%9B%91%E5%AD%97%E7%AC%AC154-1%E5%8F%B7+AH++%E6%A1%88%E5%8F%B7:%EF%BC%882012%EF%BC%89%E8%A1%8C%E7%9B%91%E5%AD%97%E7%AC%AC154-1%E5%8F%B7'.format(number,guid)
            request = Request(url=url, method='GET', meta=response.request.meta,headers=headers,callback='cookie_parse', priority=2,allow_redirects=False,allow_proxy=True)
            self.push(request)
        pass

    def cookie_parse(self,response):
        if response.status==200:
            vjkl5=response.cookies.get('vjkl5').value
            response.request.meta['vjkl5']=vjkl5
            url='http://127.0.0.1:8080/get_vl5x?cookie=%s'%vjkl5
            request = Request(url=url, method='GET',meta=response.request.meta,callback='vjkl5_parse', priority=3,allow_redirects=False,allow_proxy=False)
            self.push(request)

    def vjkl5_parse(self,response):
        if response.status==200:
            result=json.loads(response.content)
            vl5x=result.get('vl5x')
            response.request.meta['vl5x']=vl5x
            data={'Param':'案号:%s'%response.request.meta['code'],
                    'Index':1,
                    'Page':10,
                    'Direction':'asc',
                  'Order':'裁判日期',
                    'vl5x':vl5x,
                    'number':response.request.meta['number'],
                    'guid':response.request.meta['guid']}
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest'
            }
            url='http://wenshu.court.gov.cn/List/ListContent'
            request = Request(url=url, method='POST', headers=headers,cookies={'vjkl5':response.request.meta['vjkl5']},data=data,meta=response.request.meta,callback='info_parse', priority=4,allow_redirects=False,allow_proxy=True)
            self.push(request)

    def info_parse(self,response):
        if response.status==200:
            if b'remind key' in response.content:
                print('remind key')
                pass

            if b'"remind"' == response.content:
                if not self.proxy_dict.get((response.proxy or '127.0.0.1')):
                    print((response.proxy or '127.0.0.1'),'出现验证码')
                    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                               'Accept-Encoding': 'gzip, deflate, sdch',
                               'Accept-Language': 'zh-CN,zh;q=0.8',
                               'Upgrade-Insecure-Requests': '1',
                               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}
                    response.request.meta['request_pre']=response.request
                    request = Request(url='http://wenshu.court.gov.cn/User/ValidateCode',
                                      meta=response.request.meta, method='GET', callback='certifycode',headers=headers, priority=7, proxy=response.proxy,allow_proxy=False,
                                      allow_redirects=False)
                    self.proxy_dict[(response.proxy or '127.0.0.1')] = time.time()
                    self.push(request)
                else:
                    self.push(response.request)

            else:
                print(response.text())
                list_content = json.loads(json.loads(response.text()))
                try:
                    RunEval = list_content[0].get('RunEval')
                except Exception as e:
                    print(e,list_content,response.request.meta['code'])
                    self.push(response.request)
                    return
                
                count=int(list_content[0].get('Count','0'))
                update_sql='''update a_copy set count=%s where id=%s'''
                self.Pipeline.process_item((update_sql, (count,response.request.meta['id'])))
                print(response.request.meta['code'],count)
                for i in list_content[1:]:
                    nopublish_reason = i.get('不公开理由')
                    jgdge_cx = i.get('审判程序')
                    wenshu_id = i.get('文书ID')
                    aj_name = i.get('案件名称')
                    aj_type = i.get('案件类型')
                    aj_code = i.get('案号')
                    court_name = i.get('法院名称')
                    judge_date = i.get('裁判日期')
                    judge_brief = i.get('裁判要旨段原文')
                    insert_sql = '''insert into court_docid(aj_code,RunEval,wenshu_id,aj_name,aj_type,court_name,judge_date,judge_brief,nopublish_reason,jgdge_cx) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                    self.Pipeline.process_item((insert_sql, (aj_code, RunEval, wenshu_id, aj_name, aj_type, court_name, judge_date, judge_brief, nopublish_reason,jgdge_cx)))
                if not count:
                    return
                if 0<count<=200:
                    response.request.data['Index']+=1
                    response.request.callback='lasted_parse'
                    self.push(response.request)
                elif 200<count<=400:
                    response.request.data['Direction']='desc'
                    response.request.callback = 'lasted_parse'
                    self.push(response.request)
                    response.request.data['Direction'] = 'asc'
                    response.request.data['Index'] += 1
                    response.request.callback = 'lasted_parse'
                    self.push(response.request)

                else:
                    url = 'http://wenshu.court.gov.cn/List/TreeContent'
                    headers = {
                        'Accept': '*/*',
                        'Accept-Encoding': 'gzip, deflate',
                        'Accept-Language': 'zh-CN,zh;q=0.9',
                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                    data = {'Param': '案号:%s' % response.request.meta['code'],
                            'vl5x': response.request.meta['vl5x'],
                            'number': response.request.meta['number'],
                            'guid': response.request.meta['guid']}
                    request = Request(url=url, method='POST', headers=headers,cookies={'vjkl5':response.request.meta['vjkl5']}, data=data, meta=response.request.meta,
                                      callback='province_parse', priority=5,allow_redirects=False,allow_proxy=True)
                    self.push(request)

    def province_parse(self,response):
        if response.status==200:
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest'
            }
            if b'remind key' in response.content:
                print('remind key')
                pass

            if b'"remind"' == response.content:
                if not self.proxy_dict.get((response.proxy or '127.0.0.1')):
                    print((response.proxy or '127.0.0.1'),'出现验证码')
                    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                               'Accept-Encoding': 'gzip, deflate, sdch',
                               'Accept-Language': 'zh-CN,zh;q=0.8',
                               'Upgrade-Insecure-Requests': '1',
                               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}
                    response.request.meta['request_pre']=response.request
                    request = Request(url='http://wenshu.court.gov.cn/User/ValidateCode',
                                      meta=response.request.meta, method='GET', callback='certifycode',headers=headers, priority=7, proxy=response.proxy,allow_proxy=False,
                                      allow_redirects=False)
                    self.proxy_dict[(response.proxy or '127.0.0.1')] = time.time()
                    self.push(request)
                else:
                    self.push(response.request)

            else:
                list_content = json.loads(json.loads(response.text()))
                fycj_count=list_content[2].get('Child')
                for i in fycj_count:
                    if i.get('Key')=='最高法院':
                        zgfy_count=i.get('Value')
                        if zgfy_count:
                            if 0<int(zgfy_count)<=200:
                                data={'Param': '案号:%s,法院层级:最高法院' % response.request.meta['code'],
                                      'Order':'裁判日期',
                                      'vl5x': response.request.meta['vl5x'],
                                      'number': response.request.meta['number'],
                                      'guid': response.request.meta['guid'],
                                      'Direction':'asc',
                                      'Index':1,
                                      'Page':10
                                      }
                                url='http://wenshu.court.gov.cn/List/ListContent'
                                request = Request(url=url, method='POST', headers=headers,cookies={'vjkl5':response.request.meta['vjkl5']}, data=data, meta=response.request.meta,
                                                  callback='lasted_parse', priority=6,allow_redirects=False,allow_proxy=True)
                                self.push(request)
                            elif int(zgfy_count)>200:
                                data = {'Param': '案号:%s,法院层级:最高法院' % response.request.meta['code'],
                                        'Order': '裁判日期',
                                        'vl5x': response.request.meta['vl5x'],
                                        'number': response.request.meta['number'],
                                        'guid': response.request.meta['guid'],
                                        'Direction': 'asc',
                                        'Index': 1,
                                        'Page': 10
                                        }
                                url = 'http://wenshu.court.gov.cn/List/ListContent'
                                request = Request(url=url, method='POST', headers=headers, cookies={'vjkl5':response.request.meta['vjkl5']}, data=data, meta=response.request.meta,
                                                  callback='lasted_parse', priority=6,allow_redirects=False,allow_proxy=True)
                                self.push(request)
                                data = {'Param': '案号:%s,法院层级:最高法院' % response.request.meta['code'],
                                        'Order': '裁判日期',
                                        'vl5x': response.request.meta['vl5x'],
                                        'number': response.request.meta['number'],
                                        'guid': response.request.meta['guid'],
                                        'Direction': 'desc',
                                        'Index': 1,
                                        'Page': 10
                                        }
                                url = 'http://wenshu.court.gov.cn/List/ListContent'
                                request = Request(url=url, method='POST', headers=headers, cookies={'vjkl5':response.request.meta['vjkl5']}, data=data, meta=response.request.meta,
                                                  callback='lasted_parse', priority=6,allow_redirects=False,allow_proxy=True)
                                self.push(request)

                        break
                fydy_list=list_content[3].get('Child')
                for j in fydy_list:
                    if j.get('Key') and j.get('Value'):
                        if 0<int(j.get('Value'))<=200:
                            data = {'Param': '案号:%s,法院地域:%s' % (response.request.meta['code'],j.get('Key')),
                                    'Order': '裁判日期',
                                    'vl5x': response.request.meta['vl5x'],
                                    'number': response.request.meta['number'],
                                    'guid': response.request.meta['guid'],
                                    'Direction': 'asc',
                                    'Index': 1,
                                    'Page': 10
                                    }
                            url = 'http://wenshu.court.gov.cn/List/ListContent'
                            request = Request(url=url, method='POST', headers=headers, cookies={'vjkl5':response.request.meta['vjkl5']}, data=data, meta=response.request.meta,
                                              callback='lasted_parse', priority=6,allow_redirects=False,allow_proxy=True)
                            self.push(request)
                        elif int(j.get('Value'))>200:
                            data = {'Param': '案号:%s,法院地域:%s' % (response.request.meta['code'],j.get('Key')),
                                    'Order': '裁判日期',
                                    'vl5x': response.request.meta['vl5x'],
                                    'number': response.request.meta['number'],
                                    'guid': response.request.meta['guid'],
                                    'Direction': 'asc',
                                    'Index': 1,
                                    'Page': 10
                                    }
                            url = 'http://wenshu.court.gov.cn/List/ListContent'
                            request = Request(url=url, method='POST', headers=headers, cookies={'vjkl5':response.request.meta['vjkl5']}, data=data, meta=response.request.meta,
                                              callback='lasted_parse', priority=6,allow_redirects=False,allow_proxy=True)
                            self.push(request)
                            data = {'Param': '案号:%s,法院地域:%s' % (response.request.meta['code'],j.get('Key')),
                                    'Order': '裁判日期',
                                    'vl5x': response.request.meta['vl5x'],
                                    'number': response.request.meta['number'],
                                    'guid': response.request.meta['guid'],
                                    'Direction': 'desc',
                                    'Index': 1,
                                    'Page': 10
                                    }
                            url = 'http://wenshu.court.gov.cn/List/ListContent'
                            request = Request(url=url, method='POST', headers=headers, cookies={'vjkl5':response.request.meta['vjkl5']}, data=data, meta=response.request.meta,
                                              callback='lasted_parse', priority=6,allow_redirects=False,allow_proxy=True)
                            self.push(request)



    def lasted_parse(self,response):
        if response.status == 200:
            if b'remind key' in response.content:
                print('remind key')
                pass
            if b'"remind"' == response.content:
                if not self.proxy_dict.get((response.proxy or '127.0.0.1')):
                    print((response.proxy or '127.0.0.1'),'出现验证码')
                    headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                               'Accept-Encoding': 'gzip, deflate, sdch',
                               'Accept-Language': 'zh-CN,zh;q=0.8',
                               'Upgrade-Insecure-Requests': '1',
                               'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}
                    response.request.meta['request_pre']=response.request
                    request = Request(url='http://wenshu.court.gov.cn/User/ValidateCode',
                                      meta=response.request.meta, method='GET', callback='certifycode',headers=headers, priority=7, proxy=response.proxy,allow_proxy=False,
                                      allow_redirects=False)
                    self.proxy_dict[(response.proxy or '127.0.0.1')] = time.time()
                    self.push(request)
                else:
                    self.push(response.request)

            else:
                list_content = json.loads(json.loads(response.text()))
                try:
                    RunEval = list_content[0].get('RunEval')
                except Exception as e:
                    print(e,list_content,response.request.meta['code'])
                    self.push(response.request)
                    return
                count = list_content[0].get('Count')
                for i in list_content[1:]:
                    nopublish_reason = i.get('不公开理由')
                    jgdge_cx = i.get('审判程序')
                    wenshu_id = i.get('文书ID')
                    aj_name = i.get('案件名称')
                    aj_type = i.get('案件类型')
                    aj_code = i.get('案号')
                    court_name = i.get('法院名称')
                    judge_date = i.get('裁判日期')
                    judge_brief = i.get('裁判要旨段原文')
                    insert_sql='''insert into court_docid(aj_code,RunEval,wenshu_id,aj_name,aj_type,court_name,judge_date,judge_brief,nopublish_reason,jgdge_cx) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''
                    self.Pipeline.process_item((insert_sql, (aj_code,RunEval,wenshu_id,aj_name,aj_type,court_name,judge_date,judge_brief,nopublish_reason,jgdge_cx)))
                if response.request.data['Index']*response.request.data['Page']<int(count) and response.request.data['Index']<20:
                    response.request.data['Index']+=1
                    self.push(response.request)


    def certifycode(self,response):
        if response.status==200:
            self.push(Request(url='http://132.232.53.199/cpws_check', proxy=response.proxy, method='POST', meta=response.request.meta, cookies=response.cookies,
                              data={'imgcontent': base64.b64encode(response.content).decode()}, callback='shibiecode', priority=8, allow_redirects=False,allow_proxy=False))


    def shibiecode(self,response):
        if response.status==200:
            result=json.loads(response.content)
            code=result.get('code')
            if code:
                self.push(
                    Request(url='http://wenshu.court.gov.cn/Content/CheckVisitCode', proxy=response.proxy, method='POST', meta=response.request.meta, cookies=response.request.cookies,
                            data={'ValidateCode': code}, callback='checkcode', priority=9, allow_redirects=False,allow_proxy=False))
            else:
                request = Request(url='http://wenshu.court.gov.cn/User/ValidateCode', meta=response.request.meta, proxy=response.proxy, method='GET', callback='certifycode',
                                  priority=7, allow_redirects=False,allow_proxy=False)
                self.push(request)

        pass

    def checkcode(self,response):
        if response.text()=='1':
            print(str(response.proxy)+'验证成功')
            self.push(response.request.meta.get('request_pre'))
            try:
                self.proxy_dict.pop((response.proxy or '127.0.0.1'))
            except Exception as e:
                print(e,(response.proxy or '127.0.0.1'))
        elif response.text()=='2':
            request=Request(url='http://wenshu.court.gov.cn/User/ValidateCode',meta=response.request.meta,proxy=response.proxy,method='GET',callback='certifycode',priority=7,allow_redirects=False,allow_proxy=False)
            self.push(request)












    def get_guid(self):
        guid=str(hex(int(((random.random()+1)* 0x10000))|0))[3:]+str(hex(int(((random.random()+1)* 0x10000))|0))[3:]+"-"+ str(hex(int(((random.random()+1)* 0x10000))|0))[3:] + "-" + str(hex(int(((random.random()+1)* 0x10000))|0))[3:] + str(hex(int(((random.random()+1)* 0x10000))|0))[3:] + "-" + str(hex(int(((random.random()+1)* 0x10000))|0))[3:] + str(hex(int(((random.random()+1)* 0x10000))|0))[3:] + str(hex(int(((random.random()+1)* 0x10000))|0))[3:]
        return guid


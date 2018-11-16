#_*_coding:utf-8_*_
import hashlib
import datetime
# import sys
# reload(sys)
# sys.setdefaultencoding('utf8')

def getYesterday():
    today = datetime.date.today()
    oneday=datetime.timedelta(days=1)
    yesterday=today-oneday
    return yesterday

#url去重MD5
def get_md5(url):
    m=hashlib.md5()
    if isinstance(url,str):
        url=url.encode('utf-8')
    m.update(url)
    return m.hexdigest()

#验证码判断
def judge_code(code):
    code_list = 'abcdefghigklmnopqrstuvwxyz1234567890'
    if len(code)!=4:
        return False
    else:
        for i in code:
            if i not in code_list:
                return False
        return True

#字符串转元组
def str_to_tuple(str):
    return tuple(eval(str.split('(')[-1].split(')')[0]))


def cn_to_en(url):
    md=get_md5(url)[8:24].replace('0','g').replace('1','h').replace('2','i').replace('3','j').replace('4','k').replace('5','l').replace('6','m').replace('7','n').replace('8','o').replace('9','p')
    return md


if __name__=='__main__':
    # print get_md5('www.baidu.com')
    a=str_to_tuple("('','abc')")
    url='kfahfk=%sfdklmkm=%s'%a
    print(url)




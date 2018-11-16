import time

class Response(object):
    def __init__(self,url,headers,request,status,cookies,content,charset,signal={},proxy=None,sesson_cookies={}):
        self.url=url
        self.headers=headers
        self.request=request
        self.cookies = cookies
        self.content=content
        self.status=status
        self.encoding=charset
        self.signal=signal
        self.proxy = proxy
        self.end=time.time()



    def text(self):
        if self.content:
            try:
                return self.content.decode((self.encoding or 'utf-8'))
            except:
                try:
                    return self.content.decode('gbk')
                except:
                    return ''
        else:
            return ''

import time
class Request():
    def __init__(self,url=None,
                 method='GET',
                 headers=None,
                 params={},
                 data={},
                 cookies=None,
                 cookie_jar=None,
                 proxy=None,
                 meta={},
                 callback='parse',
                 priority=0,
                 allow_redirects=True,
                 timeout=None,
                 allow_proxy=False,
                 allow_status=[],
                 timesleep=0,
                 ip_cer=None):
        self.url=url
        self.method=method
        self.headers=headers
        self.params=params
        self.data=data
        self.cookies=cookies
        self.cookie_jar=cookie_jar
        self.proxy=proxy
        self.retry=0
        self.meta=meta
        self.callback=callback
        self.priority=priority
        self.allow_redirects = allow_redirects
        self.timeout=timeout
        self.allow_proxy=allow_proxy
        self.allow_status = allow_status
        self.start=time.time()
        self.timesleep=timesleep
        self.ip_cer=ip_cer








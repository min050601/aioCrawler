import redis
import os
import execjs
import time
redis_pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
redis_conn = redis.StrictRedis(connection_pool=redis_pool)
os.environ["NODE_PATH"] = r"C:\\nodejs1\\node_modules"
def update_set():
    # 微信小程序
    parser = execjs.compile("""
        var pako = require('pako');
        var btoa = require('btoa');
        function parse() {
        var rohr='{"rId":100016,"ts":startdate,"cts":currentdate,"brVD":[320,456],"brR":[[640,912],[640,912],24,24],"bI":["pages/restaurant/restaurant","pages/index/index"],"mT":["257,28","219,99","190,169","172,223","169,290","270,75","249,123","228,172","212,213","198,252","189,284","186,305","186,324"],"kT":[],"aT":[],"tT":["257,28,1","219,99,1","190,169,1","172,223,1","169,290,1","270,75,1","249,123,1","228,172,1","212,213,1","198,252,1","189,284,1","186,305,1","186,324,1"],"sign":"eJwlzdEKgjAUxvFX8SqKIs42z3GDFujSroSgBxDJYYPSkVrW05d2+f+dD44va1u4prKjhoWfonMfqzksXvei9P5pH51rG823YkuTXfq3t/o1/m5TVnO607VtbIBdsDye87U55PFq90fa8P00vJW964fKaqGUkojzg1vb1H9ljJjCEGYeBldpYSCWIomYSLkBSVIhGEjTRGSMjCSeqdQAxmHEI8kpyTJiBmMKDRwwQfwCMBlCmA=="}';
           var binaryString = pako.deflate(rohr.replace(/currentdate/, new Date().getTime().toString()).replace(/startdate/, (new Date().getTime()-10000).toString()), { to: 'string' });
        return btoa(binaryString);
        }
    """)
    # #微信钱包
    # parser = execjs.compile("""
    #     var pako = require('pako');
    #     var btoa = require('btoa');
    #     function parse() {
    #     var rohr='{"rId":100023,"ver":"1.0.6","ts":startdate,"cts":currentdate,"brVD":[320,504],"brR":[[320,568],[320,548],32,32],"bI":["https://m.waimai.meituan.com/waimai/wxwallet/menu?dpShopId=&mtShopId=399965530172672&source=shoplist&initialLat=&initialLng=&actualLat=39.99859968921387&actualLng=116.19544006111775","https://m.waimai.meituan.com/waimai/wxwallet/home?utm_source=1000&code=003359S610YNYR1UmDS61vQXR61359SJ&state=123"],"mT":[],"kT":[],"aT":["277,120,DIV"],"tT":[],"aM":"","sign":"eJw9jEEKwjAQRe/SxewsmZkk7SxyAMGFoOA6tKEG2iaYdOHtDSjuHvz3X+enevj14qtj6UVGM8hoNTKqAX7bvjhE26MY1orJoFUW5nx7pnye3QlhCen+zsERxD3W+M39ud1hq4/tmmLTmYhl1ESi0ZKGko7XFFxpsTWW2n0AOAQsgw=="}'
    #        var binaryString = pako.deflate(rohr.replace(/currentdate/, new Date().getTime().toString()).replace(/startdate/, (new Date().getTime()-5000).toString()), { to: 'string' });
    #     return btoa(binaryString);
    #     }
    # """)

    while 1:
        try:
            obj = parser.call("parse")
            #微信钱包
            # redis_conn.set('_token',obj)
            # 微信小程序
            redis_conn.set('_token', obj)
            # print('_token_wei:%s'%obj)
            print('_token_wei:%s' % obj)
            time.sleep(0.05)
        except Exception as e:
            print(e)


if __name__=="__main__":
    update_set()
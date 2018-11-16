import os
import execjs
import json

# os.environ["EXECJS_RUNTIME"] = "Node"
os.environ["NODE_PATH"] = r"C:\\nodejs1\\node_modules"
# os.environ["NODE_PATH"] = r"E:\node1\node_modules"
print(os.environ)
# parser = execjs.compile("""
#     var pako = require('pako');
#     var btoa = require('btoa');
#     function parse() {
#     var rohr='{"rId":100007,"ver":"1.0.5","ts":1514818085693,"cts":currentdate,"brVD":[667,842],"brR":[[1680,1050],[1680,1010],24,24],"bI":["http://waimai.meituan.com/home/wkn2dz7fq52r","http://waimai.meituan.com/?stay=1"],"mT":[],"kT":[],"aT":[],"tT":[],"aM":""}'
#        var binaryString = pako.deflate(rohr.replace(/currentdate/, new Date().getTime().toString()), { to: 'string' });
#     return btoa(binaryString);
#     }
# """)
# parser = execjs.compile("""
#     var pako = require('pako');
#     var btoa = require('btoa');
#     function parse() {
#     var rohr='{"rId":100016,"ts":1519352491785,"cts":currentdate,"brVD":[320,456],"brR":[[640,912],[640,912],24,24],"bI":["pages/restaurant/restaurant","pages/index/index"],"mT":["267,101","257,119","246,144","234,171","226,201","221,228","218,255","216,280","213,305","212,321","212,334"],"kT":[],"aT":["205,1319,view"],"tT":["267,101,1","257,119,1","246,144,1","234,171,1","226,201,1","221,228,1","218,255,1","216,280,1","213,305,1","212,321,1","212,334,1"],"sign":"eJytkM1OwzAQhF+l6iECQYLXjje2hJESN+FCJSQeIDKJUyyaH/LTwtuTtKrEAW7cduZbjUaz7kw/NrZXodftzVi1fa2Aeb39yEdXWwUckEoAzgWdbTe8P9mD3SvwpsmVimkSC5ZEwFKqiUAhOdEkTROWAWqBNJOpJjwOIxoJikmWIWgeY6jJhiece0fjauPywe0adecd69wU42T2+dzFjVNpFZNSChqRn6xtdmcIgCA5kjPtuoPtB9c2igYswMUrxq/OquPnzBZZnqR7fmsbu+LD6urxZXujN9v4+v5s4i19OD1ekjDAABbn10J/NOlaly/jCMYjLhmVgszHQv5ptDo/uMGNc1ZkgdIyEj7YCv2wwsIXVWl8WZhXWgKtqkKsvwG1n5GA"}'
#        var binaryString = pako.deflate(rohr.replace(/currentdate/, new Date().getTime().toString()), { to: 'string' });
#     return btoa(binaryString);
#     }
# """)

parser = execjs.compile("""
    var pako = require('pako');
    var btoa = require('btoa');
    function parse() {
    var rohr='{"rId":100023,"ver":"1.0.6","ts":startdate,"cts":currentdate,"brVD":[320,504],"brR":[[320,568],[320,548],32,32],"bI":["https://m.waimai.meituan.com/waimai/wxwallet/menu?dpShopId=&mtShopId=399965530172672&source=shoplist&initialLat=&initialLng=&actualLat=39.99859968921387&actualLng=116.19544006111775","https://m.waimai.meituan.com/waimai/wxwallet/home?utm_source=1000&code=003359S610YNYR1UmDS61vQXR61359SJ&state=123"],"mT":[],"kT":[],"aT":["277,120,DIV"],"tT":[],"aM":"","sign":"eJwdjDESgyAQRe9isaXDggtusQfIjIVdakeIOoPiACly+5C0/733u8X7HEoRWPflukIUPcB61M/DC2x3mZYqhnvmkZjtyBrN6P7g2gTR9sg0DEpZRHSOIDYfYmNw1uc5p6P9GG4pkVHotHUaUvYhz818pXwKlD3dzbLsmDRpKOmd1yC/OR6ldl+bfzGD"}'    
       var binaryString = pako.deflate(rohr.replace(/currentdate/, new Date().getTime().toString()).replace(/startdate/, (new Date().getTime()-10000).toString()), { to: 'string' });
    return btoa(binaryString);
    }
""")

unparser=execjs.compile("""
var atob=require('atob');
var pako = require('pako');
function unparse(){
var strr='eJy9kctymzAYhd/FC3a4EkIgLVi4vjSO4zpNnKb2ZIYR6Ieq5hYQEPvpK8h4pp3JpptqpXOOpCN9msRCQ1rW51CfKwiQlZVCvs+xVYhOpSa/ZmUFRahkUO6qpzWKKrRxV/3PRZYc7bXXbnW/B2ZVIoVQFRLezAmjaNQFAgcZUesC6sC1qkzopKzzABOrhtdQq9z0UUI9B3PuOtzYqjndQQeZOaXJlIQ6bCCDWIdSaBG8TF4mVlPW+nq3toF6X56gCJJ0s37ePMwetur28Zt7M/f7xWr2/aIup9kwDulhNlvulhsZM0KbubOMkXPx5ddNLSP8uf6Fnlu+aPZHOO6i23s/zLuQnOevxc3d04Eyjux2+SMdCwcYnPse8j2fj87fRmskAI3cyI1thCPPdh2BbcZd36axQLGAJAJKrF6oXChDKi2CT1afhyLWrchCw0npVkJAOMcEM/pnVhbpe4ix5yJODeIhraoO6kaVRUCmaIoHLx4h9W8mG6Qc5ePW/sIpXY3OdYs39ab+4HzYnJWpKvT/pDyWfvjOf4Cbh51qlDbrZcIiaf7HZsR3bNcVzOYEgR3RhLEEJczzyOQ3188BjA==';

var binn=atob(strr);
return pako.inflate(binn, { to: 'string' })
}
""")
if __name__ == "__main__":
    # obj = parser.call("parse")
    # print(obj)
    obj = unparser.call("unparse")
    print(obj)
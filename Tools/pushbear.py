import requests
import aiohttp
import asyncio
#监控模块
def wxMonitor(title,content):
    url='https://pushbear.ftqq.com/sub'
    params={'sendkey':'4387-ad55281662334ce4dfb060d229b755cf',
            'text':title,
            'desp':content}
    resp=requests.get(url=url,params=params)
    return resp.text


async def aioWxMonitor(title,content):
    url = 'https://pushbear.ftqq.com/sub'
    params = {'sendkey': '4387-ad55281662334ce4dfb060d229b755cf',
              'text': title,
              'desp': content}
    async with aiohttp.ClientSession() as session:
        async with session.get(url=url,params=params) as resp:
            return await resp.text()



if __name__=="__main__":
    wxMonitor('test','error')
    loop=asyncio.get_event_loop()
    loop.run_until_complete(aioWxMonitor('test','error'))
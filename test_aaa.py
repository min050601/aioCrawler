import asyncio
import threading
import aioamqp
def start_loop(loop):
    while 1:
        try:
            asyncio.set_event_loop(loop)
            print(111111111111111111111111111)
            loop.run_forever()
        except Exception as e:
            print(e)
            print(asyncio.Task.all_tasks())
            for task in asyncio.Task.all_tasks():
                print(task.cancel())
            print('重启启动')
async def mqworker():
    print('ill')
    print(22222222222222222222222222222222222)
    try:
        print(111111111111111111111111111111111111111111)
        transport, protocol = await aioamqp.connect('127.0.0.1', 5672)
    except aioamqp.AmqpClosedConnection:
        print("closed connections")
    return
print('*'*100)
new_loop = asyncio.new_event_loop()
t1 = threading.Thread(target=start_loop, args=(new_loop,))
t1.start()
asyncio.run_coroutine_threadsafe(mqworker(), new_loop)


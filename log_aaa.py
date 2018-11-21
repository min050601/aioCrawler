from log import SpiderLog
import os
import time
localDir = os.path.dirname(__file__)
print(localDir)
# log1=SpiderLog(filename='bbb.log',path='./logs/')
log=SpiderLog(filename='aaaa.log',path='./logs/')
for i in range(1000):
    log.logging.info('sdfsdfgsd')
    time.sleep(0.5)
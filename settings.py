#coding:utf-8
ALLOW_STATUS=[200]
#q请求超时
TIMEOUT=5
#
X_MAX_PRIORITY=5
#请求延时
REQUEST_DELAY=0.1
#数据库
MYSQL_HOST='47.95.249.180'
MYSQL_DBNAME='wander'
MYSQL_USER='root'
MYSQL_PASSWD='Elements123'
MYSQL_CHARSET='utf8'
#rabbitmq
MQ_HOST='localhost'
MQ_USER = 'guest'
MQ_PWD = 'guest'

LOG_LEVEL='INFO'

HEART_BEAT=300
#
START_SLEEP=0.2


#ip代理
ALLOW_PROXY=True
#

#并发数
CONCURRENT_NUMS=10

#认为代理可继续使用的状态码
ACTIVE_PROXYCODE=[200]

#额外代理池名称
POOL_NAME=None

#是否使用DNS缓存
DNS_CACHE=False

#数据库连接数
CP_MIN=3
CP_MAX=5

import pymysql
import pymysql.cursors
from twisted.enterprise import adbapi
class MysqlTwistedPipeline(object):
    def __init__(self,spider):
        self.log=spider.log
        self.success_count=0
        dbparms = dict(
            host=spider.settings['MYSQL_HOST'],
            db=spider.settings['MYSQL_DBNAME'],
            user=spider.settings['MYSQL_USER'],
            passwd=spider.settings['MYSQL_PASSWD'],
            charset=spider.settings['MYSQL_CHARSET'],
            cursorclass=pymysql.cursors.DictCursor,
            use_unicode=True,
            cp_min=spider.settings['CP_MIN'],
            cp_max=spider.settings['CP_MAX'],
        )
        dbpool = adbapi.ConnectionPool('pymysql', **dbparms)
        self.dbpool=dbpool

    def process_item(self,item):
        assert isinstance(item,tuple),'need a tuple,%s is given'%type(item)
        query=self.dbpool.runInteraction(self.do_insert,item)
        query.addCallback(self.complete_log)
        query.addErrback(self.handle_error,item)
        return

    def complete_log(self,item):
        #self.log.logging.info(item[0]%item[1]+'执行成功')
        self.success_count+=1



    def handle_error(self,failure,item):
        print(failure)
        self.log.logging.waring(failure)

    def do_insert(self,cursor,item):
        insert_sql=item[0]
        params=item[1]
        cursor.execute(insert_sql,params)
        return item


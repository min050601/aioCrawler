import pymysql
import json
import redis
redis_pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=0)
redis_conn = redis.StrictRedis(connection_pool=redis_pool)


if __name__=="__main__":
    connect = pymysql.Connect(
        host='localhost',
        port=3306,
        user='root',
        passwd='Elements123',
        db='wander',
        charset='utf8',
        use_unicode=True
    )
    cursor = connect.cursor()
    cursor.execute(
        "select id,entname,info_id,uid from h5_58_ent_qc WHERE label=9")
    # cursor.execute(
    #             "select entid,entname,uniscid,url from company_yzwfsx_entid where in_nb=1 and label!=0")
    # cursor.execute(
        # "select a.entid,entname,uniscid,url from el_company_class2 a inner join t_company_wuxi b on a.entid=b.entid where a.label is null")
    # cursor.execute(
    #     "select entid,entname,uniscid,url from el_company_class2 WHERE label =9")
    # connect.commit()

    result = cursor.fetchall()
    redis_conn.delete('h5_58_items')
    select_list=[]
    for i in result:        
        items={'id':i[0],'entname':i[1],'info_id':i[2],'uid':i[3]}
        redis_conn.rpush('h5_58_items',json.dumps(items,ensure_ascii=False))
        print(items)
    print('查询成功，共%s条' % len(result))

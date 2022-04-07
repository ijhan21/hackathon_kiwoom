import psycopg2 as pg2
import logging

logging.basicConfig(filename="log.txt", level=logging.INFO)
PASSWD = ""
HOST = ""

PORT = ""

def slice_output(data):
    return data[0]

def get_company_code_for_trade():
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWD, host=HOST, port=PORT)
    cur = conn.cursor()
        
    sql = """select company_code from company_codes_trade"""
    
    cur.execute(sql)
    res = cur.fetchall()    
    conn.commit()
    cur.close()
    conn.close()

    output_slice = list(map(slice_output, res))

    return output_slice

def delete_db():
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWD, host=HOST, port=PORT)
    cur = conn.cursor()        
    sql = """delete from tmp_db"""    
    cur.execute(sql)
    conn.commit()
    cur.close()
    conn.close()
    return

def insert_tmp_db(company, tick, df):
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWD, host=HOST, port=PORT)
    cur = conn.cursor()        
    print(df)

    sql = """insert into tmp_db(company, 현재가, 거래량, 체결시간, 시가, 고가, 저가, tick) values """
    for i in zip(df['현재가'], df['거래량'], df['체결시간'], df['시가'], df['고가'], df['저가']):
        price, amount, execution_time, start_price, high, low = i
        sql +=f"('{str(company)}',{price}, {amount}, {execution_time}, {start_price}, {high}, {low},{tick}),"
    # print(sql)
    sql = sql[:-1]+";"
    cur.execute(sql)
    
    conn.commit()
    cur.close()
    conn.close()
    return

def insert_tmp_db_tip(company, tick, df):
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWD, host=HOST, port=PORT)
    cur = conn.cursor()       
    price, amount, start_price, high, low = df

    sql = """insert into tmp_db(company, 현재가, 거래량, 시가, 고가, 저가, tick) values """    
    sql +=f"('{str(company)}',{price}, {amount}, {start_price}, {high}, {low},{tick});"      

    cur.execute(sql)
    
    conn.commit()
    cur.close()
    conn.close()
    return

def get_last_data(company, tick, data_len):
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWD, host=HOST, port=PORT)
    cur = conn.cursor()        

    sql = """select 현재가, 거래량, 시가, 고가, 저가 from tmp_db where company='%s' and tick=%d order by id asc;"""%(company, tick)

    cur.execute(sql)
    ret = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return company, ret[-1], ret[-data_len:]

def insert_action(company, order_time, trade_price, order_action, rate):
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWD, host=HOST, port=PORT)
    cur = conn.cursor()           

    sql = """insert into orders(company, order_time, trade_price, order_action, rate) values """    
    sql +=f"('{company}','{order_time}', {trade_price}, {order_action},{rate});"        
    cur.execute(sql)    
    conn.commit()
    cur.close()
    conn.close()
    return

##########

def order_search():
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWD, host=HOST, port=PORT)
    cur = conn.cursor()           

    sql = """select company, order_time, trade_price, order_action from orders where trade_bool=false;"""
    cur.execute(sql)    
    res = cur.fetchall()
    conn.commit()
    cur.close()
    conn.close()
    return res

def change_trade_bool(company, order_time):
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWD, host=HOST, port=PORT)
    cur = conn.cursor()           
    sql = """update orders set trade_bool = true where company = '%s' and order_time = '%s';"""%(company, order_time)
    cur.execute(sql)        
    conn.commit()
    cur.close()
    conn.close()
    return    

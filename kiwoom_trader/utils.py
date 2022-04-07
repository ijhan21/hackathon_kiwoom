from pykiwoom.kiwoom import *
import time
from tqdm import tqdm
import psycopg2 as pg2
from PyQt5.QtTest import *

# 로그인
kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)
sleep_time = 3600
Last_execution_time3,Last_execution_time1=None, None
company_pre=""
res_=list()

def split_contents(df):
    return df[0]

HOST = ""

PASSWORD = ""
PORT = ""
# TR 요청 (연속조회)
def price_to_db(company_code, tick):
    
    company = company_code
    tick = str(tick)
    request_time = time.time()
    QTest.qWait(sleep_time)
    df = kiwoom.block_request("opt10080",
                              종목코드=company,
                              틱범위=tick,
                              수정주가구분=1,
                              output="주식분봉차트조회",
                              next=0)

    end_flag = postgre_insert_db(company=company_code, df=df, tick=tick)
    if end_flag:
        return
    
    # while kiwoom.tr_remained:
    while kiwoom.tr_remained:
        QTest.qWait(sleep_time)
        df = kiwoom.block_request("opt10080",
                                  종목코드=company,
                                  틱범위=tick,
                                  수정주가구분=1,
                                  output="주식분봉차트조회",
                                  next=2)
        end_flag = postgre_insert_db(company=company_code, df=df, tick=tick)
        if end_flag:
            print("loop end",company_code, tick)
            return

# def price_request(company_code="005930"):
#     company = company_code
#     df = kiwoom.block_request("opt10080",
#                               종목코드=company,
#                               틱범위="1",
#                               수정주가구분=1,
#                               output="주식분봉차트조회",
#                               next=0)    
#     return df

def read_company_codes():
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWORD, host=HOST, port=PORT)
    cur = conn.cursor()
    # sql = 'SELECT company_code FROM company_codes_trade;'
    sql = 'SELECT company_code FROM company_codes;'
    cur.execute(sql)
    res = cur.fetchall()    
    conn.commit()
    cur.close()
    conn.close()
    return res

def postgre_insert_db(company, df, tick):
    
    global company_pre, res_
    end_flag = False
    global c_time
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWORD, host=HOST, port=PORT)
    cur = conn.cursor()
    check_bool = True
    Last_execution_time = Last_execution_time1    

    sql ="""INSERT INTO datas("company","현재가","거래량", "체결시간", "시가", "고가", "저가", "tick") VALUES """
    for i in zip(df['현재가'], df['거래량'], df['체결시간'], df['시가'], df['고가'], df['저가']):
        
        price, amount, execution_time, start_price, high, low = i
        if price =="":
            break
        try:
            execution_time_pre = Last_execution_time[company]
        except Exception as e:
            execution_time_pre = 0
        
        if int(execution_time) == execution_time_pre:

            print("###end_flag True", company,int(execution_time)== execution_time_pre,int(execution_time),execution_time_pre, tick)
            end_flag=True
            break
        
        sql += """('%s',%d,%d,%d,%d,%d,%d,%d),"""%(company, int(price), int(amount), int(execution_time), int(start_price), int(high), int(low), int(tick))
    
    if sql =="""INSERT INTO datas("company","현재가","거래량", "체결시간", "시가", "고가", "저가", "tick") VALUES """:
        end_flag = True
        return end_flag
    sql = sql[:-1]
    sql += """;"""

    cur.execute(sql)   

    c_time = time.strftime('%X', time.localtime(time.time()))

    conn.commit()
    cur.close()
    conn.close()
    return end_flag


codes_all = read_company_codes()
codes = list(map(split_contents,codes_all))
def get_last_execution_time(num):
    conn = pg2.connect(database="postgres", user="postgres", password=PASSWORD, host=HOST, port=PORT)
    cur = conn.cursor()
    # sql = 'SELECT company_code FROM company_codes_trade;'
    sql = 'select company, max(체결시간)  from datas d where tick = %d group by company;'%num
    cur.execute(sql)
    res = cur.fetchall()    
    conn.commit()
    cur.close()
    conn.close()
    res = dict(map(lambda x : (x[0], int(x[1])), res))
    return res
def main():
    global Last_execution_time3,Last_execution_time1
    #Last_execution_time3 = get_last_execution_time(3)
    print("File Loading")
    Last_execution_time1 = get_last_execution_time(1)
    print("Excution Communication")
    # price_to_db("002785","1")
    for i,  code in tqdm(enumerate(codes)):      
    
        print(code)
        price_to_db(code,"1")
if __name__=="__main__":
    main()

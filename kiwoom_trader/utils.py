from pykiwoom.kiwoom import *
import time
from tqdm import tqdm
import psycopg2 as pg2
from PyQt5.QtTest import *

# 로그인
kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)
sleep_time = 3600

company_pre=""
res_=list()

def split_contents(df):
    return df[0]
# HOST = "15.164.224.163"
# HOST = "172.31.37.165"
HOST = "124.197.131.17"
# HOST = "192.168.29.212"
PASSWORD = "1234"
PORT = "12988"
# TR 요청 (연속조회)
def price_to_db(company_code, tick):
    
    company = company_code
    tick = str(tick)
    request_time = time.time()
    df = kiwoom.block_request("opt10080",
                              종목코드=company,
                              틱범위=tick,
                              수정주가구분=1,
                              output="주식분봉차트조회",
                              next=0)
    print(df)

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
            print("loop end",company_code)
            return

def price_request(company_code="005930"):
    company = company_code
    df = kiwoom.block_request("opt10080",
                              종목코드=company,
                              틱범위="1",
                              수정주가구분=1,
                              output="주식분봉차트조회",
                              next=0)    
    return df

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
    if company != company_pre:
        # company code로 조회해서 체결시간이 같은 항목이 나오면 end_flag = True
        sql_ = """SELECT 체결시간 FROM datas3 WHERE company='%s' ORDER BY 체결시간 desc;"""%(company) if tick=="3" else """SELECT 체결시간 FROM datas WHERE company='%s' ORDER BY 체결시간 desc;"""%(company)
        cur.execute(sql_)
        res_ = cur.fetchall()

    sql ="""INSERT INTO datas3("company","현재가","거래량", "체결시간", "시가", "고가", "저가", "tick") VALUES """ if tick=="3" else """INSERT INTO datas("company","현재가","거래량", "체결시간", "시가", "고가", "저가", "tick") VALUES """
    for i in zip(df['현재가'], df['거래량'], df['체결시간'], df['시가'], df['고가'], df['저가']):
        try:
            price, amount, execution_time, start_price, high, low = i
            if price =="":
                break
            # print(type(execution_time), execution_time)
            """
            if execution_time=="":
                break
            sql_q = f"SELECT * FROM datas WHERE 체결시간= {execution_time} AND company = '{str(company)}' AND tick = '{tick}';"        
            
            cur.execute(sql_q)
            res = cur.fetchall()
            
            if len(res) !=0:
                # print("중복 DB 입력 스킵")
                # pass
                check_bool =False
                break
            else:

                sql += """"""('%s',%d,%d,%d,%d,%d,%d,%d),""""""%(company, int(price), int(amount), int(execution_time), int(start_price), int(high), int(low), int(tick))
                # print(sql)
                """
            # print(type(res_[0][0]), res_[0])
            if (int(execution_time),) in res_:
                # print("end_flag True")
                end_flag=True
                break
            sql += """('%s',%d,%d,%d,%d,%d,%d,%d),"""%(company, int(price), int(amount), int(execution_time), int(start_price), int(high), int(low), int(tick))
        except Exception as e:
            print(e)
            print(i)
    if sql =="""INSERT INTO datas3("company","현재가","거래량", "체결시간", "시가", "고가", "저가", "tick") VALUES """ or sql =="""INSERT INTO datas("company","현재가","거래량", "체결시간", "시가", "고가", "저가", "tick") VALUES """:
        return end_flag
    sql = sql[:-1]
    sql += """;"""
    # if not check_bool:
    #     return
    cur.execute(sql)        
    c_time = time.strftime('%X', time.localtime(time.time()))
    print(company, c_time)
    conn.commit()
    cur.close()
    conn.close()
    return end_flag

codes_all = read_company_codes()
codes = list(map(split_contents,codes_all))
def main():
    while True:
        flag = False
        for i,  code in tqdm(enumerate(codes)):               
            with open("last_code.txt", "r") as f:
                check_code = f.read()
            if code ==check_code: 
                flag = True
            if code == codes[-1]:
                code = codes[0]
            if flag:
                with open("last_code.txt", "w") as f:
                    f.write(str(code))

                print(code)
                # price_to_db(code,1)
                price_to_db(code,"3")
                price_to_db(code,"1")
            c_time = time.strftime('%X', time.localtime(time.time()))
            if c_time > '03:00:00' and c_time < '06:30:00':
                return
if __name__=="__main__":
    main()

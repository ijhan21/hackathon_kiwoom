# get data
# real time order

# 실시간 조회
# order DB 조회해서 order

# from pykiwoom.kiwoom import *
from kiwoom_evol import *
from tqdm import tqdm
import numpy as np
from db_control import *
import logging

SLEEP_TIME = 3.6
TREQUEST = "opt10080"
TICK = "3"
DATA_LENGTH = 128
LIMIT_MONEY = 100000*5


logging.info("Kiwoom() class start.")
def order_excution():
    ret = order_search()
    balance = kiwoom.account_stock_dict
    for i in ret:
        company, order_time, trade_price, order_action = i #args = trade_price, order_action
        # 기존 오더에 있는지 없는지 체크
        if company not in balance.keys() and order_action == 1:
            kiwoom.send_order("신규매수",sCode=company,order_quantity=1, order_price=trade_price, hoga_type="지정가")
        elif company not in balance.keys():
            continue
        else:
            try:
                tmp =balance[company]

            except Exception as e:
                tmp = None
                print(balance[company])
                break
            # print(company, tmp, type(tmp),balance[company]["보유금액"]<LIMIT_MONEY)
            if company in balance.keys():
                if order_action == 1:
                    # 기존 오더가 없으면 신규매수
                    if tmp.jango["보유금액"]<LIMIT_MONEY or tmp.jango["보유금액"]==0:
                        if tmp.jango["주문구분"]=="+매수" and (tmp.jango["미체결수량"] !="" or tmp.jango["미체결수량"] >0):
                            kiwoom.send_order("매수정정",sCode=company,order_quantity=1, order_price=trade_price, hoga_type="지정가", order_num=tmp.jango["주문번호"])
                            print("미체결 수량 있는 경우")
                            print(tmp.jango)
                        else: # 미체결 수량 없으면 신규 매수
                            kiwoom.send_order("신규매수",sCode=company,order_quantity=1, order_price=trade_price, hoga_type="지정가")
                            print("미체결 수량 없는 경우")
                            print(tmp.jango)
                    elif tmp.jango["주문구분"]=="-매도" and (tmp.jango["미체결수량"] !="" or tmp.jango["미체결수량"] >0):
                        kiwoom.send_order("매도취소",sCode=company,order_quantity=1, order_price=trade_price, hoga_type="지정가", order_num=tmp.jango["주문번호"])
                        # 매도 주문 있을때는 그냥 취소만 하자
                        print("미체결 수량 매도 취소")
                        print(tmp.jango)

                elif order_action == 2:
                    if tmp.jango["주문구분"]=="+매수" and (tmp.jango["미체결수량"] !="" or tmp.jango["미체결수량"] >0):
                        kiwoom.send_order("매수취소",sCode=company,order_quantity=1, order_price=trade_price, hoga_type="지정가", order_num=tmp.jango["주문번호"])
                        kiwoom.send_order("신규매도",sCode=company,order_quantity=1, order_price=trade_price, hoga_type="지정가")
                        print("매수 취소하고 매도로 전환")
                        print(tmp.jango)
                    elif tmp.jango["주문구분"]=="-매도" and (tmp.jango["미체결수량"] !="" or tmp.jango["미체결수량"] >0):
                        kiwoom.send_order("매도정정",sCode=company,order_quantity=1, order_price=trade_price, hoga_type="지정가", order_num=tmp.jango["주문번호"])
                        print("매도주문정정")
                        print(tmp.jango)
                    elif tmp.jango["주문구분"]=="+매수" and tmp.jango["보유금액"]>0: ##??
                        kiwoom.send_order("매수취소",sCode=company,order_quantity=1, order_price=trade_price, hoga_type="지정가", order_num=tmp.jango["주문번호"])
                        print("매수 취소")
                        print(tmp.jango)
            elif order_action == 1: # 기존 계좌에 없고 매수 판정일 경우 하나 매수
                # 거래 계좌 확인하여 매수 가능하면 매수################ 주문가능금액 조회해서 구현필요
                # 매수 진행
                kiwoom.send_order("신규매수",sCode=company,order_quantity=1, order_price=trade_price, hoga_type="지정가")

        #현재 오더 점검
        #해당 회사의 기 구매 오더
        #update
        change_trade_bool(company, order_time)    
    # kiwoom.detail_account_info()
    kiwoom.detail_account_mystock()
    kiwoom.get_not_concluded_account()

app = QApplication(sys.argv)
kiwoom = Kiwoom()

# codes = get_company_code_for_trade()
files = os.listdir("./models/")
codes=list()
for f in files:
    codes.append(f.replace(".pt",""))

init_data = dict()
for code in tqdm(codes):
    try:
        company, ret, data = get_last_data(code, int(TICK),DATA_LENGTH)
        init_data[code] = ret
    except Exception as e:
        print(e)
        print(code)
        break
# print(init_data.keys())

# init data 확보
# tmp_db 에서 가장 마지막 값을 조회해서 저장
# 처음에 한번 저장해 두고 다음부터는 기 저장 파일을 이용하자

# 전체 기업 리스트 확보
print("TR START")
# 100개씩 끊기
codes_100 = list()
codes_tmp = list()
# for i, v in enumerate(codes):
#     codes_tmp.append(v)
#     if (i>0 and i%100==99) or i==len(codes)-1:
#         codes_100.append(codes_tmp)
#         codes_tmp = list()
while True:    
    # tr 요청
    for code in codes:
        # multi_codes = ";".join(val)
        # df = kiwoom.multi_test(TREQUEST,
        #                     종목코드=multi_codes,
        #                     틱범위=TICK,
        #                     수정주가구분=1,
        #                     output="주식분봉차트조회",
        #                     next=0)
        df_rows = kiwoom.multi_rq3(code,TICK)[0]
        # df = df.drop(['체결시간'], axis=1)
        # df_rows = df.itertuples(index=False, name=None)        
        init_data_np = np.abs(np.array(init_data[code], dtype=np.float32))
        data_np = np.abs(np.array(df_rows, dtype=np.float32))
        if sum(init_data_np==data_np)<5:
            # insert tmp_db
            insert_tmp_db_tip(code, int(TICK), data_np)
            init_data[code]=data_np
            # print("complete "+code)       
        else:
            # print("no change "+code)   
            pass
        order_excution()

    # DB 저장
    # 이전 데이터와 비교해서 변동이 있으면 DB 저장
    # 임시 DB 사용

    # order DB 확인
    # order
    # 구매한 스톡 감시
    


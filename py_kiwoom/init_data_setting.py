# request 해서 파일 세팅해서
# 저장까지 하는 걸로
from pykiwoom.kiwoom import *
import pickle
from tqdm import tqdm
import time 
import numpy as np
from multiprocessing import Process
from db_control import *
import os
SLEEP_TIME = 3.6
TREQUEST = "opt10080"
TICK = "3"
kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)

# codes = get_company_code_for_trade()
files = os.listdir("./models/")
codes=list()
for f in files:
    codes.append(f.replace(".pt",""))
    
delete_db() # initiate db
data_dict = dict()
# init data 확보
for code in tqdm(codes):
    df = kiwoom.block_request(TREQUEST,
                              종목코드=code,
                              틱범위=TICK,
                              수정주가구분=1,
                              output="주식분봉차트조회",
                              next=0)
    
    # data frame 정렬
    df = df.sort_values(by=['체결시간'], axis=0, ascending=True)
    insert_tmp_db(code, TICK, df)
    time.sleep(SLEEP_TIME)

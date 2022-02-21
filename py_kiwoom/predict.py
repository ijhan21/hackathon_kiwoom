from db_control import *
import os
from model import *
import numpy as np
import time

import logging
logging.basicConfig(filename='predict.log', level=logging.DEBUG)

logging.debug("predict log")

TICK ="3"
TRAIND_MODEL_PATH = "./models/"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE = DATA_LENGTH = 128
CHANNELS_IMG = 5
NUM_CLASSES = 3
FEATURES_CRITIC = 16

# codes = get_company_code_for_trade()

files = os.listdir("./models/")
codes=list()
for f in files:
    codes.append(f.replace(".pt",""))
    
init_data = dict()
for code in codes:
    init_data[code] = Code_obj()
    try:
        company, ret, data = get_last_data(code, int(TICK), DATA_LENGTH)
        init_data[code].last_data = ret
        init_data[code].data = data
        
    except Exception as e:
        print(e)
        print(code)
        break
for code in codes:    
    critic = Critic_128(CHANNELS_IMG, FEATURES_CRITIC, NUM_CLASSES, IMG_SIZE).to(device)
    file_path = TRAIND_MODEL_PATH+code+".pt"
    if os.path.isfile(file_path):        
        critic.load_state_dict(torch.load(file_path, map_location=device))
        init_data[code].model=critic        


check_list = list()
# 모델 있는 것만 체크
for code in codes:
    obj = init_data[code]
    if obj.model is None:
        continue
    else:
        check_list.append(code)

while True:
    for code in check_list:
        company, ret, data = get_last_data(code, int(TICK), DATA_LENGTH)
        obj = init_data[code]
        if not obj.check(ret):
            # if code == "000070":
            #     print(obj.last_data)
            #     print(ret)
            #     print(obj.last_data==ret)
            res = obj.update(ret)
            action, rate = obj.forward()
            print("company",company, "action",action.item(), "rate",rate.item())
            if action.item() != 0:
                c_time = time.strftime('%X', time.localtime(time.time()))                
                order_time = c_time.replace(":","")
                company,order_time, trade_price, order_action =code,order_time,ret[0],action.item()
                insert_action(company, order_time, trade_price, order_action, rate)

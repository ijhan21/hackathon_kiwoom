from pykiwoom.kiwoom import *
import pickle
from tqdm import tqdm
import time 
import numpy as np
from multiprocessing import Process
from db_control import *

SLEEP_TIME = 3.6
TREQUEST = "opt10080"
TICK = "3"
DATA_LENGTH = 64

kiwoom = Kiwoom()
kiwoom.CommConnect(block=True)
accounts = kiwoom.GetLoginInfo("ACCNO")
stock_account = accounts[1]
print(accounts)
rt = kiwoom.SendOrder("시장가매수", "0101", stock_account, 1, "005930", 10, 0, "03", "")
# kiwoom.SendOrder()
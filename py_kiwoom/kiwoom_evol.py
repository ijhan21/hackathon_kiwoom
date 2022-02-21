import os
import pickle
import sys
from PyQt5.QAxContainer import *
from PyQt5.QtCore import *
from config.errorCode import *
from PyQt5.QtTest import *
from config.kiwoomType import *
# from config.slack import *

import logging
from PyQt5.QtWidgets import *

STOP_LOSS_RATE = 0.03
STOP_PROFIT_RATE = 0.03
# class Ui_class():
#     def __init__(self):
#         self.app = QApplication(sys.argv)
#         self.kiwoom = Kiwoom()
#         ret = self.kiwoom.multi_test()

#         # self.app.exec_()

logging.basicConfig(filename="kiwoom.log", level=logging.INFO)

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        self.realType = RealType()
        # self.slack = Slack() #슬랙 동작

        #print("kiwoom() class start. ")
        print("Kiwoom() class start.")

        ####### event loop를 실행하기 위한 변수모음
        self.login_event_loop = QEventLoop() #로그인 요청용 이벤트루프
        self.detail_account_info_event_loop = QEventLoop() # 예수금 요청용 이벤트루프
        self.calculator_event_loop = QEventLoop()
        self.get_not_concluded_account_event_loop = QEventLoop()
        #########################################
      
        ####### 계좌 관련된 변수
        self.account_stock_dict = {}
        self.not_concluded_account = {}
        self.deposit = 0 #예수금
        self.use_money = 0 #실제 투자에 사용할 금액
        self.use_money_percent = 0.5 #예수금에서 실제 사용할 비율
        self.output_deposit = 0 #출력가능 금액
        self.total_profit_loss_money = 0 #총평가손익금액
        self.total_profit_loss_rate = 0.0 #총수익률(%)
        ########################################

        ######## 종목 정보 가져오기
        self.portfolio_stock_dict = {}
        self.jango_dict = {}
        ########################

        ##########################################
        self.data = None

        ####### 요청 스크린 번호
        self.screen_my_info = "2000" #계좌 관련한 스크린 번호
        self.screen_calculation_stock = "4000" #계산용 스크린 번호
        self.screen_real_stock = "5000" #종목별 할당할 스크린 번호
        self.screen_meme_stock = "6000" #종목별 할당할 주문용스크린 번호
        self.screen_start_stop_real = "1000" #장 시작/종료 실시간 스크린번호
        ########################################

        ######### 초기 셋팅 함수들 바로 실행
        self.get_ocx_instance() #OCX 방식을 파이썬에 사용할 수 있게 변환해 주는 함수
        self.event_slots() # 키움과 연결하기 위한 시그널 / 슬롯 모음
        self.real_event_slot()  # 실시간 이벤트 시그널 / 슬롯 연결
        self.signal_login_commConnect() #로그인 요청 시그널 포함
        self.get_account_info() #계좌번호 가져오기


        self.detail_account_info() #예수금 요청 시그널 포함
        self.detail_account_mystock() #계좌평가잔고내역 요청 시그널 포함
        QTimer.singleShot(5000, self.get_not_concluded_account) #5초 뒤에 미체결 종목들 가져오기 실행
        #########################################

        # QTest.qWait(10000)
        self.read_code()
        self.screen_number_setting()

        QTest.qWait(5000)
        
        #실시간 수신 관련 함수
        #장시작 종료 세팅
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", self.screen_start_stop_real, '', self.realType.REALTYPE['장시작시간']['장운영구분'], "0")
        
    def setRealReg(self, companys):
        for code in companys:
            screen_num = self.not_concluded_account[code]['스크린번호']
            fids = self.realType.REALTYPE['주식체결']['체결시간']
            self.dynamicCall("SetRealReg(QString, QString, QString, QString)", screen_num, code, fids, "1")

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1") # 레지스트리에 저장된 api 모듈 불러오기


    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot) # 로그인 관련 이벤트
        self.OnReceiveTrData.connect(self.trdata_slot) # 트랜잭션 요청 관련 이벤트
        self.OnReceiveMsg.connect(self.msg_slot)


    def real_event_slot(self):
        self.OnReceiveRealData.connect(self.realdata_slot)  # 실시간 이벤트 연결
        self.OnReceiveChejanData.connect(self.chejan_slot) #종목 주문체결 관련한 이벤트


    def signal_login_commConnect(self):
        self.dynamicCall("CommConnect()") # 로그인 요청 시그널

        self.login_event_loop.exec_() # 이벤트루프 실행

    def login_slot(self, err_code):

        logging.debug(errors(err_code)[1])

        #로그인 처리가 완료됐으면 이벤트 루프를 종료한다.
        self.login_event_loop.exit()

    def get_account_info(self):
        QTest.qWait(3600) #3.6초마다 딜레이를 준다.
        account_list = self.dynamicCall("GetLoginInfo(QString)", "ACCNO") # 계좌번호 반환
        account_num = account_list.split(';')[1]

        self.account_num = account_num

        logging.debug("계좌번호 : %s" % account_num)


    def detail_account_info(self, sPrevNext="0"):
        QTest.qWait(3600) #3.6초마다 딜레이를 준다.

        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "예수금상세현황요청", "opw00001", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def detail_account_mystock(self, sPrevNext="0"):
        QTest.qWait(3600) #3.6초마다 딜레이를 준다.
        self.account_stock_dict = dict()
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "계좌평가잔고내역요청", "opw00018", sPrevNext, self.screen_my_info)

        self.detail_account_info_event_loop.exec_()

    def get_not_concluded_account(self, sPrevNext="0"):
        QTest.qWait(3600) #3.6초마다 딜레이를 준다.
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_num)
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "1")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "실시간미체결요청", "opt10075", sPrevNext, self.screen_my_info)

        self.get_not_concluded_account_event_loop.exec_()

    def trdata_slot(self, sScrNo, sRQName, sTrCode, sRecordName, sPrevNext):
        # print("sRQName", sRQName)
        if sRQName == "예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "예수금")
            self.deposit = int(deposit)

            use_money = float(self.deposit) * self.use_money_percent
            self.use_money = int(use_money)
            self.use_money = self.use_money / 4

            output_deposit = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "출금가능금액")
            self.output_deposit = int(output_deposit)

            logging.debug("예수금 : %s" % self.output_deposit)
            print("예수금 : %s" % self.output_deposit)
            self.stop_screen_cancel(self.screen_my_info)

            self.detail_account_info_event_loop.exit()

        elif sRQName == "계좌평가잔고내역요청":

            total_buy_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총매입금액")
            self.total_buy_money = int(total_buy_money)
            total_profit_loss_money = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총평가손익금액")
            self.total_profit_loss_money = int(total_profit_loss_money)
            total_profit_loss_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "총수익률(%)")
            self.total_profit_loss_rate = float(total_profit_loss_rate)

            logging.debug("계좌평가잔고내역요청 싱글데이터 : %s - %s - %s" % (total_buy_money, total_profit_loss_money, total_profit_loss_rate))

            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호")  # 출력 : A039423 // 알파벳 A는 장내주식, J는 ELW종목, Q는 ETN종목
                code = code.strip()[1:]

                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")  # 출럭 : 한국기업평가
                stock_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량")  # 보유수량 : 000000000000010
                buy_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가")  # 매입가 : 000000000054100
                learn_rate = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)")  # 수익률 : -000000001.94
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가")  # 현재가 : 000000003450
                total_chegual_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액")
                possible_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량")


                logging.debug("종목코드: %s - 종목명: %s - 보유수량: %s - 매입가:%s - 수익률: %s - 현재가: %s" % (
                    code, code_nm, stock_quantity, buy_price, learn_rate, current_price))

                if code in self.account_stock_dict:  # dictionary 에 해당 종목이 있나 확인
                    pass
                else:
                    self.account_stock_dict[code] = Jango(code)

                code_nm = code_nm.strip()
                stock_quantity = int(stock_quantity.strip())
                buy_price = int(buy_price.strip())
                learn_rate = float(learn_rate.strip())
                current_price = int(current_price.strip())
                total_chegual_price = int(total_chegual_price.strip())
                possible_quantity = int(possible_quantity.strip())
                tmp = self.account_stock_dict[code]
                tmp.jango.update({"종목명": code_nm})
                # tmp.jango.update({"보유수량": stock_quantity})
                tmp.jango.update({"체결량": stock_quantity})
                # tmp.jango.update({"매입가": buy_price})
                tmp.jango.update({"체결가": buy_price})
                # tmp.jango.update({"수익률(%)": learn_rate})
                tmp.jango.update({"현재가": current_price})
                # tmp.jango.update({"매입금액": total_chegual_price})
                # tmp.jango.update({'매매가능수량' : possible_quantity})
                tmp.update()

            logging.debug("sPreNext : %s" % sPrevNext)
            print("\n계좌에 가지고 있는 종목은 %s " % rows)
            # for item in self.account_stock_dict.keys():
            #     print(self.account_stock_dict[item].jango)
            

            if sPrevNext == "2":
                self.detail_account_mystock(sPrevNext="2")
            else:
                self.detail_account_info_event_loop.exit()


        elif sRQName == "실시간미체결요청":
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            for i in range(rows):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목코드")
                code_nm = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명")
                order_no = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                                "주문상태")  # 접수,확인,체결
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                                  "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                               "주문가격")
                order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                               "주문구분")  # -매도, +매수, -매도정정, +매수정정
                not_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                                "미체결수량")
                ok_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i,
                                               "체결량")


                code = code.strip()
                code_nm = code_nm.strip()
                order_no = int(order_no.strip())
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())
                order_gubun = order_gubun.strip().lstrip('+').lstrip('-')
                not_quantity = int(not_quantity.strip())
                ok_quantity = int(ok_quantity.strip())

                if code in self.not_concluded_account:
                    pass
                else:
                    self.not_concluded_account[code] = Jango(code)

                tmp = self.not_concluded_account[code]

                tmp.jango.update({'종목코드': code})
                tmp.jango.update({'종목명': code_nm})
                tmp.jango.update({'주문번호': order_no})
                tmp.jango.update({'주문상태': order_status})
                tmp.jango.update({'주문수량': order_quantity})
                tmp.jango.update({'주문가격': order_price})
                tmp.jango.update({'주문구분': order_gubun})
                tmp.jango.update({'미체결수량': not_quantity})
                tmp.jango.update({'체결량': ok_quantity})
                tmp.jango.update({'스크린번호': 1000})
                tmp.update()

                logging.debug("미체결 종목 : %s "  % self.not_concluded_account[code])
                print("미체결 종목 : %s "  % self.not_concluded_account[code].jango)
            self.get_not_concluded_account_event_loop.exit()

        
        #######################################
        elif sRQName == "3분봉조회":
            cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName)
            # print(sTrCode)
            # data = self.dynamicCall("GetCommDataEx(QString, QString)", sTrCode, sRQName)
            # [[‘’, ‘현재가’, ‘거래량’, ‘거래대금’, ‘날짜’, ‘시가’, ‘고가’, ‘저가’. ‘’], [‘’, ‘현재가’, ’거래량’, ‘거래대금’, ‘날짜’, ‘시가’, ‘고가’, ‘저가’, ‘’]. […]]

            logging.debug("3분봉조회 %s" % cnt)
            ret_data=list()

            for i in range(cnt):
                data = []

                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드")
                code = code.strip()
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목명")
                code_name = code_name.strip()
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가").strip()  # 출력 : 000070
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래량").strip()  # 출력 : 000070
                trading_value = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "거래대금")  # 출력 : 000070
                date = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "일자")  # 출력 : 000070
                start_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시가").strip()  # 출력 : 000070
                high_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "고가").strip()  # 출력 : 000070
                low_price = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "저가").strip()  # 출력 : 000070
                data=[int(current_price),int(volume), int(start_price), int(high_price), int(low_price)]
                ret_data.append(data)
            self.data = ret_data
            self.calculator_event_loop.exit()

    def multi_rq3(self, sCode, tick):
        QTest.qWait(3600) #3.6초마다 딜레이를 준다.
        trCode = "opt10080"
        sRQName = "3분봉조회"
        수정주가구분 = 1       
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", sCode)
        self.dynamicCall("SetInputValue(QString, QString)", "틱범위", tick)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", 수정주가구분)
        ret = self.dynamicCall("CommRqData(QString, QString, int, QString, QString, QString)",sRQName,trCode, "0", self.screen_meme_stock)
        # ret =  self.dynamicCall("GetCommDataEx(QString, QString)", trCode, "주식분봉차트")        
        self.calculator_event_loop.exec_()
        return self.data

    def stop_screen_cancel(self, sScrNo=None):
        self.dynamicCall("DisconnectRealData(QString)", sScrNo) # 스크린번호 연결 끊기

    def get_code_list_by_market(self, market_code):
        '''
        종목코드 리스트 받기
        #0:장내, 10:코스닥
        :param market_code: 시장코드 입력
        :return:
        '''
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_code)
        code_list = code_list.split(';')[:-1]
        return code_list

 

    def read_code(self):

        # if os.path.exists("files/condition_stock.txt"): # 해당 경로에 파일이 있는지 체크한다.
        #     f = open("files/condition_stock.txt", "r", encoding="utf8") # "r"을 인자로 던져주면 파일 내용을 읽어 오겠다는 뜻이다.

        #     lines = f.readlines() #파일에 있는 내용들이 모두 읽어와 진다.
        #     for line in lines: #줄바꿈된 내용들이 한줄 씩 읽어와진다.
        #         if line != "":
        #             ls = line.split("\t")

        #             stock_code = ls[0]
        #             stock_name = ls[1]
        #             stock_price = int(ls[2].split("\n")[0])
        #             stock_price = abs(stock_price)

        #             self.portfolio_stock_dict.update({stock_code:{"종목명":stock_name, "현재가":stock_price}})
        #     f.close()
        files = os.listdir("./models/")
        codes=list()
        for f in files:
            codes.append(f.replace(".pt",""))
        for code in codes:
            self.portfolio_stock_dict[code] = Jango(code)
        return codes
   
    def screen_number_setting(self):

        screen_overwrite = []

        #계좌평가잔고내역에 있는 종목들
        for code in self.account_stock_dict.keys():
            if code not in screen_overwrite:
                screen_overwrite.append(code)


        #미체결에 있는 종목들
        for code in self.not_concluded_account.keys():
            code = self.not_concluded_account[code]['종목코드']

            if code not in screen_overwrite:
                screen_overwrite.append(code)


        #포트폴리로에 담겨있는 종목들
        for code in self.portfolio_stock_dict.keys():

            if code not in screen_overwrite:
                screen_overwrite.append(code)


        # 스크린번호 할당
        cnt = 0
        for code in screen_overwrite:

            temp_screen = int(self.screen_real_stock)
            meme_screen = int(self.screen_meme_stock)

            if (cnt % 50) == 0:
                temp_screen += 1
                self.screen_real_stock = str(temp_screen)

            if (cnt % 50) == 0:
                meme_screen += 1
                self.screen_meme_stock = str(meme_screen)

            if code in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code].jango.update({"스크린번호": str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].jango.update({"주문용스크린번호": str(self.screen_meme_stock)})

            elif code not in self.portfolio_stock_dict.keys():
                self.portfolio_stock_dict[code] = Jango(code)
                self.portfolio_stock_dict[code].jango.update({"스크린번호": str(self.screen_real_stock)})
                self.portfolio_stock_dict[code].jango.update({"주문용스크린번호": str(self.screen_meme_stock)})

            cnt += 1


    # 실시간 데이터 얻어오기
    def realdata_slot(self, sCode, sRealType, sRealData):

        if sRealType == "장시작시간":
            fid = self.realType.REALTYPE[sRealType]['장운영구분']  # (0:장시작전, 2:장종료전(20분), 3:장시작, 4,8:장종료(30분), 9:장마감)
            value = self.dynamicCall("GetCommRealData(QString, int)", sCode, fid)

            if value == '0':
                logging.debug("장 시작 전")

            elif value == '3':
                logging.debug("장 시작")

            elif value == "2":
                logging.debug("장 종료, 동시호가로 넘어감")

            elif value == "4":
                logging.debug("3시30분 장 종료")

                for code in self.not_concluded_account.keys():
                    self.dynamicCall("SetRealRemove(QString, QString)", self.not_concluded_account[code]['스크린번호'], code)

                QTest.qWait(5000)

                sys.exit()

        elif sRealType == "주식체결":

            a = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['체결시간'])  # 출력 HHMMSS
            b = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['현재가'])  # 출력 : +(-)2520
            b = abs(int(b))

            c = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['전일대비'])  # 출력 : +(-)2520
            c = abs(int(c))

            d = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['등락율'])  # 출력 : +(-)12.98
            d = float(d)

            e = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['(최우선)매도호가'])  # 출력 : +(-)2520
            e = abs(int(e))

            f = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['(최우선)매수호가'])  # 출력 : +(-)2515
            f = abs(int(f))

            g = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['거래량'])  # 출력 : +240124  매수일때, -2034 매도일 때
            g = abs(int(g))

            h = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['누적거래량'])  # 출력 : 240124
            h = abs(int(h))

            i = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['고가'])  # 출력 : +(-)2530
            i = abs(int(i))

            j = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['시가'])  # 출력 : +(-)2530
            j = abs(int(j))

            k = self.dynamicCall("GetCommRealData(QString, int)", sCode, self.realType.REALTYPE[sRealType]['저가'])  # 출력 : +(-)2530
            k = abs(int(k))

            if sCode not in self.not_concluded_account:                
                self.not_concluded_account[sCode]=Jango(sCode)
            tmp_not_c = self.not_concluded_account[sCode]
            tmp_not_c.jango.update({"현재가": b})
            tmp_not_c.jango.update({"거래량": g})

            # 현재 가지고 있는 대상인지 파악
            if sCode in self.account_stock_dict.keys():
                try:
                    # 스탑로스 구현
                    print(self.account_stock_dict[sCode].jango["종목명"],(self.account_stock_dict[sCode].jango['체결가']-k)/self.account_stock_dict[sCode].jango['체결가'])
                    if self.account_stock_dict[sCode].jango["체결량"]>0 and self.account_stock_dict[sCode].jango['체결가']*(1-STOP_LOSS_RATE)>k:
                        count = self.account_stock_dict[sCode].jango["체결량"]
                        while count >0:
                            print("스탑로스 가동",self.account_stock_dict[sCode].jango['체결가'], k)
                            print('스탑로스 기준가',self.account_stock_dict[sCode].jango['체결가']*(1-STOP_LOSS_RATE))
                            ret = self.send_order("신규매도",sCode=sCode,order_quantity=1,order_price=b,hoga_type="시장가")
                            count -= 1
                            self.account_stock_dict[sCode].jango["체결량"]=count
                    elif self.account_stock_dict[sCode].jango["체결량"]>0 and self.account_stock_dict[sCode].jango['체결가']*(1+STOP_PROFIT_RATE)<b: # 익절
                        count = self.account_stock_dict[sCode].jango["체결량"]
                        while count >0:
                            print("스탑프로핏 가동",self.account_stock_dict[sCode].jango['체결가'], k)
                            print('스탑프로핏 기준가',self.account_stock_dict[sCode].jango['체결가']*(1+STOP_LOSS_RATE))
                            ret = self.send_order("신규매도",sCode=sCode,order_quantity=1,order_price=b,hoga_type="지정가")
                            count -= 1
                            self.account_stock_dict[sCode].jango["체결량"]=count

                except Exception as e:    
                    print(e)                
                    print("EXception 현재 가지고 있는 잔고 비교 정보",self.account_stock_dict[sCode].jango)
            try:
                #print("실시간 주식체결 정보 : ", self.not_concluded_account[sCode]["종목명"],a, b)
                pass
            except Exception as e:
                print("실시간 주식체결 정보 : ", sCode,a, b)


    def send_order(self,order_type, sCode, order_quantity, order_price, hoga_type, order_num=""):
        if order_type == "신규매수":
            type_dict = 1
        elif order_type =="신규매도":
            type_dict = 2
        elif order_type =="매수취소":
            type_dict = 3
        elif order_type =="매도취소":
            type_dict = 4
        elif order_type =="매수정정":
            type_dict = 5
        elif order_type =="매도정정":
            type_dict = 6

        if hoga_type =="지정가":
            hoga_dict = "00"
        elif hoga_type =="시장가":
            hoga_dict = "03"
        
        order_success = self.dynamicCall(
                        "SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                        [order_type, self.screen_meme_stock, self.account_num, type_dict, sCode, order_quantity, order_price, hoga_dict, order_num]
                    )
        if order_success == 0:
                        logging.debug("%s 전달 성공"%order_type)
                        print("%s 전달 성공"%order_type)
        else:
            logging.debug("%s 전달 실패"%order_type)
        return order_success

    # 실시간 체결 정보
    def chejan_slot(self, sGubun, nItemCnt, sFidList):

        if int(sGubun) == 0: #주문체결
            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목코드'])[1:]
            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['종목명'])
            stock_name = stock_name.strip()

            origin_order_number = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['원주문번호'])  # 출력 : defaluse : "000000"
            order_number = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문번호'])  # 출럭: 0115061 마지막 주문번호

            order_status = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문상태'])  # 출력: 접수, 확인, 체결
            order_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문수량'])  # 출력 : 3
            order_quan = int(order_quan)

            order_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문가격'])  # 출력: 21000
            order_price = int(order_price)

            not_chegual_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['미체결수량'])  # 출력: 15, default: 0
            not_chegual_quan = int(not_chegual_quan)

            order_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문구분'])  # 출력: -매도, +매수
            order_gubun = order_gubun.strip().lstrip('+').lstrip('-')

            chegual_time_str = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['주문/체결시간'])  # 출력: '151028'

            chegual_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결가'])  # 출력: 2110  default : ''
            if chegual_price == '':
                chegual_price = 0
            else:
                chegual_price = int(chegual_price)

            chegual_quantity = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['체결량'])  # 출력: 5  default : ''
            if chegual_quantity == '':
                chegual_quantity = 0
            else:
                chegual_quantity = int(chegual_quantity)

            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['현재가'])  # 출력: -6000
            current_price = abs(int(current_price))

            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['(최우선)매도호가'])  # 출력: -6010
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['주문체결']['(최우선)매수호가'])  # 출력: -6000
            first_buy_price = abs(int(first_buy_price))

            ######## 새로 들어온 주문이면 주문번호 할당
            if sCode not in self.not_concluded_account.keys():
                self.not_concluded_account[sCode]=Jango(sCode)
            tmp = self.not_concluded_account[sCode]
            tmp.jango.update({"종목코드": sCode})
            tmp.jango.update({"주문번호": order_number})
            tmp.jango.update({"종목명": stock_name})
            tmp.jango.update({"주문상태": order_status})
            tmp.jango.update({"주문수량": order_quan})
            tmp.jango.update({"주문가격": order_price})
            tmp.jango.update({"미체결수량": not_chegual_quan})
            tmp.jango.update({"원주문번호": origin_order_number})
            tmp.jango.update({"주문구분": order_gubun})
            tmp.jango.update({"체결가": chegual_price})
            tmp.jango.update({"체결량": chegual_quantity})
            tmp.jango.update({"현재가": current_price})
            tmp.update()
            print("주문체결")
            print(self.not_concluded_account[sCode].jango)

        elif int(sGubun) == 1: #잔고

            account_num = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['계좌번호'])
            sCode = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목코드'])[1:]

            stock_name = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['종목명'])
            stock_name = stock_name.strip()

            current_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['현재가'])
            current_price = abs(int(current_price))

            stock_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['보유수량'])
            stock_quan = int(stock_quan)

            like_quan = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['주문가능수량'])
            like_quan = int(like_quan)

            buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매입단가'])
            buy_price = abs(int(buy_price))

            total_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['총매입가']) # 계좌에 있는 종목의 총매입가
            total_buy_price = int(total_buy_price)

            meme_gubun = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['매도매수구분'])
            meme_gubun = self.realType.REALTYPE['매도수구분'][meme_gubun]

            first_sell_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매도호가'])
            first_sell_price = abs(int(first_sell_price))

            first_buy_price = self.dynamicCall("GetChejanData(int)", self.realType.REALTYPE['잔고']['(최우선)매수호가'])
            first_buy_price = abs(int(first_buy_price))

            if sCode not in self.jango_dict.keys():
                self.jango_dict.update({sCode:{}})

            self.jango_dict[sCode].update({"현재가": current_price})
            self.jango_dict[sCode].update({"종목코드": sCode})
            self.jango_dict[sCode].update({"종목명": stock_name})
            self.jango_dict[sCode].update({"보유수량": stock_quan})
            self.jango_dict[sCode].update({"주문가능수량": like_quan})
            self.jango_dict[sCode].update({"매입단가": buy_price})
            self.jango_dict[sCode].update({"총매입가": total_buy_price})
            self.jango_dict[sCode].update({"매도매수구분": meme_gubun})
            self.jango_dict[sCode].update({"(최우선)매도호가": first_sell_price})
            self.jango_dict[sCode].update({"(최우선)매수호가": first_buy_price})
            # print("잔고")
            # print(self.jango_dict)
            if stock_quan == 0:
                del self.jango_dict[sCode]

    #송수신 메세지 get
    def msg_slot(self, sScrNo, sRQName, sTrCode, msg):
        logging.debug("스크린: %s, 요청이름: %s, tr코드: %s --- %s" %(sScrNo, sRQName, sTrCode, msg))

# ui = Ui_class()

class Jango():
    def __init__(self, code):        
        self.jango=dict()
        self.jango["종목코드"]=code
        self.jango["종목명"] = ""        
        self.jango["체결가"]=0
        self.jango["현재가"]=0
        self.jango["체결량"]=0 #보유수량
        self.jango["주문번호"]=""
        self.jango["원주문번호"]=""
        self.jango["주문상태"]=""
        self.jango["주문수량"]=0
        self.jango["주문가격"]=0
        self.jango["주문구분"]=""
        self.jango["미체결수량"]=""
        self.jango["스크린번호"]=""
        self.jango["주문용스크린번호"]=""
        self.jango["손익률"]=0.
        # self.jango["평균단가"]=0
        self.jango["보유금액"]=0

    def update(self):
        #손익률
        if self.jango["체결가"] != 0:
            self.jango["손익률"] = (self.jango["현재가"]-self.jango["체결가"])/self.jango["체결가"]        
        #보유금액
        self.jango["보유금액"]=self.jango["체결가"]*self.jango["체결량"] #내용 확인해 보자. 기존 주식과 합산 계산 되는지 
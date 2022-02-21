from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import sys
from PyQt5.QtTest import *
from config.kiwoomType import *

class Ui_class():
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.kiwoom = Kiwoom()
        self.app.exec_()

class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()
        # Variable
        self.account_num = None
        self.account_stock_dict = dict()
        self.not_account_stock_dict = dict()
        self.realType = RealType()

        # Event Loop
        self.event_loop=QEventLoop()

        # 스크린 번호
        self.screen_my_info = "2000"
        self.screen_calculation_stock = "4000"
        self.screen_real_stock = "5000"
        self.screen_meme_stock = "6000"
        self.screen_start_stop_real = "1000"

        # 계좌 관련 변수
        self.use_money = 0
        self.use_money_percent = 0.5

        self.get_ocx_instance()
        self.event_slots()
        self.real_event_slots()
        self.sinal_login_commConnect()
        self.get_account_info()
        self.detail_account_info()
        self.detail_account_mystock()
        self.get_non_contract_status()   
        # self.calculator_fnc()     

        self.dynamicCall("SetRealReg(QString, QString, QString, QString", self.screen_start_stop_real, '', self.realType.REALTYPE['장시작시간']['장운영구분'],"0") #리얼타입 처음 등록할때는 0 이후는 1(추가)

    def get_ocx_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def event_slots(self):
        self.OnEventConnect.connect(self.login_slot)
        self.OnReceiveTrData.connect(self.trdata_slot)

    def real_event_slots(self):
        self.OnReceiveRealData.connect(self.real_data_slot)
    def login_slot(self,errCode):
        print("Login ErrCode:" ,errCode)
        self.event_loop.exit()
    def trdata_slot(self, sScrNo,sRQName,sTrCode,sRecordName,sPrevNext, arg):
        # print("sPrevNext: ",sPrevNext)
        """        
          [OnReceiveTrData() 이벤트]
          
          void OnReceiveTrData(
          BSTR sScrNo,       // 화면번호
          BSTR sRQName,      // 사용자 구분명
          BSTR sTrCode,      // TR이름
          BSTR sRecordName,  // 레코드 이름
          BSTR sPrevNext,    // 연속조회 유무를 판단하는 값 0: 연속(추가조회)데이터 없음, 2:연속(추가조회) 데이터 있음
          LONG nDataLength,  // 사용안함.
          BSTR sErrorCode,   // 사용안함.
          BSTR sMessage,     // 사용안함.
          BSTR sSplmMsg     // 사용안함.
          )
          
          요청했던 조회데이터를 수신했을때 발생됩니다.
          수신된 데이터는 이 이벤트내부에서 GetCommData()함수를 이용해서 얻어올 수 있습니다.
        """
        if sRQName =="예수금상세현황요청":
            deposit = self.dynamicCall("GetCommData(String,String,int,String)",sTrCode, sRQName, 0, "예수금")
            output_cash = self.dynamicCall("GetCommData(String,String,int,String)",sTrCode, sRQName, 0, "출금가능금액")
            print(deposit, output_cash)
            self.event_loop.exit()

        elif sRQName =="미체결요청":
            print("미체결요청")
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName) #멀티데이터의 정보를 가져오겠다는 뜻
            for i in range(rows):
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명").strip()
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호").strip()
                order_num = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문번호").strip())
                order_time = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "시간").strip())
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문상태").strip()
                order_quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문수량").strip())
                order_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문가격").strip())
                order_gubun = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "주문구분").strip() #"+매수", "-매도"
                not_quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "미체결수량").strip())
                ok_quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "체결량").strip())
            # 접수 -> 확인 -> 체결
            if order_num in self.not_account_stock_dict:
                pass
            else:
                self.not_account_stock_dict[order_num] = dict()
            nasd = self.not_account_stock_dict[order_num]
            nasd.update({"종목명":code_name})
            nasd.update({"종목코드":code})
            nasd.update({"주문번호":order_num})
            nasd.update({"시간":order_time})
            nasd.update({"주문상태":order_status})
            nasd.update({"주문수량":order_quantity})
            nasd.update({"주문가격":order_price})
            nasd.update({"주문구분":order_gubun})
            nasd.update({"미체결수량":not_quantity})
            nasd.update({"체결량":ok_quantity})

            print("미체결종목 : %s"%self.not_account_stock_dict[order_num])
            self.event_loop.exit()

        elif sRQName == "계좌평가잔고내역요청":
            total_buy_money = self.dynamicCall("GetCommData(String,String,int,String)",sTrCode, sRQName, 0, "총매입금액")
            total_buy_money_result = int(total_buy_money)
            print("총매입금액 %s"%total_buy_money_result)

            total_profit_loss_rate = self.dynamicCall("GetCommData(String,String,int,String)",sTrCode, sRQName, 0, "총수익률(%)")
            total_profit_loss_rate_result = float(total_profit_loss_rate)
            print("총수익률 (%%): %s"%total_profit_loss_rate_result)

            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName) #멀티데이터의 정보를 가져오겠다는 뜻

            for i in range(rows):
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목명").strip()
                code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "종목번호").strip()
                code = code.strip()[1:]
                stock_quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "보유수량").strip())
                buy_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입가").strip())
                learn_rate = float(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "수익률(%)").strip())
                current_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "현재가").strip())
                total_chegual_price = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매입금액").strip())
                possible_quantity = int(self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, i, "매매가능수량").strip())
                
                print(code_name, code, stock_quantity, buy_price, learn_rate, current_price, total_chegual_price, possible_quantity)
            if sPrevNext =="2":
                self.detail_account_mystock(sPrevNext=sPrevNext)
            else:
                self.event_loop.exit()
        
        elif sRQName == "주식일봉차트조회":
            print("주식일봉차트조회 요청")
            code = self.dynamicCall("GetCommData(QString, QString, int, QString)", sTrCode, sRQName, 0, "종목코드").strip()
            print(code)
            rows = self.dynamicCall("GetRepeatCnt(QString, QString)", sTrCode, sRQName) #멀티데이터의 정보를 가져오겠다는 뜻 
            if sPrevNext == "2":
                self.day_kiwoom_db(code=code, sPrevNext=sPrevNext)
            else:
                self.event_loop.exit()


    def sinal_login_commConnect(self):
        self.dynamicCall("CommConnect()")
        self.event_loop.exec_()

    def get_account_info(self):
        account_list = self.dynamicCall("GetLoginInfo(String", "ACCNO")
        """
        "ACCOUNT_CNT" : 보유계좌 갯수를 반환합니다.
          "ACCLIST" 또는 "ACCNO" : 구분자 ';'로 연결된 보유계좌 목록을 반환합니다.
          "USER_ID" : 사용자 ID를 반환합니다.
          "USER_NAME" : 사용자 이름을 반환합니다.
          "GetServerGubun" : 접속서버 구분을 반환합니다.(1 : 모의투자, 나머지 : 실거래서버)
          "KEY_BSECGB" : 키보드 보안 해지여부를 반환합니다.(0 : 정상, 1 : 해지)
          "FIREW_SECGB" : 방화벽 설정여부를 반환합니다.(0 : 미설정, 1 : 설정, 2 : 해지)
        """
        self.account_num = account_list.split(";")[1]

    def detail_account_info(self):
        self.dynamicCall("SetInputValue(String,String)"	,"계좌번호",self.account_num)
        self.dynamicCall("SetInputValue(String,String)"	,"비밀번호","")
        self.dynamicCall("SetInputValue(String,String)"	,"비밀번호입력매체구분","00")
        self.dynamicCall("SetInputValue(String,String)"	,"조회구분","2")
        rqname = "예수금상세현황요청" #내가 정한 요청이름
        trname = "opw00001"
        # (내가 지은 요청이름, TR번호, preNext, 화면번호)
        self.dynamicCall("CommRqData( String	,  String	,  int	,  String)", rqname, trname, "0",self.screen_my_info)        

        self.event_loop.exec_()
    def detail_account_mystock(self, sPrevNext="0"): # 처음조회 0 다음조회 2 # 다음 조회 꺼리가 있으면 2로 들어온다
        self.dynamicCall("SetInputValue(String,String)"	,"계좌번호",self.account_num)
        self.dynamicCall("SetInputValue(String,String)"	,"비밀번호","")
        self.dynamicCall("SetInputValue(String,String)"	,"비밀번호입력매체구분","00")
        self.dynamicCall("SetInputValue(String,String)"	,"조회구분","2")
        rqname = "계좌평가잔고내역요청" #내가 정한 요청이름
        trname = "opw00018"
        # (내가 지은 요청이름, TR번호, preNext, 화면번호)
        self.dynamicCall("CommRqData( String	,  String	,  int	,  String)", rqname, trname, sPrevNext,self.screen_my_info)        

        self.event_loop.exec_()

    def get_non_contract_status(self, sPrevNext="0"):
        self.dynamicCall("SetInputValue(String,String)"	,"계좌번호",self.account_num)
        # self.dynamicCall("SetInputValue(String,String)"	,"전체종목구분","0") # 0: 전체 1:종목
        self.dynamicCall("SetInputValue(String,String)"	,"매매구분","0") # 0 :전체 1: 매도 2: 매수
        # self.dynamicCall("SetInputValue(String,String)"	,"종목코드","")
        self.dynamicCall("SetInputValue(String,String)"	,"체결구분","1") # 0 :전체 2:체결 1:미체결
        rqname = "미체결요청" #내가 정한 요청이름
        trname = "opt10075"
        # (내가 지은 요청이름, TR번호, preNext, 화면번호)
        self.dynamicCall("CommRqData( String	,  String	,  int	,  String)", rqname, trname, sPrevNext,self.screen_my_info)
        self.event_loop.exec_()

    def get_code_list_by_market(self, market_code):
        code_list = self.dynamicCall("GetCodeListByMarket(QString", market_code) # 0 : 장내, 10: 코스닥
        code_list = code_list.split(";")[:-1]
        return code_list

    def day_kiwoom_db(self, code=None, date =None, sPrevNext="0"):

        QTest.qWait(3600) # 동작 자체를 멈추지 않고 다음 단계로 넘어가는것을 ms 단위로 대기

        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")

        if date != None:
            self.dynamicCall("SetInputValue(QString, QString)", "기준일자", date)
        self.dynamicCall("CommRqData(QString, QString, int, QString)","주식일봉차트조회", "opt10081", sPrevNext, self.screen_calculation_stock)

    def calculator_fnc(self):
        code_list = self.get_code_list_by_market("10")
        print("코스닥 개수 : %s"%len(code_list))

        for idx, code in enumerate(code_list):
            self.dynamicCall("DisconnectRealData(QString)", self.screen_calculation_stock)
            print("%s/%s : KOSDAQ : %s"%(idx+1, len(code_list), code))
            self.day_kiwoom_db(code)
            self.event_loop.exec_()
    def real_data_slot(self, sCode, sRealTye, sRealData):
        print(sCode)
k=Ui_class()
 
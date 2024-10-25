import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
import pandas as pd
import GiExpertControl as giLogin  # 통신모듈 - 로그인
import GiExpertControl as RTShow
import GiExpertControl as TRShow
from dotenv import load_dotenv
import os
import asyncio
from datetime import datetime

# load .env
load_dotenv()

INDI_ID = os.environ.get('INDI_ID')
INDI_PW = os.environ.get('INDI_PW')
PUBLIC_PW= os.environ.get('PUBLIC_PW')
GAEJWA = os.environ.get('GAEJWA')
GAEJWA_PW = os.environ.get('GAEJWA_PW')

async def wait_data(key, result):
    count = 0
    while key not in result:
        await asyncio.sleep(0.2)
        count += 1
        if count > 30:
            return 0
    return result[key]

class indiApp(QMainWindow):
    def __init__(self):
        super().__init__()
        TRShow.SetQtMode(True) 
        print('finish qt mode set')
        TRShow.RunIndiPython()
        giLogin.RunIndiPython()
        # RTShow.RunIndiPython()

        print('run python')

        self.rqidD = {}
        self.tempResult = {}

        print(giLogin.GetCommState())
        if giLogin.GetCommState() == 0:  # 정상
            print('정상')
        elif giLogin.GetCommState() == 1:  # 비정상
            print('비정상')
            # 본인의 ID 및 PW 넣으셔야 합니다.
            login_return = giLogin.StartIndi(
                INDI_ID, INDI_PW, PUBLIC_PW, 'C:\\SHINHAN-i\\indi\\GiExpertStarter.exe')
            if login_return == True:
                print("INDI 로그인 정보", "INDI 정상 호출")
                print(giLogin.GetCommState())
            else:
                print("INDI 로그인 정보", "INDI 호출 실패")

        self.read_jango()

        # time.sleep(5)
        TRShow.SetCallBack('ReceiveData', self.TRShow_ReceiveData)

        # 실시간 데이터 callback
        # RTShow.SetCallBack('ReceiveRTData', self.RTShow_ReceiveRTData)
    
    async def read_trade(self):
        gaejwa_text = GAEJWA
        PW_text = GAEJWA_PW
        TR_Name = "SABA231Q1"
        today_str = datetime.now().strftime('%Y%m%d')

        ret = TRShow.SetQueryName(TR_Name)
        ret = TRShow.SetSingleData(0, today_str)
        ret = TRShow.SetSingleData(1, gaejwa_text)
        ret = TRShow.SetSingleData(2, PW_text)
        ret = TRShow.SetSingleData(3, "00")
        ret = TRShow.SetSingleData(4, "1")
        ret = TRShow.SetSingleData(5, "1")
        ret = TRShow.SetSingleData(6, "*")
        ret = TRShow.SetSingleData(7, "")
        ret = TRShow.SetSingleData(8, "Y")

        rqid = TRShow.RequestData()
        # Error
        err_code = print(TRShow.GetErrorCode())
        err_msg = print(TRShow.GetErrorMessage())

        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        if str(rqid) == '0':
            return {"status": 502, "result": "전달 오류"}
        
        # ReceiveData 구분용
        self.rqidD[rqid] = TR_Name

        # Response 전달용
        temp = await wait_data(rqid, self.tempResult)
        self.tempResult = {}

        # error handling
        if temp == 0:
            return {"status": 500, "result": "error"}
        elif err_code == '0':
            return {"status": 500, "result": err_msg}
        else:
            return {"status": 200, "result": temp}


    async def read_jango(self):
        gaejwa_text = GAEJWA
        PW_text = GAEJWA_PW
        TR_Name = "SABA200QB"
        ret = TRShow.SetQueryName(TR_Name)          
        ret = TRShow.SetSingleData(0,gaejwa_text)
        ret = TRShow.SetSingleData(1,"01")
        ret = TRShow.SetSingleData(2,PW_text)

        rqid = TRShow.RequestData()
        # Error
        err_code = print(TRShow.GetErrorCode())
        err_msg = print(TRShow.GetErrorMessage())

        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        if str(rqid) == '0':
            return {"status": 502, "result": "전달 오류"}
        
        # ReceiveData 구분용
        self.rqidD[rqid] = TR_Name

        # Response 전달용
        temp = await wait_data(rqid, self.tempResult)
        self.tempResult = {}

        # error handling
        if temp == 0:
            return {"status": 500, "result": "error"}
        elif err_code == '0':
            return {"status": 500, "result": err_msg}
        else:
            return {"status": 200, "result": temp}

    async def order_stock(self, stockcode, quantity):
        # 한화손해보험 000370
        # 에스코넥 096630
        gaejwa_text = GAEJWA
        PW_text = GAEJWA_PW
        order_type ="2" # 매수
        code = stockcode # 에스코넥
        count = str(quantity)
        call_type="1"
        price="" # 시장가일때 ""
        
        TR_Name = "SABA101U1"         
        ret = TRShow.SetQueryName(TR_Name)
        ret = TRShow.SetSingleData(0, gaejwa_text)
        ret = TRShow.SetSingleData(1, "01") # 상품 구분 01 고정
        ret = TRShow.SetSingleData(2, PW_text)
        ret = TRShow.SetSingleData(3, "")
        ret = TRShow.SetSingleData(4, "")
        ret = TRShow.SetSingleData(5, '0') # 선물대용매도구분 0 -> 일반
        ret = TRShow.SetSingleData(6, '00') # 신용거래구분 00 -> 보통
        ret = TRShow.SetSingleData(7, order_type) # 매도매수구분 1:매도 2:매수
        ret = TRShow.SetSingleData(8, 'A' + code)
        ret = TRShow.SetSingleData(9, count) # 주문수량
        ret = TRShow.SetSingleData(10, price) # 주문가격
        ret = TRShow.SetSingleData(11, '1') # 정규장
        ret = TRShow.SetSingleData(12, call_type) # 호가유형, 1: 시장가, X:최유리, Y:최우선
        ret = TRShow.SetSingleData(13, '0') # 주문조건, 0:일반, 3:IOC, 4:FOK
        ret = TRShow.SetSingleData(14, '0') # 신용대출
        ret = TRShow.SetSingleData(15, "")
        ret = TRShow.SetSingleData(16, "")
        ret = TRShow.SetSingleData(17, "")
        ret = TRShow.SetSingleData(18, "")
        ret = TRShow.SetSingleData(19, "")
        ret = TRShow.SetSingleData(20, "")
        ret = TRShow.SetSingleData(21, 'Y') # 결과출력여부

        rqid = TRShow.RequestData()

        # Error   
        err_code = print(TRShow.GetErrorCode())
        err_msg = print(TRShow.GetErrorMessage())

        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        if str(rqid) == '0':
            return {"status": 502, "result": "전달 오류"}
        
        # ReceiveData 구분용
        self.rqidD[rqid] = TR_Name

        # Response 전달용
        temp = await wait_data(rqid, self.tempResult)
        self.tempResult = {}

        # error handling
        if temp == 0:
            return {"status": 500, "result": "error"}
        elif err_code == '0':
            return {"status": 500, "result": err_msg}
        else:
            return {"status": 200, "result": temp}

    def TRShow_ReceiveData(self,giCtrl,rqid):
        print("in receive_Data:",rqid)
        print('recv rqid: {}->{}\n'.format(rqid, self.rqidD[rqid]))
        TR_Name = self.rqidD[rqid]
        tr_data_output = []

        print("TR_name : ",TR_Name)
        if TR_Name == "SABA200QB":
            nCnt = giCtrl.GetMultiRowCount()
            try:
                for i in range(nCnt):
                    row_data = []  # 한 행의 데이터를 저장할 리스트
                    
                    # 선택한 열의 데이터만 가져와서 추가
                    stock_code = str(giCtrl.GetMultiData(i, 0))  # 종목코드
                    stock_name = str(giCtrl.GetMultiData(i, 1))  # 종목명
                    quantity = str(giCtrl.GetMultiData(i, 2))  # 결제일 잔고 수량
                    current_price = str(giCtrl.GetMultiData(i, 5))  # 현재가
                    average_price = str(giCtrl.GetMultiData(i, 6))  # 평단가

                    # 데이터를 리스트에 추가
                    row_data.append(stock_code)
                    row_data.append(stock_name)
                    row_data.append(quantity)
                    row_data.append(current_price)
                    row_data.append(average_price)

                    # 한 행의 데이터를 tr_data_output 리스트에 추가
                    tr_data_output.append(row_data)
                print(TRShow.GetErrorMessage())
                if len(tr_data_output) == 0:
                    raise ValueError("에러 발생 로그 확인")
                else:
                    self.tempResult[rqid] = tr_data_output
                    print(tr_data_output)
            except ValueError as e:
                self.tempResult[rqid] = 0
        
        if TR_Name == "SABA101U1":
            nCnt = giCtrl.GetSingleRowCount()
            print("nCnt : ",nCnt)
            try:
                row_data = {}
                row_data['Order_Num'] = str(giCtrl.GetSingleData(0))
                row_data['Num'] = str(giCtrl.GetSingleData(2))
                row_data['Msg1'] = str(giCtrl.GetSingleData(3))
                row_data['Msg2'] = str(giCtrl.GetSingleData(4))
                row_data['Msg3'] = str(giCtrl.GetSingleData(5))
                tr_data_output.append(row_data)
                print(TRShow.GetErrorMessage())
                if len(tr_data_output) == 0:
                    raise ValueError("에러 발생 로그 확인")
                else:
                    self.tempResult[rqid] = tr_data_output
                    print("매수 및 매도 주문결과: ", tr_data_output)
            except ValueError as e:
                self.callback_result[rqid] = 0

        if TR_Name == "SABA231Q1":
            nCnt = giCtrl.GetSingleRowCount()
            print("nCnt : ",nCnt)
            try:
                for i in range(nCnt):
                    row_data = []  # 한 행의 데이터를 저장할 리스트
                    order_code = str(giCtrl.GetMultiData(i, 0)) # 주문 번호
                    order_quantity = str(giCtrl.GetMultiData(i, 24)) # 체결수량  
                    order_price = str(giCtrl.GetMultiData(i, 25))  # 체결단가

                    row_data.append(order_code)
                    row_data.append(order_quantity)
                    row_data.append(order_price)

                    tr_data_output.append(row_data)
                print(TRShow.GetErrorMessage())
                if len(tr_data_output) == 0:
                    raise ValueError("에러 발생 로그 확인")
                else:
                    self.tempResult[rqid] = tr_data_output
                    print(tr_data_output)
            except ValueError as e:
                self.tempResult[rqid] = 0


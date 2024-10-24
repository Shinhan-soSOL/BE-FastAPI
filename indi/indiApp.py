import sys
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
import pandas as pd
import GiExpertControl as giLogin
import GiExpertControl as giJongmokTRShow
from dotenv import load_dotenv
import os
import asyncio

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

class indiWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # self.setWindowTitle("IndiQMainWindow
        #  App")
        giJongmokTRShow.SetQtMode(True)
        giJongmokTRShow.RunIndiPython()
        giLogin.RunIndiPython()
        print('run python')

        # RecieveData를 위한 dict
        self.rqidD = {}
        # api response용 dict
        self.callback_result = {}

        giJongmokTRShow.SetCallBack('ReceiveData', self.giJongmokTRShow_ReceiveData)
        
        # PyQt5를 통해 버튼만들고 함수와 연결시킵니다.
        # self.MainSymbol = ""
        # btnResearch = QPushButton("조회하기", self)
        # btnResearch.setGeometry(85, 20, 50, 20)
        # btnResearch.clicked.connect(self.read_jango)  # 버튼을 누르면 'btn_Search' 함수가 실행됩니다.

        print(giLogin.GetCommState())
        if giLogin.GetCommState() == 0: # 정상
            print("")        
        elif  giLogin.GetCommState() == 1: # 비정상
        #본인의 ID 및 PW 넣으셔야 합니다.
            login_return = giLogin.StartIndi(INDI_ID, INDI_PW, "", 'C:\\SHINHAN-i\\indi\\GiExpertStarter.exe')
            if login_return == True:
                print("INDI 로그인 정보","INDI 정상 호출")
            else:
                print("INDI 로그인 정보","INDI 호출 실패")

    async def read_jango(self):
        gaejwa_text = GAEJWA
        PW_text = GAEJWA_PW
        print("aaaa")
        TR_Name = "SABA200QB"
        ret = giJongmokTRShow.SetQueryName(TR_Name)          
        ret = giJongmokTRShow.SetSingleData(0,gaejwa_text)
        ret = giJongmokTRShow.SetSingleData(1,"01")
        ret = giJongmokTRShow.SetSingleData(2,PW_text)

        rqid = giJongmokTRShow.RequestData()
        print(type(rqid))
        print('Request Data rqid: ' + str(rqid))
        self.rqidD[rqid] = TR_Name

        # Response 전달용
        result = await wait_data(rqid, self.callback_result)
        self.callback_result = {}
        print("wait 함수는 실행된둣")

        return result

    def giJongmokTRShow_ReceiveData(self,giCtrl,rqid):
        print("in receive_Data:",rqid)
        print('recv rqid: {}->{}\n'.format(rqid, self.rqidD[rqid]))
        TR_Name = self.rqidD[rqid]
        tr_data_output = []

        print("TR_name : ",TR_Name)
        if TR_Name == "SABA200QB":
            nCnt = giCtrl.GetMultiRowCount()
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

            self.callback_result[rqid] = tr_data_output
            print(tr_data_output)
                

if __name__ == "__main__":
    app = QApplication(sys.argv)
    IndiWindow = indiWindow()    
    IndiWindow.show()
    app.exec_()

# 글로벌로 인스턴스 생성
# indi_instance = indiWindow()
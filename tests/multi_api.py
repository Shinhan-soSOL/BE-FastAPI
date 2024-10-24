from fastapi import FastAPI, Request
import threading
import sys, os
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
import indi_core
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

app = FastAPI()

indi_app_instance = None

load_dotenv()
DB_URL=os.environ.get('DB_URL')
DB_NAME=os.environ.get('DB_NAME')
DB_USER=os.environ.get('DB_USER')
DB_PW=os.environ.get('DB_PW')

def create_connection():
    try:
        connection = mysql.connector.connect(
            host = DB_URL,  # MySQL 서버 주소
            port = 3306,
            database = DB_NAME,  # 데이터베이스 이름
            user = DB_USER,  # MySQL 사용자 이름
            password = DB_PW  # MySQL 사용자 비밀번호
        )
        if connection.is_connected():
            print("MySQL 서버에 연결되었습니다.")
        return connection
    except Error as e:
        print(f"MySQL 연결 에러: {e}")
        return None

def update_or_insert_assets(account_id, assets):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # 현재 자산 조회
            select_query = "SELECT stock_code FROM asset WHERE account_id = %s"
            
            cursor.execute(select_query, (account_id,))
            existing_assets = cursor.fetchall()
            existing_asset_codes = {row[0] for row in existing_assets}  # 현재 DB에 있는 종목 코드들

            # 자산 업데이트 및 추가
            new_asset_codes = {asset['stock_code'] for asset in assets}
            for asset in assets:
                stock_code = asset['stock_code']
                if stock_code in existing_asset_codes:
                    # 기존 데이터 업데이트
                    update_query = """
                        UPDATE asset
                        SET stock_name = %s, quantity = %s, average_price = %s
                        WHERE account_id = %s AND stock_code = %s
                    """
                    cursor.execute(update_query, (
                        asset['stock_name'],
                        asset['quantity'],
                        asset['average_price'],
                        account_id,
                        stock_code
                    ))
                    print(f"기존 자산 업데이트됨: {stock_code}")
                else:
                    # 새 데이터 추가
                    insert_query = """
                        INSERT INTO asset (account_id, stock_name, quantity, average_price, stock_code)
                        VALUES (%s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_query, (
                        account_id,
                        asset['stock_name'],
                        asset['quantity'],
                        asset['average_price'],
                        stock_code
                    ))
                    print(f"새 자산 추가됨: {stock_code}")
            # 존재하지 않는 자산 삭제
            assets_to_delete = existing_asset_codes - new_asset_codes
            for stock_code in assets_to_delete:
                delete_query = """
                    DELETE FROM asset WHERE account_id = %s AND stock_code = %s
                """
                cursor.execute(delete_query, (account_id, stock_code))
                print(f"자산 삭제됨: {stock_code}")

            connection.commit()
        except Error as e:
            print(f"DB 저장/업데이트 에러: {e}")
        finally:
            cursor.close()
            connection.close()

# 히스토리 저장
def save_to_history(stock_code, quantity, result, current_balance, user_id):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()

            # result에서 필요한 값 추출
            stock_name = result['stock_name']  # 종목명
            trade_price = result['current_price']  # 현재가
            # result_change 계산 (잔액 - 현재가 * 수량)
            result_change = current_balance - (trade_price * quantity)

            # 현재 날짜와 시간을 trade_date로 저장
            trade_date = 'NOW()'
            insert_query = """
                INSERT INTO history (user_id, trade_date, stock_name, stock_code, trade_count, trade_price, result_change, is_jandon)
                VALUES (%s, NOW(), %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                user_id,
                stock_name,
                stock_code,
                quantity,
                trade_price,
                result_change,
                True 
            ))
            connection.commit()
            print("히스토리에 성공적으로 저장되었습니다.")
        except Error as e:
            print(f"히스토리 저장 에러: {e}")
        finally:
            cursor.close()
            connection.close()

# 잔돈 테이블 업데이트 함수 (total은 유지, current_balance만 업데이트)
def update_small_change(account_id, result_change):
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            # 기존 잔돈 정보를 account_id로 가져와서 current_balance만 업데이트
            update_query = """
                UPDATE small_change
                SET current_balance = %s
                WHERE account_id = %s
            """
            cursor.execute(update_query, (
                result_change,  # current_balance를 result_change로 업데이트
                account_id
            ))
            connection.commit()
            print("잔돈 테이블이 성공적으로 업데이트되었습니다.")
        except Error as e:
            print(f"잔돈 테이블 업데이트 에러: {e}")
        finally:
            cursor.close()
            connection.close()

def run_indi_app():
    global indi_app_instance

    app = QApplication(sys.argv)
    indi_app_instance = indi_core.indiApp()
    sys.exit(app.exec_())

def run_fastapi_server():
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8001)


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/jango/{account_id}")
async def get_jango(account_id: int):
    result = await indi_app_instance.read_jango()
    print(result)

    if result['status'] == 200:
        assets = []
        for item in result['result']:
            assets.append({
                "stock_code": item[0],
                "stock_name": item[1],
                "quantity": item[2],
                "current_price": item[3],
                "average_price": item[4]
            })
        update_or_insert_assets(account_id, assets)

    return {"data": result}

@app.post("/order")
async def get_order(request: Request):
    data = await request.json()
    stockCode = data.get("stockCode")
    quantity = data.get("quantity")
    currentBalance = data.get("currentBalance")
    user_id = data.get("user_id")
    account_id = data.get("account_id")

    result = await indi_app_instance.order_stock(stockCode, quantity)
    print(result)

    # 잔액 - 현재가 * 수량
    # 히스토리, 잔돈 업데이트
    if result['status'] == 200:
        result_change = currentBalance - (result['result']['current_price'] * quantity)
        save_to_history(stockCode, quantity, result['result'], currentBalance, user_id)
        update_small_change(account_id, result_change)

    return {"data": result}

if __name__ == "__main__":
    indi_thread = threading.Thread(target=run_indi_app)
    indi_thread.start()

    server_thread = threading.Thread(target=run_fastapi_server)
    server_thread.start()


# app.include_router(test_router.route)
# asyncio.create_task(test_router.consume())

import sys
from fastapi import FastAPI,APIRouter,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette import status
from tmessage import Message
from tconfig import loop, KAFKA_BOOTSTRAP_SERVERS, KAFKA_CONSUMER_GROUP, ACCOUNT_TOPIC, ORDER_TOPIC
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import json
import httpx 

route = APIRouter()

# -----------------------------------------------------------

@route.post('/create_message', status_code=status.HTTP_201_CREATED)
async def send(message: Message):
    producer = AIOKafkaProducer(
        loop=loop, bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS)
    try:
        await producer.start()
        value_json = json.dumps(message.__dict__).encode('utf-8')
        await producer.send_and_wait(topic=ACCOUNT_TOPIC, value=value_json)

        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={
                "status": "success",
                "message": "Message successfully sent to Kafka",
                "data": message.__dict__
            }
        )
    except ConnectionError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "error",
                "message": "Failed to connect to Kafka server"
            }
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": f"Invalid message format: {str(e)}"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }
        )
    finally:
        await producer.stop()

async def consume():
    consumer = AIOKafkaConsumer(ACCOUNT_TOPIC, loop=loop,
                                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS, group_id=KAFKA_CONSUMER_GROUP)
    await consumer.start()
    try:
        async for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg_dict = json.loads(msg_str)
            
            account_id = msg_dict["accountId"]
            user_id = msg_dict["usreId"]
            stockCode = msg_dict["stockCode"]
            quantity = msg_dict["quantity"] 
            currentBalance = msg_dict["currentBalance"] # 잔액

            print(f'Received message with value: {stockCode} {quantity}')
            async with httpx.AsyncClient() as client:
                order_data = {
                    "stockCode": stockCode,
                    "quantity": quantity,
                    "currentBalance": currentBalance,
                    "user_id": user_id,
                    "account_id": account_id
                }
                response = await client.post('http://localhost:8001/order', json=order_data)
                response2 = await client.get('http://localhost:8001/jango/{account_id}')
                if response.status_code == 200:
                    print(f"API 호출 성공: {response.json()}")
                    print(f"API 호출 성공: {response2.json()}")
                else:
                    print(f"API 호출 실패: {response.status_code}")

    finally:
        await consumer.stop()


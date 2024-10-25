from pydantic import BaseModel

class Message(BaseModel):
    stockCode: str
    currentBalance: int
    quantity: int
    userId: int
    accountId: int
    stockName: str
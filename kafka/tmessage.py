from pydantic import BaseModel

class Message(BaseModel):
    stockCode: str
    currentBalance: int
    quantity: int
    user_id: int
    account_id: int
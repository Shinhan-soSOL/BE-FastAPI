import asyncio
import test_router
from fastapi import FastAPI

app = FastAPI()
@app.get("/")
async def root():
    return {"message": "good response"}


app.include_router(test_router.route)
asyncio.create_task(test_router.consume())

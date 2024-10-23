import asyncio

from routers import router
from fastapi import FastAPI

app = FastAPI()
@app.get("/")
async def root():
    return {"message": "good response"}


app.include_router(router.route)
asyncio.create_task(router.consume())
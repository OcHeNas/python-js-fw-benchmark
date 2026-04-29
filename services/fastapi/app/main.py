import asyncio

from fastapi import FastAPI


app = FastAPI()


@app.get("/ping")
async def ping():
    return {"status": "ok"}


@app.get("/items")
async def items():
    return {"items": list(range(100))}


@app.get("/io")
async def io():
    await asyncio.sleep(0.01)
    return {"status": "ok"}

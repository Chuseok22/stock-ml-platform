import os

from fastapi import FastAPI

app = FastAPI(title=os.getenv("APP_NAME", "stock-ml-platform"))

@app.get("/health")
async def health():
  return {"status": "ok", "message": "시스템이 정상적으로 작동중입니다."}



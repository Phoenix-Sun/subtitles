from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.transcribe import app as transcribe_app
from api.whisper import app as whisper_app

app = FastAPI()

# 設定 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生產環境中應該限制為實際的前端網域
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 掛載子應用程式
app.mount("/api/transcribe", transcribe_app)
app.mount("/api/whisper", whisper_app)

@app.get("/")
async def root():
    return {"status": "ok", "message": "YouTube 字幕下載 API 服務運作中"} 
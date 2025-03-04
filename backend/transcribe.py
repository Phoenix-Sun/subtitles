from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi
import re

app = FastAPI()

class TranscribeRequest(BaseModel):
    video_url: str

class TranscribeResponse(BaseModel):
    text: str
    source: str  # 'youtube' 或 'whisper'
    status: str

def extract_video_id(url: str) -> Optional[str]:
    """從 URL 中擷取影片 ID"""
    m = re.search(r'(?:v=|youtu\.be/)([^?&]+)', url)
    return m.group(1) if m else None

def get_youtube_transcript(video_id: str) -> Optional[str]:
    """嘗試獲取 YouTube 字幕"""
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            transcript_data = transcript.fetch()
            return "\n".join(entry.get('text', '') for entry in transcript_data)
    except Exception:
        return None

@app.post("/api/transcribe")
async def transcribe(request: TranscribeRequest) -> TranscribeResponse:
    video_id = extract_video_id(request.video_url)
    if not video_id:
        raise HTTPException(status_code=400, detail="無效的 YouTube 網址")

    # 嘗試獲取 YouTube 字幕
    transcript = get_youtube_transcript(video_id)
    if transcript:
        return TranscribeResponse(
            text=transcript,
            source="youtube",
            status="success"
        )

    # 如果沒有字幕，返回狀態碼讓前端知道需要使用備用服務
    raise HTTPException(
        status_code=404,
        detail="找不到字幕，請使用音訊轉錄服務"
    ) 
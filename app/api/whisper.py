import os
import tempfile
from typing import Optional, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import whisper
from pydub import AudioSegment

app = FastAPI()

# 初始化 Whisper 模型
model = whisper.load_model("base")

class WhisperRequest(BaseModel):
    video_url: str

class WhisperResponse(BaseModel):
    text: str
    status: str

def split_audio(audio_path: str, segment_length: int = 60000) -> List[str]:
    """將音訊檔案分割成較小的片段（預設每段 60 秒）"""
    audio = AudioSegment.from_mp3(audio_path)
    segments = []
    
    for i in range(0, len(audio), segment_length):
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            segment = audio[i:i + segment_length]
            segment.export(temp_file.name, format="mp3")
            segments.append(temp_file.name)
    
    return segments

def download_audio(video_url: str) -> Optional[str]:
    """下載 YouTube 影片的音訊"""
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': temp_file.name,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            return temp_file.name
        except Exception as e:
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
            raise HTTPException(status_code=400, detail=f"下載失敗：{str(e)}")

@app.post("/api/whisper")
async def transcribe_audio(request: WhisperRequest) -> WhisperResponse:
    try:
        # 下載音訊
        audio_path = download_audio(request.video_url)
        
        try:
            # 分割音訊
            segments = split_audio(audio_path)
            
            # 處理每個片段
            transcripts = []
            for segment_path in segments:
                try:
                    result = model.transcribe(segment_path)
                    transcripts.append(result["text"])
                finally:
                    if os.path.exists(segment_path):
                        os.unlink(segment_path)
            
            return WhisperResponse(
                text="\n".join(transcripts),
                status="success"
            )
        finally:
            # 清理原始音訊檔案
            if os.path.exists(audio_path):
                os.unlink(audio_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本程式使用 Flask 建立 Web 介面，
讓使用者輸入 YouTube 影片網址後，
利用 youtube_transcript_api 取得影片字幕，
如果沒有字幕則使用 AI 進行音訊轉錄。
"""

import os
import re
import threading
import webbrowser
import yt_dlp
import whisper
import subprocess
from flask import Flask, request, render_template_string, Response
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'any_secret_key_for_local_dev')

# 初始化 Whisper 模型
whisper_model = whisper.load_model("base")

# HTML 前端頁面：首頁表單
home_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>YouTube 字幕下載工具</title>
  <style>
    body { 
      font-family: Arial, sans-serif; 
      background-color: #f5f5f5; 
      margin: 0; 
      padding: 20px; 
    }
    .container {
      max-width: 600px;
      margin: 0 auto;
      background-color: #fff;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 0 10px rgba(0,0,0,0.1);
    }
    input[type="text"] {
      width: calc(100% - 22px);
      padding: 10px;
      margin-bottom: 10px;
      border: 1px solid #ccc;
      border-radius: 4px;
    }
    button {
      padding: 10px 20px;
      background-color: #ff0000;
      color: #fff;
      border: none;
      border-radius: 4px;
      cursor: pointer;
    }
  </style>
</head>
<body>
<div class="container">
  <h1>YouTube 字幕下載工具</h1>
  <form action="/download" method="post">
    <input type="text" name="video_url" placeholder="請輸入 YouTube 影片網址" required>
    <button type="submit">取得字幕</button>
  </form>
</div>
</body>
</html>
"""

# HTML 模板：顯示字幕並提供「複製」功能
result_template = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>字幕結果</title>
  <style>
    body { font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }
    .container { max-width: 800px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    textarea { width: 100%; height: 400px; padding: 10px; font-size: 14px; }
    button { padding: 10px 20px; background-color: #007bff; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
    a { text-decoration: none; color: #007bff; }
  </style>
  <script>
    function copyText() {
      var textArea = document.getElementById("subtitleText");
      textArea.select();
      document.execCommand("copy");
      alert("字幕已複製到剪貼簿！");
    }
  </script>
</head>
<body>
<div class="container">
  <h1>字幕結果</h1>
  <textarea id="subtitleText" readonly>{{ srt_content }}</textarea>
  <br><br>
  <button onclick="copyText()">複製字幕</button>
  <br><br>
  <a href="/">回首頁</a>
</div>
</body>
</html>
"""

def extract_video_id(url):
    """
    從 URL 中擷取影片 ID，支援一般網址與 youtu.be 短網址格式
    """
    m = re.search(r'(?:v=|youtu\.be/)([^?&]+)', url)
    if m:
        return m.group(1)
    return None

def format_time(seconds):
    """
    將秒數轉換為 SRT 格式的時間字串 (hh:mm:ss,ms)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def convert_transcript_to_text(transcript):
    """
    將取得的字幕內容轉換為純文字格式
    transcript 為 list，每個元素為字典，包含 'text'
    """
    text = ""
    for entry in transcript:
        text += f"{entry.get('text', '')}\n"
    return text.strip()

def check_ffmpeg():
    """
    檢查系統是否安裝了 FFmpeg
    """
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return True
    except FileNotFoundError:
        return False

def download_audio(video_id):
    """
    下載 YouTube 影片的音訊
    """
    if not check_ffmpeg():
        raise RuntimeError(
            "找不到 FFmpeg！請先安裝 FFmpeg：\n"
            "Windows: 使用 chocolatey 安裝：choco install ffmpeg\n"
            "或從 https://www.gyan.dev/ffmpeg/builds/ 下載並加入系統 PATH"
        )

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'temp_{video_id}.%(ext)s',
        # 添加 headers 來模擬瀏覽器請求
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
        'quiet': False,
        'no_warnings': False,
        'cookiesfrombrowser': ('chrome',),
        'ignoreerrors': True,
        'nocheckcertificate': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f'https://www.youtube.com/watch?v={video_id}', download=True)
            # 獲取實際下載的檔案名稱
            if 'requested_downloads' in info:
                for d in info['requested_downloads']:
                    if d['filepath'].endswith('.mp3'):
                        return d['filepath']
            return f'temp_{video_id}.mp3'
    except Exception as e:
        print(f"下載失敗：{str(e)}")
        raise

def process_audio(audio_path):
    """
    使用 Whisper 處理音訊並轉換為文字
    """
    result = whisper_model.transcribe(audio_path)
    return result["text"]

def cleanup_temp_files(video_id):
    """
    清理臨時檔案
    """
    temp_file = f'temp_{video_id}.mp3'
    if os.path.exists(temp_file):
        os.remove(temp_file)

@app.route("/", methods=["GET"])
def index():
    # 回傳首頁表單頁面
    return render_template_string(home_template)

@app.route("/download", methods=["POST"])
def download_subtitle():
    video_url = request.form.get("video_url")
    if not video_url:
        return "請提供影片網址", 400

    video_id = extract_video_id(video_url)
    if not video_id:
        return "無法解析影片 ID", 400

    srt_content = None
    
    # 首先嘗試取得 YouTube 字幕
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
        for transcript in transcript_list:
            transcript_data = transcript.fetch()
            srt_content = convert_transcript_to_text(transcript_data)
            break
    except Exception as e:
        print(f"無法取得 YouTube 字幕：{str(e)}")
        
    # 如果沒有取得字幕，使用 Whisper 處理
    if not srt_content:
        try:
            print("開始使用 Whisper 處理音訊...")
            audio_path = download_audio(video_id)
            try:
                srt_content = process_audio(audio_path)
            finally:
                cleanup_temp_files(video_id)
        except Exception as e:
            return f"音訊處理失敗：{str(e)}", 400

    if not srt_content:
        return "無法產生字幕內容", 400

    return render_template_string(result_template, srt_content=srt_content)

def open_browser():
    webbrowser.open("http://127.0.0.1:5000/")

if __name__ == "__main__":
    # 延遲 1 秒後自動開啟預設瀏覽器
    threading.Timer(1, open_browser).start()
    # 啟動 Flask 伺服器，只監聽本地端的 5000 port
    app.run(debug=True, host="127.0.0.1", port=5000)

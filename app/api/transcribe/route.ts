import { NextResponse } from 'next/server'
import { YouTubeTranscriptApi } from 'youtube-transcript-api'

export async function POST(request: Request) {
  try {
    const { video_url } = await request.json()
    
    // 從 URL 中提取影片 ID
    const videoId = extractVideoId(video_url)
    if (!videoId) {
      return NextResponse.json(
        { error: '無效的 YouTube 網址' },
        { status: 400 }
      )
    }

    // 獲取字幕
    const transcript = await getTranscript(videoId)
    if (!transcript) {
      return NextResponse.json(
        { error: '無法取得字幕' },
        { status: 404 }
      )
    }

    return NextResponse.json({ text: transcript })
  } catch (error) {
    console.error('字幕下載失敗:', error)
    return NextResponse.json(
      { error: '字幕下載失敗' },
      { status: 500 }
    )
  }
}

function extractVideoId(url: string): string | null {
  const match = url.match(/(?:v=|youtu\.be\/)([^?&]+)/)
  return match ? match[1] : null
}

async function getTranscript(videoId: string): Promise<string | null> {
  try {
    const transcriptList = await YouTubeTranscriptApi.list_transcripts(videoId)
    const transcript = await transcriptList.fetch()
    return transcript.map(entry => entry.text).join('\n')
  } catch {
    return null
  }
} 
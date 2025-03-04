'use client'

import { useState } from 'react'

export default function Home() {
  const [url, setUrl] = useState('')
  const [transcript, setTranscript] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setTranscript('')
    
    try {
      const response = await fetch('/api/transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_url: url })
      })

      if (!response.ok) {
        throw new Error('無法取得字幕')
      }

      const data = await response.json()
      setTranscript(data.text)
    } catch (err) {
      setError(err instanceof Error ? err.message : '發生錯誤')
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 text-center">
          YouTube 字幕下載工具
        </h1>
        
        <form onSubmit={handleSubmit} className="space-y-4 mb-8">
          <div>
            <label htmlFor="url" className="block text-sm font-medium mb-2">
              YouTube 影片網址
            </label>
            <input
              type="text"
              id="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-500 text-white py-2 px-4 rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
          >
            {loading ? '處理中...' : '取得字幕'}
          </button>
        </form>

        {error && (
          <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-8">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {transcript && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold">字幕內容</h2>
            <div className="relative">
              <textarea
                value={transcript}
                readOnly
                className="w-full h-64 p-3 border border-gray-300 rounded-md shadow-sm"
              />
              <button
                onClick={() => navigator.clipboard.writeText(transcript)}
                className="absolute top-2 right-2 bg-white border border-gray-300 rounded-md px-3 py-1 text-sm hover:bg-gray-50"
              >
                複製
              </button>
            </div>
          </div>
        )}
      </div>
    </main>
  )
} 
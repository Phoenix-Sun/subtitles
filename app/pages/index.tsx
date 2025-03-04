import React, { useState, ChangeEvent } from 'react'
import { Box, Button, Container, TextField, Typography, Paper, LinearProgress } from '@mui/material'

export default function Home() {
  const [url, setUrl] = useState('')
  const [transcript, setTranscript] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [progress, setProgress] = useState(0)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')
    setProgress(0)
    setTranscript('')
    
    try {
      // 首先嘗試從 YouTube 獲取字幕
      const response = await fetch('/api/transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ video_url: url })
      })

      if (response.status === 404) {
        setProgress(10)
        // 如果沒有字幕，使用音訊轉錄服務
        const whisperResponse = await fetch('/api/whisper', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ video_url: url })
        })
        
        if (!whisperResponse.ok) {
          throw new Error('音訊轉錄失敗')
        }
        
        const data = await whisperResponse.json()
        setTranscript(data.text)
        setProgress(100)
      } else if (response.ok) {
        const data = await response.json()
        setTranscript(data.text)
        setProgress(100)
      } else {
        throw new Error('處理失敗')
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : '發生錯誤'
      setError(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleUrlChange = (e: ChangeEvent<HTMLInputElement>) => {
    setUrl(e.target.value)
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper elevation={3} sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          YouTube 字幕下載工具
        </Typography>
        
        <Box component="form" onSubmit={handleSubmit} sx={{ mb: 4 }}>
          <TextField
            fullWidth
            label="YouTube 影片網址"
            value={url}
            onChange={handleUrlChange}
            margin="normal"
            required
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? '處理中...' : '取得字幕'}
          </Button>
        </Box>

        {loading && (
          <Box sx={{ width: '100%', mb: 2 }}>
            <LinearProgress variant="determinate" value={progress} />
            <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
              {progress < 100 ? '處理中...' : '完成！'}
            </Typography>
          </Box>
        )}

        {error && (
          <Typography color="error" sx={{ mb: 2 }}>
            {error}
          </Typography>
        )}

        {transcript && (
          <Box>
            <Typography variant="h6" gutterBottom>
              字幕內容
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={10}
              value={transcript}
              InputProps={{ readOnly: true }}
            />
            <Button
              variant="outlined"
              onClick={() => navigator.clipboard.writeText(transcript)}
              sx={{ mt: 2 }}
            >
              複製文字
            </Button>
          </Box>
        )}
      </Paper>
    </Container>
  )
} 
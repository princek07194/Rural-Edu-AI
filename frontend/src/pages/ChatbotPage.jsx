import { useEffect, useState, useRef } from 'react'
import { useParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { FiSend, FiTrash2, FiMic } from 'react-icons/fi'
import { chatAPI, videoAPI } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

function TypingIndicator() {
  return (
    <div className="flex gap-1 p-3">
      {[0, 1, 2].map((i) => (
        <div key={i} className="w-2 h-2 bg-primary-500 rounded-full typing-dot" />
      ))}
    </div>
  )
}

export default function ChatbotPage() {
  const { videoId } = useParams()
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [video, setVideo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [listening, setListening] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    Promise.all([
      videoAPI.get(videoId),
      chatAPI.history(videoId),
    ]).then(([videoRes, histRes]) => {
      setVideo(videoRes.data.video)
      setMessages(histRes.data.history || [])
    }).finally(() => setLoading(false))
  }, [videoId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, sending])

  const sendMessage = async (text) => {
    const msg = text || input.trim()
    if (!msg) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', message: msg }])
    setSending(true)
    try {
      const res = await chatAPI.send(videoId, msg)
      setMessages((m) => [...m, { role: 'assistant', message: res.data.reply }])
    } catch (err) {
      toast.error(err.response?.data?.error || 'Failed to get response')
      setMessages((m) => m.slice(0, -1))
    } finally {
      setSending(false)
    }
  }

  const clearChat = async () => {
    await chatAPI.clear(videoId)
    setMessages([])
    toast.success('Chat cleared')
  }

  const voiceInput = () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SR) return toast.error('Voice not supported')
    const rec = new SR()
    rec.lang = 'en-US'
    rec.onstart = () => setListening(true)
    rec.onend = () => setListening(false)
    rec.onresult = (e) => sendMessage(e.results[0][0].transcript)
    rec.start()
  }

  if (loading) return <LoadingSpinner fullScreen />

  return (
    <div className="max-w-3xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
      <div className="mb-4">
        <h1 className="text-xl font-bold">AI Tutor</h1>
        <p className="text-slate-500 text-sm truncate">{video?.title}</p>
      </div>

      <div className="flex-1 glass-card flex flex-col overflow-hidden">
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 && (
            <p className="text-center text-slate-500 text-sm py-8">
              Ask anything about this video. I'll answer based on the transcript and notes.
            </p>
          )}
          {messages.map((m, i) => (
            <motion.div key={i}
              className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
              <div className={`max-w-[85%] p-4 rounded-2xl text-sm ${
                m.role === 'user'
                  ? 'bg-primary-600 text-white rounded-br-md'
                  : 'bg-slate-100 dark:bg-slate-800 rounded-bl-md'
              }`}>
                {m.role === 'assistant' ? (
                  <span className="whitespace-pre-wrap">{m.message}</span>
                ) : m.message}
              </div>
            </motion.div>
          ))}
          {sending && (
            <div className="flex justify-start">
              <div className="bg-slate-100 dark:bg-slate-800 rounded-2xl rounded-bl-md">
                <TypingIndicator />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="p-4 border-t border-slate-200 dark:border-slate-700 flex gap-2">
          <button onClick={clearChat} className="p-3 rounded-xl border hover:bg-slate-50 dark:hover:bg-slate-800" title="Clear chat">
            <FiTrash2 size={18} />
          </button>
          <button onClick={voiceInput} className={`p-3 rounded-xl border ${listening ? 'border-red-500 text-red-500' : ''}`}>
            <FiMic size={18} />
          </button>
          <input
            className="input-field flex-1"
            placeholder="Ask about the video content..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), sendMessage())}
          />
          <button onClick={() => sendMessage()} disabled={sending} className="gradient-btn px-4">
            <FiSend size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}

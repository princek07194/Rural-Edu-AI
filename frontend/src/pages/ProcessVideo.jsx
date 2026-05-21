import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { FiYoutube, FiMic, FiVolume2, FiFileText } from 'react-icons/fi'
import { videoAPI } from '../services/api'
import { getErrorMessage } from '../utils/getErrorMessage'
import LoadingSpinner from '../components/LoadingSpinner'

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'hi', label: 'Hindi (हिंदी)' },
  { value: 'pa', label: 'Punjabi (ਪੰਜਾਬੀ)' },
  { value: 'bho', label: 'Bhojpuri (भोजपुरी)' },
]

export default function ProcessVideo() {
  const [url, setUrl] = useState('')
  const [language, setLanguage] = useState('en')
  const [loading, setLoading] = useState(false)
  const [listening, setListening] = useState(false)
  const [useManual, setUseManual] = useState(false)
  const [manualTranscript, setManualTranscript] = useState('')
  const [aiMode, setAiMode] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((d) => setAiMode(d.ai_mode))
      .catch(() => setAiMode('unknown'))
  }, [])

  const handleProcess = async (e) => {
    e.preventDefault()
    if (!url.trim()) return toast.error('Enter a YouTube URL')
    if (useManual && manualTranscript.trim().length < 50) {
      return toast.error('Paste at least 50 characters of transcript text')
    }
    setLoading(true)
    try {
      const payload = { youtube_url: url, language }
      if (useManual && manualTranscript.trim()) {
        payload.manual_transcript = manualTranscript.trim()
      }
      const res = await videoAPI.process(payload)
      toast.success('Video processed successfully!')
      navigate(`/notes/${res.data.video.id}`)
    } catch (err) {
      const msg = getErrorMessage(err, 'Processing failed')
      toast.error(msg, { duration: 6000 })
      // If auto-fetch failed, suggest manual mode
      if (!useManual && /transcript|caption|blocked|fetch/i.test(msg)) {
        setUseManual(true)
        toast('Tip: Paste transcript manually using the option below', { icon: '💡' })
      }
    } finally {
      setLoading(false)
    }
  }

  const startVoiceInput = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return toast.error('Speech recognition not supported in this browser')
    const recognition = new SpeechRecognition()
    recognition.lang = language === 'hi' ? 'hi-IN' : language === 'pa' ? 'pa-IN' : 'en-US'
    recognition.onstart = () => setListening(true)
    recognition.onend = () => setListening(false)
    recognition.onresult = (e) => setUrl(e.results[0][0].transcript)
    recognition.onerror = () => { setListening(false); toast.error('Voice input failed') }
    recognition.start()
  }

  const speakInstructions = () => {
    const utterance = new SpeechSynthesisUtterance(
      'Use videos with captions enabled. If auto fetch fails, open transcript on YouTube and paste it manually.'
    )
    utterance.lang = language === 'hi' ? 'hi-IN' : language === 'pa' ? 'pa-IN' : 'en-US'
    speechSynthesis.speak(utterance)
  }

  if (loading) {
    return (
      <motion.div className="flex flex-col items-center justify-center min-h-[60vh] gap-6">
        <LoadingSpinner text="Processing video with AI..." />
        <motion.p className="text-slate-500 text-center max-w-md" animate={{ opacity: [0.5, 1, 0.5] }} transition={{ repeat: Infinity, duration: 2 }}>
          {useManual ? 'Using your transcript → Generating notes & MCQs...' : 'Fetching transcript → Generating notes → Creating MCQs...'}
        </motion.p>
      </motion.div>
    )
  }

  return (
    <motion.div className="max-w-2xl mx-auto">
      <h1 className="text-2xl font-display font-bold mb-2">Process YouTube Video</h1>
      <p className="text-slate-500 mb-2">Paste an educational video URL to generate AI study material</p>
      {aiMode === 'local' && (
        <p className="text-sm text-amber-600 dark:text-amber-400 mb-6 p-3 rounded-lg bg-amber-50 dark:bg-amber-900/20">
          Using built-in local AI (no API key needed). Add GEMINI_API_KEY in backend/.env for smarter results.
        </p>
      )}
      {aiMode === 'cloud' && (
        <p className="text-sm text-green-600 mb-6">✓ Gemini AI connected</p>
      )}
      {aiMode !== 'local' && aiMode !== 'cloud' && <div className="mb-6" />}

      <motion.form onSubmit={handleProcess} className="glass-card p-8 space-y-6" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
        <div>
          <label className="block text-sm font-medium mb-2">YouTube URL</label>
          <div className="relative">
            <FiYoutube className="absolute left-4 top-1/2 -translate-y-1/2 text-red-500" size={20} />
            <input
              className="input-field pl-12"
              placeholder="https://www.youtube.com/watch?v=..."
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
          </div>
          <div className="flex gap-2 mt-2 flex-wrap">
            <button type="button" onClick={startVoiceInput}
              className={`text-sm px-3 py-1.5 rounded-lg border flex items-center gap-1 ${listening ? 'border-red-500 text-red-500' : 'border-slate-300 dark:border-slate-600'}`}>
              <FiMic size={14} /> {listening ? 'Listening...' : 'Voice Input'}
            </button>
            <button type="button" onClick={speakInstructions} className="text-sm px-3 py-1.5 rounded-lg border border-slate-300 dark:border-slate-600 flex items-center gap-1">
              <FiVolume2 size={14} /> Help
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Output Language</label>
          <select className="input-field" value={language} onChange={(e) => setLanguage(e.target.value)}>
            {LANGUAGES.map((l) => <option key={l.value} value={l.value}>{l.label}</option>)}
          </select>
        </div>

        {/* Manual transcript fallback */}
        <div className="border border-amber-200 dark:border-amber-800 rounded-xl p-4 bg-amber-50/50 dark:bg-amber-900/10">
          <label className="flex items-center gap-2 cursor-pointer font-medium text-sm">
            <input
              type="checkbox"
              checked={useManual}
              onChange={(e) => setUseManual(e.target.checked)}
              className="rounded border-slate-300"
            />
            <FiFileText className="text-amber-600" />
            Paste transcript manually (if auto-fetch fails)
          </label>
          {useManual && (
            <motion.div className="mt-3" initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
              <textarea
                className="input-field min-h-[160px] text-sm"
                placeholder="Open video on YouTube → ⋮ menu → Show transcript → Copy all text → Paste here..."
                value={manualTranscript}
                onChange={(e) => setManualTranscript(e.target.value)}
              />
              <p className="text-xs text-slate-500 mt-2">
                Minimum 50 characters. On YouTube: click <strong>⋯</strong> below video → <strong>Show transcript</strong> → select all → copy → paste.
              </p>
            </motion.div>
          )}
        </div>

        <button type="submit" className="gradient-btn w-full">
          {useManual ? 'Generate from Pasted Transcript' : 'Generate Study Material'}
        </button>

        <div className="text-xs text-slate-500 space-y-1">
          <p>• Use videos with <strong>CC / captions</strong> turned ON</p>
          <p>• NCERT, Khan Academy, and educational channels work best</p>
          <p>• If &quot;failed to fetch transcript&quot; appears → enable manual paste above</p>
          <p>• Processing takes 30–90 seconds (AI generation)</p>
        </div>
      </motion.form>
    </motion.div>
  )
}

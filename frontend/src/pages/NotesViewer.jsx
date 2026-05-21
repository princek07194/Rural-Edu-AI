import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import toast from 'react-hot-toast'
import { FiDownload, FiBookmark, FiMessageCircle, FiHelpCircle, FiVolume2 } from 'react-icons/fi'
import { videoAPI, downloadAPI, bookmarkAPI, translateAPI } from '../services/api'
import { downloadBlob } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

const TABS = ['summary', 'detailed', 'short', 'keywords', 'topics', 'questions']

export default function NotesViewer() {
  const { videoId } = useParams()
  const [content, setContent] = useState(null)
  const [activeTab, setActiveTab] = useState('summary')
  const [loading, setLoading] = useState(true)
  const [translating, setTranslating] = useState(false)

  useEffect(() => {
    videoAPI.getContent(videoId)
      .then((res) => setContent(res.data))
      .catch(() => toast.error('Failed to load content'))
      .finally(() => setLoading(false))
  }, [videoId])

  const handleDownload = async (type) => {
    try {
      const apis = { notes: downloadAPI.notes, mcqs: downloadAPI.mcqs, summary: downloadAPI.summary }
      const res = await apis[type](videoId)
      downloadBlob(res.data, `${type}_${content.video.video_id}.pdf`)
      toast.success('Download started')
    } catch {
      toast.error('Download failed')
    }
  }

  const handleBookmark = async () => {
    try {
      await bookmarkAPI.add({ video_id: parseInt(videoId) })
      toast.success('Bookmarked!')
    } catch {
      toast.error('Bookmark failed')
    }
  }

  const speakNotes = (text) => {
    const utterance = new SpeechSynthesisUtterance(text?.slice(0, 500) || '')
    utterance.lang = content?.video?.language === 'hi' ? 'hi-IN' : 'en-US'
    speechSynthesis.speak(utterance)
  }

  const handleTranslate = async (targetLang) => {
    const note = getActiveContent()
    if (!note) return
    setTranslating(true)
    try {
      const res = await translateAPI.translate({ text: note, target_language: targetLang })
      setContent((prev) => {
        const updated = { ...prev }
        if (activeTab === 'summary') updated.summary = { ...updated.summary, content: res.data.translated_text }
        else {
          const idx = updated.notes.findIndex((n) => n.note_type === activeTab)
          if (idx >= 0) updated.notes[idx] = { ...updated.notes[idx], content: res.data.translated_text }
        }
        return updated
      })
      toast.success('Translated!')
    } catch {
      toast.error('Translation failed')
    } finally {
      setTranslating(false)
    }
  }

  const getActiveContent = () => {
    if (!content) return ''
    if (activeTab === 'summary') return content.summary?.content
    if (activeTab === 'questions') {
      return content.questions?.map((q) => `Q: ${q.question}\nA: ${q.sample_answer}`).join('\n\n')
    }
    return content.notes?.find((n) => n.note_type === activeTab)?.content || ''
  }

  if (loading) return <LoadingSpinner fullScreen />
  if (!content?.video) return <p>Video not found</p>

  const { video, summary, notes, questions } = content

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-4 justify-between items-start">
        <div className="flex gap-4">
          {video.thumbnail_url && <img src={video.thumbnail_url} alt="" className="w-32 rounded-xl" />}
          <div>
            <h1 className="text-xl font-bold">{video.title}</h1>
            <p className="text-slate-500 text-sm">{video.channel_name} • {video.language?.toUpperCase()}</p>
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <button onClick={() => handleDownload('summary')} className="px-3 py-2 rounded-lg border text-sm flex items-center gap-1 hover:bg-slate-50 dark:hover:bg-slate-800">
            <FiDownload size={14} /> Summary PDF
          </button>
          <button onClick={() => handleDownload('notes')} className="px-3 py-2 rounded-lg border text-sm flex items-center gap-1 hover:bg-slate-50 dark:hover:bg-slate-800">
            <FiDownload size={14} /> Notes PDF
          </button>
          <button onClick={handleBookmark} className="px-3 py-2 rounded-lg border text-sm flex items-center gap-1"><FiBookmark size={14} /> Bookmark</button>
          <Link to={`/chat/${videoId}`} className="px-3 py-2 rounded-lg bg-primary-100 text-primary-700 text-sm flex items-center gap-1">
            <FiMessageCircle size={14} /> Chatbot
          </Link>
          <Link to={`/mcq/${videoId}`} className="gradient-btn text-sm py-2 px-3 flex items-center gap-1">
            <FiHelpCircle size={14} /> MCQs
          </Link>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex flex-wrap gap-2">
        {TABS.map((tab) => (
          <button key={tab} onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-xl text-sm font-medium transition ${activeTab === tab ? 'bg-primary-600 text-white' : 'bg-slate-100 dark:bg-slate-800'}`}>
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
        <select onChange={(e) => e.target.value && handleTranslate(e.target.value)} className="input-field w-auto text-sm py-2" defaultValue="">
          <option value="">Translate to...</option>
          <option value="hi">Hindi</option>
          <option value="pa">Punjabi</option>
          <option value="en">English</option>
        </select>
        <button onClick={() => speakNotes(getActiveContent())} className="px-3 py-2 rounded-xl bg-slate-100 dark:bg-slate-800">
          <FiVolume2 size={16} />
        </button>
      </div>

      <motion.div className="glass-card p-6" key={activeTab} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        {translating ? <LoadingSpinner text="Translating..." /> : (
          <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">{getActiveContent() || 'No content available'}</pre>
        )}
      </motion.div>
    </div>
  )
}

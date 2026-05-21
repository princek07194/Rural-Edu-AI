import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import toast from 'react-hot-toast'
import { FiDownload, FiCheck, FiX } from 'react-icons/fi'
import { videoAPI, downloadAPI } from '../services/api'
import { downloadBlob } from '../services/api'
import LoadingSpinner from '../components/LoadingSpinner'

export default function MCQPage() {
  const { videoId } = useParams()
  const [mcqs, setMcqs] = useState([])
  const [video, setVideo] = useState(null)
  const [current, setCurrent] = useState(0)
  const [selected, setSelected] = useState(null)
  const [showAnswer, setShowAnswer] = useState(false)
  const [score, setScore] = useState({ correct: 0, attempted: 0 })
  const [quizMode, setQuizMode] = useState(false)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    videoAPI.getContent(videoId)
      .then((res) => {
        setMcqs(res.data.mcqs || [])
        setVideo(res.data.video)
      })
      .finally(() => setLoading(false))
  }, [videoId])

  const mcq = mcqs[current]
  const options = mcq ? [
    { key: 'A', text: mcq.option_a },
    { key: 'B', text: mcq.option_b },
    { key: 'C', text: mcq.option_c },
    { key: 'D', text: mcq.option_d },
  ] : []

  const handleSelect = (key) => {
    if (showAnswer) return
    setSelected(key)
    setShowAnswer(true)
    const correct = key === mcq.correct_answer
    setScore((s) => ({
      correct: s.correct + (correct ? 1 : 0),
      attempted: s.attempted + 1,
    }))
    if (quizMode) {
      videoAPI.updateProgress(videoId, {
        mcqs_attempted: score.attempted + 1,
        mcqs_correct: score.correct + (correct ? 1 : 0),
        quiz_score: ((score.correct + (correct ? 1 : 0)) / (score.attempted + 1)) * 100,
      }).catch(() => {})
    }
  }

  const next = () => {
    setSelected(null)
    setShowAnswer(false)
    setCurrent((c) => Math.min(c + 1, mcqs.length - 1))
  }

  const handleDownload = async () => {
    try {
      const res = await downloadAPI.mcqs(videoId)
      downloadBlob(res.data, `mcqs_${video?.video_id}.pdf`)
      toast.success('MCQ PDF downloaded')
    } catch {
      toast.error('Download failed')
    }
  }

  if (loading) return <LoadingSpinner fullScreen />
  if (!mcqs.length) return <p className="text-center text-slate-500">No MCQs available for this video.</p>

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <motion.div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold">MCQ Quiz</h1>
          <p className="text-slate-500">{video?.title}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setQuizMode(!quizMode)} className={`px-3 py-1.5 rounded-lg text-sm ${quizMode ? 'bg-primary-600 text-white' : 'border'}`}>
            Quiz Mode
          </button>
          <button onClick={handleDownload} className="px-3 py-1.5 rounded-lg border text-sm flex items-center gap-1">
            <FiDownload size={14} /> PDF
          </button>
        </div>
      </motion.div>

      {quizMode && (
        <div className="glass-card p-4 flex justify-between text-sm">
          <span>Score: {score.correct}/{score.attempted}</span>
          <span>Question {current + 1} of {mcqs.length}</span>
        </div>
      )}

      <AnimatePresence mode="wait">
        <motion.div key={current} className="glass-card p-8" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
          <p className="text-lg font-medium mb-6">Q{current + 1}. {mcq.question}</p>
          <div className="space-y-3">
            {options.map(({ key, text }) => {
              let cls = 'w-full text-left p-4 rounded-xl border transition '
              if (showAnswer) {
                if (key === mcq.correct_answer) cls += 'border-green-500 bg-green-50 dark:bg-green-900/20'
                else if (key === selected) cls += 'border-red-500 bg-red-50 dark:bg-red-900/20'
                else cls += 'border-slate-200 dark:border-slate-700 opacity-60'
              } else {
                cls += selected === key ? 'border-primary-500 bg-primary-50' : 'border-slate-200 dark:border-slate-700 hover:border-primary-300'
              }
              return (
                <button key={key} onClick={() => handleSelect(key)} className={cls} disabled={showAnswer}>
                  <span className="font-semibold mr-2">{key}.</span>{text}
                  {showAnswer && key === mcq.correct_answer && <FiCheck className="inline ml-2 text-green-500" />}
                  {showAnswer && key === selected && key !== mcq.correct_answer && <FiX className="inline ml-2 text-red-500" />}
                </button>
              )
            })}
          </div>

          {showAnswer && mcq.explanation && (
            <motion.p className="mt-4 p-4 bg-slate-50 dark:bg-slate-800 rounded-xl text-sm" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <strong>Explanation:</strong> {mcq.explanation}
            </motion.p>
          )}

          <motion.div className="flex justify-between mt-6">
            <button onClick={() => setCurrent((c) => Math.max(0, c - 1))} disabled={current === 0} className="px-4 py-2 rounded-lg border disabled:opacity-40">Previous</button>
            {current < mcqs.length - 1 ? (
              <button onClick={next} className="gradient-btn" disabled={!showAnswer}>Next</button>
            ) : (
              <Link to={`/notes/${videoId}`} className="gradient-btn">View Notes</Link>
            )}
          </motion.div>
        </motion.div>
      </AnimatePresence>

      {/* Question navigator */}
      <div className="flex flex-wrap gap-2 justify-center">
        {mcqs.map((_, i) => (
          <button key={i} onClick={() => { setCurrent(i); setSelected(null); setShowAnswer(false) }}
            className={`w-8 h-8 rounded-lg text-sm ${i === current ? 'bg-primary-600 text-white' : 'bg-slate-100 dark:bg-slate-800'}`}>
            {i + 1}
          </button>
        ))}
      </div>
    </div>
  )
}

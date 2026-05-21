import { useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FiSearch } from 'react-icons/fi'
import { videoAPI } from '../services/api'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    try {
      const res = await videoAPI.search(query)
      setResults(res.data)
    } catch {
      setResults({ videos: [], notes: [], mcqs: [] })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-display font-bold">Search</h1>

      <form onSubmit={handleSearch} className="flex gap-2">
        <div className="relative flex-1">
          <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" />
          <input className="input-field pl-12" placeholder="Search videos, notes, MCQs..." value={query} onChange={(e) => setQuery(e.target.value)} />
        </div>
        <button type="submit" className="gradient-btn" disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </form>

      {results && (
        <motion.div className="space-y-6" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          {results.videos?.length > 0 && (
            <section className="glass-card p-6">
              <h3 className="font-semibold mb-3">Videos ({results.videos.length})</h3>
              <div className="space-y-2">
                {results.videos.map((v) => (
                  <Link key={v.id} to={`/notes/${v.id}`} className="block p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800">
                    {v.title || v.video_id}
                  </Link>
                ))}
              </div>
            </section>
          )}
          {results.notes?.length > 0 && (
            <section className="glass-card p-6">
              <h3 className="font-semibold mb-3">Notes ({results.notes.length})</h3>
              {results.notes.map(({ note, video }, i) => (
                <Link key={i} to={`/notes/${video.id}`} className="block p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 text-sm">
                  <span className="font-medium">{video.title}</span> — {note.note_type}
                  <p className="text-slate-500 truncate">{note.content?.slice(0, 100)}...</p>
                </Link>
              ))}
            </section>
          )}
          {results.mcqs?.length > 0 && (
            <section className="glass-card p-6">
              <h3 className="font-semibold mb-3">MCQs ({results.mcqs.length})</h3>
              {results.mcqs.map(({ mcq, video }, i) => (
                <Link key={i} to={`/mcq/${video.id}`} className="block p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-slate-800 text-sm">
                  {mcq.question}
                </Link>
              ))}
            </section>
          )}
          {!results.videos?.length && !results.notes?.length && !results.mcqs?.length && (
            <p className="text-center text-slate-500">No results found</p>
          )}
        </motion.div>
      )}
    </div>
  )
}

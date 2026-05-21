import { motion } from 'framer-motion'

export default function LoadingSpinner({ fullScreen = false, text = 'Loading...' }) {
  const content = (
    <div className="flex flex-col items-center gap-4">
      <motion.div
        className="w-12 h-12 border-4 border-primary-200 border-t-primary-600 rounded-full"
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
      />
      {text && <p className="text-slate-500 dark:text-slate-400 text-sm">{text}</p>}
    </div>
  )

  if (fullScreen) {
    return (
      <motion.div className="min-h-screen flex items-center justify-center" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        {content}
      </motion.div>
    )
  }
  return <div className="flex justify-center py-12">{content}</div>
}

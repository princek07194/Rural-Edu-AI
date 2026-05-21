import { Routes, Route } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import ProcessVideo from './pages/ProcessVideo'
import NotesViewer from './pages/NotesViewer'
import MCQPage from './pages/MCQPage'
import ChatbotPage from './pages/ChatbotPage'
import Profile from './pages/Profile'
import AdminPanel from './pages/AdminPanel'
import SearchPage from './pages/SearchPage'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/process" element={<ProcessVideo />} />
        <Route path="/notes/:videoId" element={<NotesViewer />} />
        <Route path="/mcq/:videoId" element={<MCQPage />} />
        <Route path="/chat/:videoId" element={<ChatbotPage />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/admin" element={<AdminPanel />} />
      </Route>
    </Routes>
  )
}

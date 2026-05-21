import { useState } from 'react'
import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  FiHome, FiUpload, FiBook, FiMessageCircle, FiUser,
  FiSearch, FiShield, FiMenu, FiX, FiSun, FiMoon, FiLogOut,
} from 'react-icons/fi'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'

const navItems = [
  { to: '/dashboard', icon: FiHome, label: 'Dashboard' },
  { to: '/process', icon: FiUpload, label: 'Process Video' },
  { to: '/search', icon: FiSearch, label: 'Search' },
  { to: '/profile', icon: FiUser, label: 'Profile' },
]

export default function Layout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { user, logout, isAdmin } = useAuth()
  const { dark, toggle } = useTheme()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  const Sidebar = () => (
    <aside className="flex flex-col h-full">
      <motion.div className="p-6 border-b border-slate-200/50 dark:border-slate-700/50" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
        <h1 className="font-display font-bold text-lg bg-gradient-to-r from-primary-600 to-accent-500 bg-clip-text text-transparent">
          Rural Edu AI
        </h1>
        <p className="text-xs text-slate-500 mt-1">Digital Learning Platform</p>
      </motion.div>

      <nav className="flex-1 p-4 space-y-1">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink key={to} to={to} onClick={() => setSidebarOpen(false)}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <Icon size={20} /> {label}
          </NavLink>
        ))}
        {isAdmin && (
          <NavLink to="/admin" onClick={() => setSidebarOpen(false)}
            className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <FiShield size={20} /> Admin Panel
          </NavLink>
        )}
      </nav>

      <div className="p-4 border-t border-slate-200/50 dark:border-slate-700/50 space-y-2">
        <div className="px-4 py-2 text-sm">
          <p className="font-medium truncate">{user?.full_name || user?.username}</p>
          <p className="text-xs text-slate-500 truncate">{user?.email}</p>
        </div>
        <button onClick={toggle} className="sidebar-link w-full">
          {dark ? <FiSun size={20} /> : <FiMoon size={20} />}
          {dark ? 'Light Mode' : 'Dark Mode'}
        </button>
        <button onClick={handleLogout} className="sidebar-link w-full text-red-500 hover:text-red-600">
          <FiLogOut size={20} /> Logout
        </button>
      </div>
    </aside>
  )

  return (
    <div className="min-h-screen flex">
      {/* Desktop sidebar */}
      <div className="hidden lg:flex w-64 glass-card m-4 mr-0 fixed h-[calc(100vh-2rem)] z-30">
        <Sidebar />
      </div>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <>
            <motion.div className="fixed inset-0 bg-black/50 z-40 lg:hidden" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              onClick={() => setSidebarOpen(false)} />
            <motion.div className="fixed left-0 top-0 h-full w-64 glass-card z-50 lg:hidden"
              initial={{ x: -280 }} animate={{ x: 0 }} exit={{ x: -280 }}>
              <button className="absolute top-4 right-4 p-2" onClick={() => setSidebarOpen(false)}>
                <FiX size={24} />
              </button>
              <Sidebar />
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Main content */}
      <main className="flex-1 lg:ml-72 p-4 md:p-6 min-h-screen">
        <button className="lg:hidden mb-4 p-2 glass-card rounded-xl" onClick={() => setSidebarOpen(true)}>
          <FiMenu size={24} />
        </button>
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}

-- Regional Language Based Digital Education System for Rural Communities
-- MySQL Database Schema

CREATE DATABASE IF NOT EXISTS rural_education_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE rural_education_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(80) NOT NULL UNIQUE,
  email VARCHAR(120) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(150),
  preferred_language ENUM('en', 'hi', 'pa', 'bho') DEFAULT 'en',
  role ENUM('user', 'admin') DEFAULT 'user',
  avatar_url VARCHAR(500),
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_users_email (email),
  INDEX idx_users_role (role)
) ENGINE=InnoDB;

-- Videos table
CREATE TABLE IF NOT EXISTS videos (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  youtube_url VARCHAR(500) NOT NULL,
  video_id VARCHAR(20) NOT NULL,
  title VARCHAR(500),
  channel_name VARCHAR(200),
  thumbnail_url VARCHAR(500),
  duration_seconds INT,
  language ENUM('en', 'hi', 'pa', 'bho') DEFAULT 'en',
  status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
  error_message TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_videos_user (user_id),
  INDEX idx_videos_video_id (video_id),
  INDEX idx_videos_status (status)
) ENGINE=InnoDB;

-- Transcripts table
CREATE TABLE IF NOT EXISTS transcripts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  video_id INT NOT NULL UNIQUE,
  content LONGTEXT NOT NULL,
  language VARCHAR(10) DEFAULT 'en',
  word_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Summaries table
CREATE TABLE IF NOT EXISTS summaries (
  id INT AUTO_INCREMENT PRIMARY KEY,
  video_id INT NOT NULL,
  content LONGTEXT NOT NULL,
  language ENUM('en', 'hi', 'pa', 'bho') DEFAULT 'en',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
  INDEX idx_summaries_video (video_id)
) ENGINE=InnoDB;

-- Notes table (detailed, short, keywords, topics)
CREATE TABLE IF NOT EXISTS notes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  video_id INT NOT NULL,
  note_type ENUM('detailed', 'short', 'keywords', 'topics') NOT NULL,
  content LONGTEXT NOT NULL,
  language ENUM('en', 'hi', 'pa', 'bho') DEFAULT 'en',
  is_bookmarked BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
  INDEX idx_notes_video (video_id),
  INDEX idx_notes_type (note_type)
) ENGINE=InnoDB;

-- MCQs table
CREATE TABLE IF NOT EXISTS mcqs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  video_id INT NOT NULL,
  question TEXT NOT NULL,
  option_a VARCHAR(500) NOT NULL,
  option_b VARCHAR(500) NOT NULL,
  option_c VARCHAR(500) NOT NULL,
  option_d VARCHAR(500) NOT NULL,
  correct_answer CHAR(1) NOT NULL,
  explanation TEXT,
  language ENUM('en', 'hi', 'pa', 'bho') DEFAULT 'en',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
  INDEX idx_mcqs_video (video_id)
) ENGINE=InnoDB;

-- Questions table (long/short answer)
CREATE TABLE IF NOT EXISTS questions (
  id INT AUTO_INCREMENT PRIMARY KEY,
  video_id INT NOT NULL,
  question_type ENUM('long', 'short') NOT NULL,
  question TEXT NOT NULL,
  sample_answer TEXT,
  language ENUM('en', 'hi', 'pa', 'bho') DEFAULT 'en',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
  INDEX idx_questions_video (video_id)
) ENGINE=InnoDB;

-- Chatbot history
CREATE TABLE IF NOT EXISTS chatbot_history (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  video_id INT NOT NULL,
  role ENUM('user', 'assistant') NOT NULL,
  message TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
  INDEX idx_chat_user_video (user_id, video_id)
) ENGINE=InnoDB;

-- User progress tracking
CREATE TABLE IF NOT EXISTS user_progress (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  video_id INT NOT NULL,
  notes_read INT DEFAULT 0,
  mcqs_attempted INT DEFAULT 0,
  mcqs_correct INT DEFAULT 0,
  quiz_score FLOAT DEFAULT 0,
  last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
  UNIQUE KEY unique_user_video (user_id, video_id)
) ENGINE=InnoDB;

-- Bookmarks
CREATE TABLE IF NOT EXISTS bookmarks (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  video_id INT NOT NULL,
  note_id INT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  FOREIGN KEY (video_id) REFERENCES videos(id) ON DELETE CASCADE,
  FOREIGN KEY (note_id) REFERENCES notes(id) ON DELETE SET NULL,
  UNIQUE KEY unique_bookmark (user_id, video_id, note_id)
) ENGINE=InnoDB;

-- Notifications
CREATE TABLE IF NOT EXISTS notifications (
  id INT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  title VARCHAR(200) NOT NULL,
  message TEXT NOT NULL,
  is_read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_notifications_user (user_id)
) ENGINE=InnoDB;

-- Admin logs
CREATE TABLE IF NOT EXISTS admin_logs (
  id INT AUTO_INCREMENT PRIMARY KEY,
  admin_id INT NOT NULL,
  action VARCHAR(100) NOT NULL,
  target_type VARCHAR(50),
  target_id INT,
  details TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (admin_id) REFERENCES users(id) ON DELETE CASCADE,
  INDEX idx_admin_logs_admin (admin_id)
) ENGINE=InnoDB;

-- Admin user: run `python backend/scripts/create_admin.py` after setup
-- Default credentials: admin@ruraledu.local / Admin@123

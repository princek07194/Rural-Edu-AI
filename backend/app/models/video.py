"""Video and related content models."""
from datetime import datetime
from app.extensions import db


class Video(db.Model):
    __tablename__ = "videos"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    youtube_url = db.Column(db.String(500), nullable=False)
    video_id = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(500))
    channel_name = db.Column(db.String(200))
    thumbnail_url = db.Column(db.String(500))
    duration_seconds = db.Column(db.Integer)
    language = db.Column(db.String(5), default="en")
    status = db.Column(db.String(20), default="pending")
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    transcript = db.relationship("Transcript", backref="video", uselist=False)
    summaries = db.relationship("Summary", backref="video", lazy="dynamic")
    notes = db.relationship("Note", backref="video", lazy="dynamic")
    mcqs = db.relationship("Mcq", backref="video", lazy="dynamic")
    questions = db.relationship("Question", backref="video", lazy="dynamic")

    def to_dict(self, include_content=False):
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "youtube_url": self.youtube_url,
            "video_id": self.video_id,
            "title": self.title,
            "channel_name": self.channel_name,
            "thumbnail_url": self.thumbnail_url,
            "language": self.language,
            "status": self.status,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_content:
            data["has_transcript"] = self.transcript is not None
            data["summary_count"] = self.summaries.count()
            data["notes_count"] = self.notes.count()
            data["mcqs_count"] = self.mcqs.count()
        return data


class Transcript(db.Model):
    __tablename__ = "transcripts"

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("videos.id"), unique=True)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(10), default="en")
    word_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "content": self.content,
            "language": self.language,
            "word_count": self.word_count,
        }


class Summary(db.Model):
    __tablename__ = "summaries"

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("videos.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(5), default="en")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "content": self.content,
            "language": self.language,
        }


class Note(db.Model):
    __tablename__ = "notes"

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("videos.id"), nullable=False)
    note_type = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    language = db.Column(db.String(5), default="en")
    is_bookmarked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "note_type": self.note_type,
            "content": self.content,
            "language": self.language,
            "is_bookmarked": self.is_bookmarked,
        }


class Mcq(db.Model):
    __tablename__ = "mcqs"

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("videos.id"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    explanation = db.Column(db.Text)
    language = db.Column(db.String(5), default="en")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self, hide_answer=False):
        data = {
            "id": self.id,
            "video_id": self.video_id,
            "question": self.question,
            "option_a": self.option_a,
            "option_b": self.option_b,
            "option_c": self.option_c,
            "option_d": self.option_d,
            "explanation": self.explanation,
            "language": self.language,
        }
        if not hide_answer:
            data["correct_answer"] = self.correct_answer
        return data


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    video_id = db.Column(db.Integer, db.ForeignKey("videos.id"), nullable=False)
    question_type = db.Column(db.String(10), nullable=False)
    question = db.Column(db.Text, nullable=False)
    sample_answer = db.Column(db.Text)
    language = db.Column(db.String(5), default="en")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "question_type": self.question_type,
            "question": self.question,
            "sample_answer": self.sample_answer,
            "language": self.language,
        }

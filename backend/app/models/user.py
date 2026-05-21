"""User model."""
from datetime import datetime
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150))
    preferred_language = db.Column(db.String(5), default="en")
    role = db.Column(db.String(10), default="user")
    avatar_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    videos = db.relationship("Video", backref="owner", lazy="dynamic")
    chat_messages = db.relationship("ChatbotHistory", backref="user", lazy="dynamic")

    def to_dict(self, include_email=True):
        data = {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "preferred_language": self.preferred_language,
            "role": self.role,
            "avatar_url": self.avatar_url,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data["email"] = self.email
        return data

"""Create admin user script. Run: python scripts/create_admin.py"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import User
from app.utils.auth_helpers import hash_password

app = create_app()

with app.app_context():
    email = "admin@ruraledu.local"
    existing = User.query.filter_by(email=email).first()
    if existing:
        existing.password_hash = hash_password("Admin@123")
        existing.role = "admin"
        print("Admin password reset to: Admin@123")
    else:
        admin = User(
            username="admin",
            email=email,
            password_hash=hash_password("Admin@123"),
            full_name="System Administrator",
            role="admin",
            preferred_language="en",
        )
        db.session.add(admin)
        print("Admin created - email: admin@ruraledu.local, password: Admin@123")
    db.session.commit()

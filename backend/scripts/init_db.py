"""Initialize database tables. Run: python scripts/init_db.py"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    db.create_all()
    print("Database tables created successfully.")
    print("DB:", app.config["SQLALCHEMY_DATABASE_URI"])

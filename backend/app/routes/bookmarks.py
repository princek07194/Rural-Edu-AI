"""Bookmark routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import Bookmark, Note, Video
from app.utils.auth_helpers import get_current_user

bookmarks_bp = Blueprint("bookmarks", __name__, url_prefix="/api/bookmarks")


@bookmarks_bp.route("", methods=["GET"])
@jwt_required()
def list_bookmarks():
    user = get_current_user()
    bookmarks = Bookmark.query.filter_by(user_id=user.id).all()
    result = []
    for b in bookmarks:
        video = db.session.get(Video, b.video_id)
        note = db.session.get(Note, b.note_id) if b.note_id else None
        result.append({
            "id": b.id,
            "video": video.to_dict() if video else None,
            "note": note.to_dict() if note else None,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        })
    return jsonify({"bookmarks": result})


@bookmarks_bp.route("", methods=["POST"])
@jwt_required()
def add_bookmark():
    user = get_current_user()
    data = request.get_json() or {}
    video_id = data.get("video_id")
    note_id = data.get("note_id")

    if not video_id:
        return jsonify({"error": "video_id required"}), 400

    existing = Bookmark.query.filter_by(
        user_id=user.id, video_id=video_id, note_id=note_id
    ).first()
    if existing:
        return jsonify({"message": "Already bookmarked", "id": existing.id})

    bookmark = Bookmark(user_id=user.id, video_id=video_id, note_id=note_id)
    if note_id:
        note = db.session.get(Note, note_id)
        if note:
            note.is_bookmarked = True
    db.session.add(bookmark)
    db.session.commit()
    return jsonify({"message": "Bookmarked", "id": bookmark.id}), 201


@bookmarks_bp.route("/<int:bookmark_id>", methods=["DELETE"])
@jwt_required()
def remove_bookmark(bookmark_id):
    user = get_current_user()
    bookmark = Bookmark.query.filter_by(id=bookmark_id, user_id=user.id).first()
    if not bookmark:
        return jsonify({"error": "Not found"}), 404
    if bookmark.note_id:
        note = db.session.get(Note, bookmark.note_id)
        if note:
            note.is_bookmarked = False
    db.session.delete(bookmark)
    db.session.commit()
    return jsonify({"message": "Bookmark removed"})

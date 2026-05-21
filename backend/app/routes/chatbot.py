"""Chatbot routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db, limiter
from app.models import Video, ChatbotHistory, Summary, Transcript
from app.utils.auth_helpers import get_current_user
from app.services.ai_service import chat_with_context

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")


@chatbot_bp.route("/<int:video_id>", methods=["POST"])
@jwt_required()
@limiter.limit("60 per hour")
def chat(video_id):
    user = get_current_user()
    data = request.get_json() or {}
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "Message is required"}), 400

    video = Video.query.filter_by(id=video_id, user_id=user.id).first()
    if not video:
        return jsonify({"error": "Video not found"}), 404
    if video.status != "completed":
        return jsonify({"error": "Video processing not complete"}), 400

    transcript = video.transcript
    summary = Summary.query.filter_by(video_id=video.id).first()
    if not transcript:
        return jsonify({"error": "No transcript available for chat"}), 400

    # Save user message
    db.session.add(
        ChatbotHistory(user_id=user.id, video_id=video.id, role="user", message=message)
    )
    db.session.commit()

    # Get history
    history = (
        ChatbotHistory.query.filter_by(user_id=user.id, video_id=video.id)
        .order_by(ChatbotHistory.created_at.asc())
        .limit(20)
        .all()
    )
    history_data = [{"role": h.role, "message": h.message} for h in history]

    try:
        reply = chat_with_context(
            transcript=transcript.content,
            summary=summary.content if summary else "",
            user_message=message,
            history=history_data,
            language=video.language or user.preferred_language,
        )
    except Exception as e:
        return jsonify({"error": f"AI chat failed: {str(e)}"}), 500

    # Save assistant reply
    db.session.add(
        ChatbotHistory(user_id=user.id, video_id=video.id, role="assistant", message=reply)
    )
    db.session.commit()

    return jsonify({"reply": reply, "video_id": video_id})


@chatbot_bp.route("/<int:video_id>/history", methods=["GET"])
@jwt_required()
def get_history(video_id):
    user = get_current_user()
    video = Video.query.filter_by(id=video_id, user_id=user.id).first()
    if not video:
        return jsonify({"error": "Video not found"}), 404

    history = (
        ChatbotHistory.query.filter_by(user_id=user.id, video_id=video_id)
        .order_by(ChatbotHistory.created_at.asc())
        .all()
    )
    return jsonify({"history": [h.to_dict() for h in history]})


@chatbot_bp.route("/<int:video_id>/history", methods=["DELETE"])
@jwt_required()
def clear_history(video_id):
    user = get_current_user()
    ChatbotHistory.query.filter_by(user_id=user.id, video_id=video_id).delete()
    db.session.commit()
    return jsonify({"message": "Chat history cleared"})

"""Dashboard analytics routes."""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Video, Note, Mcq, Summary, Notification, UserProgress
from app.utils.auth_helpers import get_current_user
from app.services.ai_service import get_recommendations

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/stats", methods=["GET"])
@jwt_required()
def get_stats():
    user = get_current_user()

    total_videos = Video.query.filter_by(user_id=user.id).count()
    completed = Video.query.filter_by(user_id=user.id, status="completed").count()
    total_notes = (
        db.session.query(func.count(Note.id))
        .join(Video, Note.video_id == Video.id)
        .filter(Video.user_id == user.id)
        .scalar()
    )
    total_mcqs = (
        db.session.query(func.count(Mcq.id))
        .join(Video, Mcq.video_id == Video.id)
        .filter(Video.user_id == user.id)
        .scalar()
    )
    total_summaries = (
        db.session.query(func.count(Summary.id))
        .join(Video, Summary.video_id == Video.id)
        .filter(Video.user_id == user.id)
        .scalar()
    )

    # Recent activity (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_videos = (
        Video.query.filter_by(user_id=user.id)
        .filter(Video.created_at >= week_ago)
        .order_by(Video.created_at.desc())
        .limit(5)
        .all()
    )

    # Monthly chart data (videos per month, last 6 months)
    chart_data = []
    for i in range(5, -1, -1):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30 * i)
        month_end = month_start + timedelta(days=30)
        count = Video.query.filter(
            Video.user_id == user.id,
            Video.created_at >= month_start,
            Video.created_at < month_end,
        ).count()
        chart_data.append({
            "month": month_start.strftime("%b"),
            "videos": count,
        })

    # Progress overview
    progress_list = UserProgress.query.filter_by(user_id=user.id).all()

    # Titles for recommendations
    video_titles = [
        v.title for v in Video.query.filter_by(user_id=user.id, status="completed")
        .order_by(Video.created_at.desc()).limit(5).all()
        if v.title
    ]
    recommendations = get_recommendations(video_titles, user.preferred_language)

    return jsonify({
        "stats": {
            "total_videos": total_videos,
            "completed_videos": completed,
            "total_notes": total_notes or 0,
            "total_mcqs": total_mcqs or 0,
            "total_summaries": total_summaries or 0,
            "processing": total_videos - completed,
        },
        "recent_videos": [v.to_dict() for v in recent_videos],
        "chart_data": chart_data,
        "progress": [p.to_dict() for p in progress_list],
        "recommendations": recommendations,
    })


@dashboard_bp.route("/notifications", methods=["GET"])
@jwt_required()
def get_notifications():
    user = get_current_user()
    notifications = (
        Notification.query.filter_by(user_id=user.id)
        .order_by(Notification.created_at.desc())
        .limit(20)
        .all()
    )
    unread = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return jsonify({
        "notifications": [n.to_dict() for n in notifications],
        "unread_count": unread,
    })


@dashboard_bp.route("/notifications/<int:notif_id>/read", methods=["PUT"])
@jwt_required()
def mark_read(notif_id):
    user = get_current_user()
    notif = Notification.query.filter_by(id=notif_id, user_id=user.id).first()
    if notif:
        notif.is_read = True
        db.session.commit()
    return jsonify({"message": "Marked as read"})

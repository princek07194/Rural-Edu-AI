"""Admin panel routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import db
from app.models import User, Video, AdminLog
from app.utils.auth_helpers import get_current_user, admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


def _log_action(admin_id, action, target_type=None, target_id=None, details=None):
    db.session.add(
        AdminLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details,
        )
    )


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required
def list_users():
    page = request.args.get("page", 1, type=int)
    pagination = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return jsonify({
        "users": [u.to_dict() for u in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
    })


@admin_bp.route("/users/<int:user_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_user(user_id):
    admin = get_current_user()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    if user.role == "admin":
        return jsonify({"error": "Cannot delete admin account"}), 403

    _log_action(admin.id, "delete_user", "user", user_id, f"Deleted user {user.username}")
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"})


@admin_bp.route("/users/<int:user_id>/toggle", methods=["PUT"])
@jwt_required()
@admin_required
def toggle_user(user_id):
    admin = get_current_user()
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    user.is_active = not user.is_active
    _log_action(admin.id, "toggle_user", "user", user_id, f"Active: {user.is_active}")
    db.session.commit()
    return jsonify({"message": "User status updated", "is_active": user.is_active})


@admin_bp.route("/videos", methods=["GET"])
@jwt_required()
@admin_required
def all_videos():
    page = request.args.get("page", 1, type=int)
    pagination = (
        Video.query.order_by(Video.created_at.desc())
        .paginate(page=page, per_page=20, error_out=False)
    )
    return jsonify({
        "videos": [v.to_dict(include_content=True) for v in pagination.items],
        "total": pagination.total,
    })


@admin_bp.route("/videos/<int:video_id>", methods=["DELETE"])
@jwt_required()
@admin_required
def delete_video_admin(video_id):
    admin = get_current_user()
    video = db.session.get(Video, video_id)
    if not video:
        return jsonify({"error": "Video not found"}), 404
    _log_action(admin.id, "delete_video", "video", video_id)
    db.session.delete(video)
    db.session.commit()
    return jsonify({"message": "Video deleted"})


@admin_bp.route("/stats", methods=["GET"])
@jwt_required()
@admin_required
def admin_stats():
    return jsonify({
        "total_users": User.query.count(),
        "active_users": User.query.filter_by(is_active=True).count(),
        "total_videos": Video.query.count(),
        "completed_videos": Video.query.filter_by(status="completed").count(),
        "failed_videos": Video.query.filter_by(status="failed").count(),
    })


@admin_bp.route("/logs", methods=["GET"])
@jwt_required()
@admin_required
def admin_logs():
    logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(50).all()
    return jsonify({
        "logs": [
            {
                "id": l.id,
                "admin_id": l.admin_id,
                "action": l.action,
                "target_type": l.target_type,
                "target_id": l.target_id,
                "details": l.details,
                "created_at": l.created_at.isoformat() if l.created_at else None,
            }
            for l in logs
        ]
    })

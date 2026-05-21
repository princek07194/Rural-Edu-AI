"""Video processing and content routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from app.extensions import db, limiter
from app.models import Video, Summary, Note, Mcq, Question, Transcript, UserProgress
from app.utils.validators import extract_youtube_id, validate_language
from app.utils.auth_helpers import get_current_user
from app.services.video_processor import process_video

videos_bp = Blueprint("videos", __name__, url_prefix="/api/videos")


@videos_bp.route("/process", methods=["POST"])
@jwt_required()
@limiter.limit("10 per hour")
def process_youtube_video():
    """Process a YouTube URL - extract transcript and generate AI content."""
    user = get_current_user()
    data = request.get_json() or {}
    url = (data.get("youtube_url") or "").strip()
    language = data.get("language", user.preferred_language or "en")
    manual_transcript = (data.get("manual_transcript") or data.get("transcript_text") or "").strip()

    if not validate_language(language):
        return jsonify({"error": "Unsupported language. Use en, hi, or pa"}), 400

    video_id = extract_youtube_id(url)
    if not video_id:
        return jsonify({"error": "Invalid YouTube URL"}), 400

    # Check duplicate for same user
    existing = Video.query.filter_by(user_id=user.id, video_id=video_id).first()
    if existing and existing.status == "completed":
        transcript = existing.transcript.content if existing.transcript else None
        summary = Summary.query.filter_by(video_id=existing.id).first()
        notes = Note.query.filter_by(video_id=existing.id).all()
        return jsonify({
            "message": "Video already processed",
            "status": existing.status,
            "transcript": transcript,
            "summary": summary.content if summary else None,
            "notes": [n.to_dict() for n in notes],
            "video": existing.to_dict(include_content=True),
        }), 200

    if existing:
        video = existing
        video.status = "pending"
        video.language = language
        video.youtube_url = url
        video.error_message = None
        db.session.commit()
    else:
        video = Video(
            user_id=user.id,
            youtube_url=url,
            video_id=video_id,
            language=language,
            status="pending",
        )
        db.session.add(video)
        db.session.commit()

    try:
        video = process_video(video.id, language, manual_transcript=manual_transcript or None)
        summary = Summary.query.filter_by(video_id=video.id).first()
        notes = Note.query.filter_by(video_id=video.id).all()
        return jsonify({
            "message": "Video processed successfully",
            "status": video.status,
            "transcript": video.transcript.content if video.transcript else None,
            "summary": summary.content if summary else None,
            "notes": [n.to_dict() for n in notes],
            "video": video.to_dict(include_content=True),
        }), 201
    except Exception as e:
        video = db.session.get(Video, video.id)
        return jsonify({
            "error": str(e),
            "video": video.to_dict() if video else None,
        }), 422


@videos_bp.route("", methods=["GET"])
@jwt_required()
def list_videos():
    user = get_current_user()
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 50)
    status = request.args.get("status")

    query = Video.query.filter_by(user_id=user.id)
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Video.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        "videos": [v.to_dict(include_content=True) for v in pagination.items],
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": page,
    })


@videos_bp.route("/<int:video_id>", methods=["GET"])
@jwt_required()
def get_video(video_id):
    user = get_current_user()
    video = Video.query.filter_by(id=video_id, user_id=user.id).first()
    if not video:
        return jsonify({"error": "Video not found"}), 404
    return jsonify({"video": video.to_dict(include_content=True)})


@videos_bp.route("/<int:video_id>/content", methods=["GET"])
@jwt_required()
def get_video_content(video_id):
    user = get_current_user()
    video = Video.query.filter_by(id=video_id, user_id=user.id).first()
    if not video:
        return jsonify({"error": "Video not found"}), 404

    summary = Summary.query.filter_by(video_id=video.id).first()
    notes = Note.query.filter_by(video_id=video.id).all()
    mcqs = Mcq.query.filter_by(video_id=video.id).all()
    questions = Question.query.filter_by(video_id=video.id).all()
    transcript = video.transcript

    return jsonify({
        "video": video.to_dict(),
        "transcript": transcript.to_dict() if transcript else None,
        "summary": summary.to_dict() if summary else None,
        "notes": [n.to_dict() for n in notes],
        "mcqs": [m.to_dict() for m in mcqs],
        "questions": [q.to_dict() for q in questions],
    })


@videos_bp.route("/<int:video_id>", methods=["DELETE"])
@jwt_required()
def delete_video(video_id):
    user = get_current_user()
    video = Video.query.filter_by(id=video_id, user_id=user.id).first()
    if not video:
        return jsonify({"error": "Video not found"}), 404
    db.session.delete(video)
    db.session.commit()
    return jsonify({"message": "Video deleted"})


@videos_bp.route("/search", methods=["GET"])
@jwt_required()
def search_videos():
    user = get_current_user()
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"results": []})

    videos = Video.query.filter(
        Video.user_id == user.id,
        or_(Video.title.ilike(f"%{q}%"), Video.video_id.ilike(f"%{q}%")),
    ).limit(20).all()

    # Search in notes
    note_results = (
        db.session.query(Note, Video)
        .join(Video, Note.video_id == Video.id)
        .filter(Video.user_id == user.id, Note.content.ilike(f"%{q}%"))
        .limit(10)
        .all()
    )

    mcq_results = (
        db.session.query(Mcq, Video)
        .join(Video, Mcq.video_id == Video.id)
        .filter(Video.user_id == user.id, Mcq.question.ilike(f"%{q}%"))
        .limit(10)
        .all()
    )

    return jsonify({
        "videos": [v.to_dict() for v in videos],
        "notes": [
            {"note": n.to_dict(), "video": v.to_dict()}
            for n, v in note_results
        ],
        "mcqs": [
            {"mcq": m.to_dict(hide_answer=True), "video": v.to_dict()}
            for m, v in mcq_results
        ],
    })


@videos_bp.route("/<int:video_id>/progress", methods=["POST"])
@jwt_required()
def update_progress(video_id):
    user = get_current_user()
    data = request.get_json() or {}
    progress = UserProgress.query.filter_by(user_id=user.id, video_id=video_id).first()
    if not progress:
        progress = UserProgress(user_id=user.id, video_id=video_id)
        db.session.add(progress)

    if "notes_read" in data:
        progress.notes_read = data["notes_read"]
    if "mcqs_attempted" in data:
        progress.mcqs_attempted = data["mcqs_attempted"]
    if "mcqs_correct" in data:
        progress.mcqs_correct = data["mcqs_correct"]
    if "quiz_score" in data:
        progress.quiz_score = data["quiz_score"]

    db.session.commit()
    return jsonify({"progress": progress.to_dict()})

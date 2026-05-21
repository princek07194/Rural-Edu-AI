"""Download / PDF export routes."""
from flask import Blueprint, send_file, jsonify
from flask_jwt_extended import jwt_required
import io
from app.models import Video, Summary, Note, Mcq
from app.utils.auth_helpers import get_current_user
from app.services.pdf_service import generate_notes_pdf, generate_mcq_pdf, generate_summary_pdf

download_bp = Blueprint("download", __name__, url_prefix="/api/download")


@download_bp.route("/<int:video_id>/notes", methods=["GET"])
@jwt_required()
def download_notes(video_id):
    user = get_current_user()
    video = Video.query.filter_by(id=video_id, user_id=user.id).first()
    if not video:
        return jsonify({"error": "Video not found"}), 404

    summary = Summary.query.filter_by(video_id=video.id).first()
    notes = {n.note_type: n.content for n in Note.query.filter_by(video_id=video.id).all()}

    pdf_bytes = generate_notes_pdf(
        title=video.title or f"Video {video.video_id}",
        summary=summary.content if summary else "",
        notes=notes,
    )
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"notes_{video.video_id}.pdf",
    )


@download_bp.route("/<int:video_id>/mcqs", methods=["GET"])
@jwt_required()
def download_mcqs(video_id):
    user = get_current_user()
    video = Video.query.filter_by(id=video_id, user_id=user.id).first()
    if not video:
        return jsonify({"error": "Video not found"}), 404

    mcqs = [m.to_dict() for m in Mcq.query.filter_by(video_id=video.id).all()]
    pdf_bytes = generate_mcq_pdf(title=video.title or "MCQs", mcqs=mcqs)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"mcqs_{video.video_id}.pdf",
    )


@download_bp.route("/<int:video_id>/summary", methods=["GET"])
@jwt_required()
def download_summary(video_id):
    user = get_current_user()
    video = Video.query.filter_by(id=video_id, user_id=user.id).first()
    if not video:
        return jsonify({"error": "Video not found"}), 404

    summary = Summary.query.filter_by(video_id=video.id).first()
    pdf_bytes = generate_summary_pdf(
        title=video.title or "Summary",
        summary=summary.content if summary else "No summary available",
    )
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"summary_{video.video_id}.pdf",
    )

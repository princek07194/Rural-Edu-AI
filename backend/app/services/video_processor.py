"""Orchestrates video processing pipeline."""
import logging
from typing import Optional
from app.extensions import db
from app.models import (
    Video,
    Transcript,
    Summary,
    Note,
    Mcq,
    Question,
    Notification,
)
from app.services.youtube_service import (
    fetch_transcript,
    get_video_metadata,
    normalize_manual_transcript,
)
from app.services.ai_service import generate_all_content

logger = logging.getLogger(__name__)


def process_video(
    video_db_id: int,
    language: str = "en",
    manual_transcript: Optional[str] = None,
) -> Video:
    """Full pipeline: transcript -> AI content -> save."""
    video = db.session.get(Video, video_db_id)
    if not video:
        raise ValueError("Video not found")

    video.status = "processing"
    db.session.commit()

    try:
        # Step 1: Fetch or use pasted transcript
        if manual_transcript and manual_transcript.strip():
            transcript_data = normalize_manual_transcript(manual_transcript)
            transcript_data["language"] = language
        else:
            transcript_data = fetch_transcript(video.video_id, language)
        meta = get_video_metadata(video.video_id)

        video.title = meta.get("title", video.title)
        video.thumbnail_url = meta.get("thumbnail_url")
        video.channel_name = meta.get("channel_name")

        # Save or update transcript
        if video.transcript:
            video.transcript.content = transcript_data["content"]
            video.transcript.language = transcript_data["language"]
            video.transcript.word_count = transcript_data["word_count"]
        else:
            t = Transcript(
                video_id=video.id,
                content=transcript_data["content"],
                language=transcript_data["language"],
                word_count=transcript_data["word_count"],
            )
            db.session.add(t)

        db.session.flush()

        # Step 2: AI generation
        content = generate_all_content(transcript_data["content"], language)

        # Clear old generated content on reprocess
        Summary.query.filter_by(video_id=video.id).delete()
        Note.query.filter_by(video_id=video.id).delete()
        Mcq.query.filter_by(video_id=video.id).delete()
        Question.query.filter_by(video_id=video.id).delete()

        # Summary
        db.session.add(
            Summary(video_id=video.id, content=content.get("summary", ""), language=language)
        )

        # Notes
        note_map = {
            "detailed": content.get("detailed_notes", ""),
            "short": content.get("short_notes", ""),
            "keywords": ", ".join(content.get("keywords", [])),
            "topics": _format_topics(content.get("topics", [])),
        }
        for note_type, note_content in note_map.items():
            if note_content:
                db.session.add(
                    Note(
                        video_id=video.id,
                        note_type=note_type,
                        content=note_content,
                        language=language,
                    )
                )

        # MCQs
        for mcq in content.get("mcqs", []):
            db.session.add(
                Mcq(
                    video_id=video.id,
                    question=mcq.get("question", ""),
                    option_a=mcq.get("option_a", ""),
                    option_b=mcq.get("option_b", ""),
                    option_c=mcq.get("option_c", ""),
                    option_d=mcq.get("option_d", ""),
                    correct_answer=mcq.get("correct_answer", "A"),
                    explanation=mcq.get("explanation", ""),
                    language=language,
                )
            )

        # Questions
        for q in content.get("long_questions", []):
            db.session.add(
                Question(
                    video_id=video.id,
                    question_type="long",
                    question=q.get("question", ""),
                    sample_answer=q.get("sample_answer", ""),
                    language=language,
                )
            )
        for q in content.get("short_questions", []):
            db.session.add(
                Question(
                    video_id=video.id,
                    question_type="short",
                    question=q.get("question", ""),
                    sample_answer=q.get("sample_answer", ""),
                    language=language,
                )
            )

        video.status = "completed"
        video.language = language
        video.error_message = None

        # Notification
        db.session.add(
            Notification(
                user_id=video.user_id,
                title="Video Processed Successfully",
                message=f'Your video "{video.title}" has been processed. Notes and MCQs are ready!',
            )
        )

        db.session.commit()
        return video

    except Exception as e:
        logger.exception("Video processing failed: %s", e)
        video.status = "failed"
        err_msg = str(e)
        if "api key" in err_msg.lower() or "API_KEY" in err_msg:
            err_msg = (
                "AI API key invalid. Add GEMINI_API_KEY in backend/.env "
                "(get free key: https://aistudio.google.com/) OR use manual transcript paste."
            )
        video.error_message = err_msg[:500]
        db.session.commit()
        raise ValueError(err_msg) from e


def _format_topics(topics: list) -> str:
    lines = []
    for t in topics:
        if isinstance(t, dict):
            lines.append(f"• {t.get('topic', '')}: {t.get('description', '')}")
        else:
            lines.append(f"• {t}")
    return "\n".join(lines)

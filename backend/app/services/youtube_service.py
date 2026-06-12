"""YouTube transcript extraction — multiple methods + manual fallback."""
import glob
import logging
import os
import re
import shutil
import tempfile
import time
import urllib.request
from typing import Optional

logger = logging.getLogger(__name__)

LANGUAGE_MAP = {
    "en": ["en", "en-US", "en-GB", "a.en"],
    "hi": ["hi", "hi-IN", "a.hi", "en"],
    "pa": ["pa", "pa-IN", "a.pa", "en"],
    "bho": ["hi", "hi-IN", "a.hi", "en"],
}


def get_video_metadata(video_id: str) -> dict:
    """Fetch title/thumbnail via yt-dlp when possible."""
    meta = {
        "video_id": video_id,
        "title": f"YouTube Video {video_id}",
        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
        "channel_name": "YouTube",
    }
    try:
        import yt_dlp

        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}", download=False
            )
        if info.get("title"):
            meta["title"] = info["title"]
        if info.get("uploader"):
            meta["channel_name"] = info["uploader"]
    except Exception as e:
        logger.debug("Metadata fetch skipped: %s", e)
    return meta


def _snippets_to_text(snippets) -> str:
    """Join transcript snippets into plain text."""
    parts = []
    for s in snippets:
        if isinstance(s, dict):
            text = s.get("text", "")
        else:
            text = getattr(s, "text", str(s))
        text = re.sub(r"<[^>]+>", "", text).strip()
        if text:
            parts.append(text)
    return " ".join(parts)


def _parse_vtt(content: str) -> str:
    """Parse WebVTT / SRT subtitle file to plain text."""
    lines = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("WEBVTT") or line.startswith("NOTE"):
            continue
        if re.match(r"^\d+$", line):
            continue
        if re.match(r"\d{2}:\d{2}", line) and "-->" in line:
            continue
        if line.startswith("{"):
            continue
        # Remove VTT tags like <c> or align markers
        line = re.sub(r"<[^>]*>", "", line).strip()
        if line and not line.startswith("align:"):
            lines.append(line)
    # De-duplicate consecutive identical lines (common in auto-captions)
    deduped = []
    for line in lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return " ".join(deduped)


def _fetch_ytt_api_v1(video_id: str, language: str) -> dict:
    """youtube-transcript-api >= 1.0 (instance API)."""
    from youtube_transcript_api import YouTubeTranscriptApi

    langs = LANGUAGE_MAP.get(language, ["en"])
    api = YouTubeTranscriptApi()

    last_error = None
    for attempt in range(2):
        try:
            fetched = api.fetch(video_id, languages=langs)
            text = _snippets_to_text(fetched)
            if not text or len(text) < 20:
                raise ValueError("Transcript too short or empty")
            lang_code = getattr(fetched, "language_code", None) or language
            return {
                "content": text,
                "language": lang_code,
                "word_count": len(text.split()),
            }
        except Exception as e:
            last_error = e
            err_name = type(e).__name__
            if "IpBlocked" in err_name or "RequestBlocked" in err_name:
                raise ValueError(
                    "YouTube blocked automatic transcript download from your network. "
                    "Paste the transcript manually below, or try again after some time."
                ) from e
            if attempt == 0:
                time.sleep(1)
                continue
            raise last_error

    raise last_error or ValueError("Transcript fetch failed")


def _fetch_ytt_api_legacy(video_id: str, language: str) -> dict:
    """youtube-transcript-api 0.6.x fallback."""
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api._errors import (
        TranscriptsDisabled,
        NoTranscriptFound,
        VideoUnavailable,
    )

    langs = LANGUAGE_MAP.get(language, ["en"])
    try:
        entries = YouTubeTranscriptApi.get_transcript(
            video_id, languages=[l.split("-")[0] for l in langs]
        )
        text = _snippets_to_text(entries)
        if len(text) < 20:
            raise ValueError("Transcript too short")
        return {
            "content": text,
            "language": language,
            "word_count": len(text.split()),
        }
    except TranscriptsDisabled:
        raise ValueError(
            "Captions are disabled on this video. Use a video with CC enabled or paste transcript manually."
        )
    except NoTranscriptFound:
        raise ValueError(
            "No captions found. Choose a video with subtitles (CC button on YouTube) or paste transcript manually."
        )
    except VideoUnavailable:
        raise ValueError("Video is private, deleted, or unavailable.")
    except Exception as e:
        raise ValueError(f"Transcript API error: {e}") from e


class SubtitlesUnavailable(ValueError):
    pass


def _get_ytdlp_cookiefile() -> Optional[str]:
    cookiefile = (
        os.getenv("YTDLP_COOKIE_FILE")
        or os.getenv("YTDLP_COOKIEFILE")
        or os.getenv("COOKIES_TXT")
    )
    if not cookiefile:
        return None
    cookiefile = os.path.expanduser(cookiefile)
    if os.path.isfile(cookiefile):
        logger.debug("Using yt-dlp cookies file: %s", cookiefile)
        return cookiefile
    logger.warning("yt-dlp cookie file not found: %s", cookiefile)
    return None


def _parse_ytdlp_subtitles(info: dict, video_id: str, lang_list: list) -> str:
    for pool_name in ("subtitles", "automatic_captions"):
        pool = info.get(pool_name) or {}
        if not pool:
            continue
        logger.debug("Inspecting %s for %s subtitles", pool_name, video_id)
        for code in lang_list:
            base_code = code.split("-")[0]
            candidates = {code, base_code}
            if base_code and not base_code.startswith("a."):
                candidates.add(f"a.{base_code}")

            for key in candidates:
                if key not in pool or not pool[key]:
                    continue
                for entry in pool[key]:
                    sub_url = entry.get("url")
                    if not sub_url:
                        continue
                    logger.info("Fetching %s subtitles for %s from %s", pool_name, video_id, sub_url)
                    raw = urllib.request.urlopen(sub_url, timeout=30).read().decode(
                        "utf-8", errors="ignore"
                    )
                    text = _parse_vtt(raw)
                    if len(text) >= 20:
                        logger.info("Loaded %s subtitles for %s (%s words)", pool_name, video_id, len(text.split()))
                        return text
    raise SubtitlesUnavailable("yt-dlp could not download subtitles for this video")


def _download_audio(video_id: str, cookiefile: Optional[str] = None) -> str:
    import yt_dlp

    tmp = tempfile.mkdtemp()
    url = f"https://www.youtube.com/watch?v={video_id}"
    opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(tmp, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": False,
        "noplaylist": True,
    }

    if cookiefile:
        opts["cookiefile"] = cookiefile

    logger.info("Downloading audio for %s with yt-dlp", video_id)
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    candidates = glob.glob(os.path.join(tmp, f"{video_id}.*"))
    if not candidates:
        raise ValueError("Audio download failed: no audio file was produced")

    audio_path = max(candidates, key=os.path.getsize)
    logger.info("Downloaded audio file for %s: %s", video_id, audio_path)
    return audio_path


def _transcribe_audio_whisper(audio_path: str) -> str:
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OpenAI API key is required for audio transcription fallback. "
            "Set OPENAI_API_KEY in backend/.env."
        )

    logger.info("Transcribing audio with OpenAI Whisper: %s", audio_path)
    client = OpenAI(api_key=api_key)
    with open(audio_path, "rb") as audio_file:
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )

    transcript = getattr(response, "text", None) or response.get("text")
    if not transcript:
        raise ValueError("Whisper transcription returned no text")
    logger.info("Whisper transcription complete (%s words)", len(transcript.split()))
    return transcript


def _transcribe_audio_fallback(video_id: str) -> dict:
    audio_path = None
    cookiefile = _get_ytdlp_cookiefile()
    try:
        audio_path = _download_audio(video_id, cookiefile=cookiefile)
        transcript = _transcribe_audio_whisper(audio_path)
        if len(transcript) < 20:
            raise ValueError("Audio transcription was too short")
        return {
            "content": transcript,
            "language": "auto",
            "word_count": len(transcript.split()),
        }
    finally:
        if audio_path:
            cleanup_dir = os.path.dirname(audio_path)
            logger.debug("Cleaning up audio temp dir: %s", cleanup_dir)
            shutil.rmtree(cleanup_dir, ignore_errors=True)


def _fetch_ytdlp(video_id: str, language: str) -> dict:
    """Download subtitles via yt-dlp."""
    import yt_dlp

    url = f"https://www.youtube.com/watch?v={video_id}"
    lang_list = LANGUAGE_MAP.get(language, ["en"])
    lang_codes = [code.split("-")[0] for code in lang_list]
    cookiefile = _get_ytdlp_cookiefile()

    opts = {
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitleslangs": lang_codes,
        "subtitlesformat": "vtt/best",
        "noplaylist": True,
    }
    if cookiefile:
        opts["cookiefile"] = cookiefile

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        text = _parse_ytdlp_subtitles(info, video_id, lang_list)
        return {
            "content": text,
            "language": language,
            "word_count": len(text.split()),
        }
    except SubtitlesUnavailable:
        logger.warning("No subtitles available for %s, falling back to audio transcription", video_id)
        return _transcribe_audio_fallback(video_id)
    except Exception as e:
        logger.debug("yt-dlp subtitle extraction failed for %s: %s", video_id, e)
        raise ValueError(f"yt-dlp subtitle download error: {e}") from e


def fetch_transcript(video_id: str, language: str = "en") -> dict:
    """
    Fetch transcript using multiple methods.
    Raises ValueError with a helpful message on failure.
    """
    errors = []

    # Method 1: youtube-transcript-api v1.x (instance.fetch)
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        if hasattr(YouTubeTranscriptApi(), "fetch"):
            return _fetch_ytt_api_v1(video_id, language)
    except ValueError as e:
        msg = str(e).lower()
        if "blocked automatic transcript download" in msg or "ipblocked" in msg or "requestblocked" in msg:
            raise
        errors.append(f"transcript-api: {e}")
    except Exception as e:
        errors.append(f"transcript-api: {e}")

    # Method 2: legacy 0.6.x (classmethod get_transcript)
    try:
        from youtube_transcript_api import YouTubeTranscriptApi

        if hasattr(YouTubeTranscriptApi, "get_transcript"):
            return _fetch_ytt_api_legacy(video_id, language)
    except ValueError as e:
        msg = str(e).lower()
        if "blocked automatic transcript download" in msg or "ipblocked" in msg or "requestblocked" in msg:
            raise
        errors.append(f"legacy-api: {e}")
    except Exception as e:
        errors.append(f"legacy-api: {e}")

    # Method 3: yt-dlp subtitle download
    try:
        return _fetch_ytdlp(video_id, language)
    except ValueError:
        raise
    except Exception as e:
        errors.append(f"yt-dlp: {e}")

    logger.error("All transcript methods failed for %s: %s", video_id, errors)
    raise ValueError(
        "Failed to fetch transcript automatically. "
        "Use a video with CC/captions enabled, wait a few minutes if rate-limited, "
        "or paste the transcript manually on the Process Video page."
    )


def normalize_manual_transcript(text: str) -> dict:
    """Validate and normalize user-pasted transcript."""
    text = (text or "").strip()
    if len(text) < 50:
        raise ValueError("Pasted transcript is too short (minimum 50 characters).")
    if len(text) > 500000:
        raise ValueError("Transcript is too long (max 500,000 characters).")
    return {
        "content": text,
        "language": "manual",
        "word_count": len(text.split()),
    }

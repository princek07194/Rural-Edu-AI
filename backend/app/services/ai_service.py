"""AI content generation service (Gemini / OpenAI) with local fallback."""
import json
import logging
import re
from flask import current_app
from app.services.local_ai_service import (
    generate_all_content_local,
    chat_local,
)

logger = logging.getLogger(__name__)

LANGUAGE_NAMES = {"en": "English", "hi": "Hindi", "pa": "Punjabi", "bho": "Bhojpuri"}

PLACEHOLDER_KEYS = {
    "",
    "your_gemini_api_key_here",
    "your_openai_api_key_here",
    "your_key",
    "sk-xxx",
}


def _truncate(text: str, max_chars: int = 28000) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...[truncated]"


def is_cloud_ai_configured() -> bool:
    """Check if a real API key is set (not placeholder)."""
    provider = current_app.config.get("AI_PROVIDER", "gemini").lower()
    if current_app.config.get("USE_LOCAL_AI", "").lower() in ("1", "true", "yes"):
        return False
    if provider == "openai":
        key = (current_app.config.get("OPENAI_API_KEY") or "").strip()
    else:
        key = (current_app.config.get("GEMINI_API_KEY") or "").strip()
    return bool(key) and key.lower() not in PLACEHOLDER_KEYS


def get_ai_mode() -> str:
    return "cloud" if is_cloud_ai_configured() else "local"


def _call_gemini(prompt: str) -> str:
    import google.generativeai as genai

    genai.configure(api_key=current_app.config["GEMINI_API_KEY"])
    model_name = current_app.config.get("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    if not response.text:
        raise ValueError("Empty response from Gemini")
    return response.text


def _call_openai(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=current_app.config["OPENAI_MODEL"],
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.choices[0].message.content


def generate_text(prompt: str) -> str:
    """Route to configured AI provider."""
    if not is_cloud_ai_configured():
        raise ValueError("Cloud AI not configured")
    provider = current_app.config.get("AI_PROVIDER", "gemini").lower()
    if provider == "openai":
        return _call_openai(prompt)
    return _call_gemini(prompt)


def _parse_json_from_response(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError("Could not parse AI response as JSON")


def _normalize_mcqs(data: dict) -> dict:
    for mcq in data.get("mcqs", []):
        ans = str(mcq.get("correct_answer", "A")).upper().strip()
        if ans in ("A", "B", "C", "D"):
            mcq["correct_answer"] = ans
        elif len(ans) >= 1:
            mcq["correct_answer"] = ans[0]
    return data


def _generate_cloud(transcript: str, language: str) -> dict:
    lang_name = LANGUAGE_NAMES.get(language, "English")
    transcript = _truncate(transcript)

    prompt = f"""You are an expert educational content creator for rural students.
Analyze this video transcript and generate comprehensive study material in {lang_name}.

TRANSCRIPT:
{transcript}

Respond with ONLY valid JSON (no markdown) in this exact structure:
{{
  "summary": "comprehensive paragraph summary",
  "detailed_notes": "structured detailed notes with headings and bullet points",
  "short_notes": "concise bullet-point revision notes",
  "keywords": ["keyword1", "keyword2"],
  "topics": [{{"topic": "Topic Name", "description": "brief explanation"}}],
  "mcqs": [
    {{
      "question": "...",
      "option_a": "...",
      "option_b": "...",
      "option_c": "...",
      "option_d": "...",
      "correct_answer": "A",
      "explanation": "..."
    }}
  ],
  "long_questions": [{{"question": "...", "sample_answer": "..."}}],
  "short_questions": [{{"question": "...", "sample_answer": "..."}}]
}}

Generate at least 8 MCQs, 5 long and 5 short questions. Base everything on the transcript.
correct_answer must be A, B, C, or D only.
"""

    raw = generate_text(prompt)
    return _normalize_mcqs(_parse_json_from_response(raw))


def generate_all_content(transcript: str, language: str = "en") -> dict:
    """Generate summary, notes, MCQs — uses cloud AI or local fallback."""
    if is_cloud_ai_configured():
        try:
            return _generate_cloud(transcript, language)
        except Exception as e:
            err = str(e).lower()
            if "api key" in err or "api_key" in err or "invalid" in err:
                logger.warning("Cloud AI failed (API key?), using local fallback: %s", e)
            else:
                logger.warning("Cloud AI failed, using local fallback: %s", e)

    logger.info("Using local AI generator (set GEMINI_API_KEY in .env for Gemini)")
    return generate_all_content_local(transcript, language)


def chat_with_context(
    transcript: str,
    summary: str,
    user_message: str,
    history: list,
    language: str = "en",
) -> str:
    if is_cloud_ai_configured():
        try:
            lang_name = LANGUAGE_NAMES.get(language, "English")
            history_text = ""
            for h in history[-10:]:
                history_text += f"{h.get('role', 'user').upper()}: {h.get('message', '')}\n"

            prompt = f"""You are an educational AI tutor. Answer ONLY from the video content. Respond in {lang_name}.

SUMMARY: {_truncate(summary, 4000)}
TRANSCRIPT: {_truncate(transcript, 8000)}
HISTORY: {history_text}
QUESTION: {user_message}

Provide a clear educational answer:"""
            return generate_text(prompt)
        except Exception as e:
            logger.warning("Chat cloud AI failed, local fallback: %s", e)

    return chat_local(transcript, summary, user_message)


def get_recommendations(processed_videos: list, language: str = "en") -> list:
    defaults = [
        "Review your short notes daily for better retention",
        "Practice MCQs to test your understanding",
        "Use the chatbot to clarify difficult concepts",
    ]
    if not processed_videos:
        return [
            "Start by processing your first educational YouTube video",
            "Enable captions or paste transcript manually if auto-fetch fails",
            "Add GEMINI_API_KEY in backend/.env for smarter AI content",
        ]

    if not is_cloud_ai_configured():
        return defaults + ["Set GEMINI_API_KEY for personalized AI recommendations"]

    topics = ", ".join(processed_videos[:5])
    prompt = f"""Based on topics: {topics}
Suggest 5 study tips in {LANGUAGE_NAMES.get(language, 'English')}.
Return JSON: {{"recommendations": ["tip1", ...]}}"""
    try:
        raw = generate_text(prompt)
        data = _parse_json_from_response(raw)
        return data.get("recommendations", defaults)
    except Exception:
        return defaults

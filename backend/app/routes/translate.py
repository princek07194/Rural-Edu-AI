"""Translation API routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.extensions import limiter
from app.utils.validators import validate_language
from app.services.translation_service import translate_text

translate_bp = Blueprint("translate", __name__, url_prefix="/api/translate")


@translate_bp.route("", methods=["POST"])
@jwt_required()
@limiter.limit("30 per hour")
def translate():
    data = request.get_json() or {}
    text = data.get("text", "")
    target_lang = data.get("target_language", "hi")
    source_lang = data.get("source_language", "auto")

    if not text:
        return jsonify({"error": "Text is required"}), 400
    if not validate_language(target_lang):
        return jsonify({"error": "Unsupported target language"}), 400

    try:
        translated = translate_text(text, target_lang, source_lang)
        return jsonify({"translated_text": translated, "target_language": target_lang})
    except ValueError as e:
        return jsonify({"error": str(e)}), 422

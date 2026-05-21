"""Translation service using deep-translator."""
from deep_translator import GoogleTranslator

LANG_CODES = {"en": "en", "hi": "hi", "pa": "pa", "bho": "bho"}


def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """Translate text to target language."""
    if not text or target_lang == source_lang:
        return text
    target = LANG_CODES.get(target_lang, target_lang)
    source = LANG_CODES.get(source_lang, source_lang) if source_lang != "auto" else "auto"
    try:
        translator = GoogleTranslator(source=source, target=target)
        # Chunk long text
        if len(text) > 4500:
            chunks = [text[i : i + 4500] for i in range(0, len(text), 4500)]
            return "".join(translator.translate(c) for c in chunks)
        return translator.translate(text)
    except Exception as e:
        # If GoogleTranslator doesn't support the requested language code, try using Hindi as fallback for Bhojpuri
        if target == "bho":
            try:
                translator = GoogleTranslator(source=source, target="hi")
                if len(text) > 4500:
                    chunks = [text[i : i + 4500] for i in range(0, len(text), 4500)]
                    return "".join(translator.translate(c) for c in chunks)
                return translator.translate(text)
            except Exception:
                pass
        raise ValueError(f"Translation failed: {str(e)}")

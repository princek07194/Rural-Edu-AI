"""Local content generation when Gemini/OpenAI API is not configured."""
import re
import random
from collections import Counter

STOPWORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "must", "shall", "can", "need", "dare",
    "ought", "used", "to", "of", "in", "for", "on", "with", "at", "by",
    "from", "as", "into", "through", "during", "before", "after", "above",
    "below", "between", "under", "again", "further", "then", "once", "here",
    "there", "when", "where", "why", "how", "all", "each", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "and", "but", "if", "or",
    "because", "until", "while", "this", "that", "these", "those", "it",
    "its", "they", "them", "their", "what", "which", "who", "whom", "you",
    "your", "we", "our", "he", "she", "his", "her", "about", "also", "up",
}


def _sentences(text: str) -> list:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text.strip())
    return [s.strip() for s in parts if len(s.strip()) > 25]


def _keywords(text: str, n: int = 15) -> list:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    filtered = [w for w in words if w not in STOPWORDS]
    return [w.title() for w, _ in Counter(filtered).most_common(n)]


def _chunk_notes(sentences: list) -> str:
    lines = ["## Key Points from Video\n"]
    for i, s in enumerate(sentences[:25], 1):
        lines.append(f"{i}. {s}")
    if len(sentences) > 25:
        lines.append(f"\n... and {len(sentences) - 25} more points in the full transcript.")
    return "\n".join(lines)


def _short_notes(sentences: list) -> str:
    lines = ["## Quick Revision Notes\n"]
    for s in sentences[:12]:
        short = s[:120] + ("..." if len(s) > 120 else "")
        lines.append(f"• {short}")
    return "\n".join(lines)


def _topics_from_sentences(sentences: list) -> list:
    topics = []
    chunk = 4
    for i in range(0, min(len(sentences), 20), chunk):
        group = sentences[i : i + chunk]
        title = group[0][:60].split(",")[0].strip()
        if len(title) < 10:
            title = f"Topic {i // chunk + 1}"
        topics.append({
            "topic": title[:80],
            "description": " ".join(group[:2])[:200],
        })
    return topics[:5] if topics else [{"topic": "Main Content", "description": sentences[0][:200] if sentences else ""}]


def _make_mcqs(sentences: list, keywords: list) -> list:
    mcqs = []
    pool = [s for s in sentences if 40 < len(s) < 200]
    if not pool:
        pool = sentences[:10]
    random.shuffle(pool)

    for i, sent in enumerate(pool[:10]):
        # Fill-in style MCQ from sentence
        words = sent.split()
        if len(words) < 6:
            continue
        blank_idx = len(words) // 2
        answer_word = words[blank_idx].strip(".,!?")
        if len(answer_word) < 3:
            continue
        question_sent = " ".join(words[:blank_idx]) + " ______ " + " ".join(words[blank_idx + 1 :])
        question = f"Complete the statement: {question_sent}?"

        distractors = [w for w in keywords if w.lower() != answer_word.lower()][:3]
        while len(distractors) < 3:
            distractors.append(f"Option{len(distractors)+1}")

        options = [answer_word.title()] + distractors[:3]
        random.shuffle(options)
        correct_letter = "ABCD"[options.index(answer_word.title())] if answer_word.title() in options else "A"

        mcqs.append({
            "question": question[:300],
            "option_a": str(options[0])[:100],
            "option_b": str(options[1])[:100],
            "option_c": str(options[2])[:100],
            "option_d": str(options[3])[:100],
            "correct_answer": correct_letter,
            "explanation": f"The correct answer is based on: {sent[:150]}...",
        })

    # Concept MCQs from sentences
    for sent in sentences[:5]:
        if len(mcqs) >= 12:
            break
        mcqs.append({
            "question": f"Which statement is true according to the lesson?\n\"{sent[:150]}...\"",
            "option_a": "Yes, this is discussed in the video",
            "option_b": "No, this is not mentioned",
            "option_c": "Only partially correct",
            "option_d": "Cannot be determined",
            "correct_answer": "A",
            "explanation": "This point is directly covered in the video transcript.",
        })

    return mcqs[:12] if mcqs else [{
        "question": "What is the main topic of this video?",
        "option_a": sentences[0][:80] if sentences else "Educational content",
        "option_b": "Unrelated topic",
        "option_c": "No specific topic",
        "option_d": "Entertainment only",
        "correct_answer": "A",
        "explanation": "Based on the transcript content.",
    }]


def _make_questions(sentences: list, qtype: str) -> list:
    qs = []
    for s in sentences[:8 if qtype == "long" else 6]:
        qs.append({
            "question": f"Explain: {s[:200]}?",
            "sample_answer": s,
        })
    return qs


def generate_all_content_local(transcript: str, language: str = "en") -> dict:
    """Generate study material without external AI API."""
    sentences = _sentences(transcript)
    if not sentences:
        sentences = [transcript[:500]]

    kw = _keywords(transcript)
    summary_sents = sentences[:3] + (sentences[len(sentences) // 2 : len(sentences) // 2 + 2] if len(sentences) > 5 else [])
    summary = " ".join(summary_sents)
    if len(summary) < 100:
        summary = transcript[:800]

    lang_note = ""
    if language == "hi":
        lang_note = "\n\n(नोट: बेहतर हिंदी सामग्री के लिए backend/.env में GEMINI_API_KEY सेट करें)"
    elif language == "pa":
        lang_note = "\n\n(ਨੋਟ: ਬਿਹਤਰ ਪੰਜਾਬੀ ਸਮੱਗਰੀ ਲਈ GEMINI_API_KEY ਸੈੱਟ ਕਰੋ)"

    return {
        "summary": summary + lang_note,
        "detailed_notes": _chunk_notes(sentences),
        "short_notes": _short_notes(sentences),
        "keywords": kw,
        "topics": _topics_from_sentences(sentences),
        "mcqs": _make_mcqs(sentences, kw),
        "long_questions": _make_questions(sentences, "long"),
        "short_questions": _make_questions(sentences[:10], "short"),
    }


def chat_local(transcript: str, summary: str, user_message: str) -> str:
    """Simple keyword-based chatbot without API."""
    msg = user_message.lower()
    sentences = _sentences(transcript)

    if any(w in msg for w in ("summary", "summarize", "overview", "main topic")):
        return f"**Summary:**\n{summary[:1500]}"

    # Find most relevant sentence
    words = [w for w in re.findall(r"\w+", msg) if len(w) > 3 and w not in STOPWORDS]
    best, score = "", 0
    for s in sentences:
        s_lower = s.lower()
        sc = sum(1 for w in words if w in s_lower)
        if sc > score:
            score, best = sc, s

    if best and score > 0:
        return (
            f"Based on the video content:\n\n{best}\n\n"
            "For more detail, check the Notes and Summary sections."
        )

    return (
        "I can answer questions about this video's content. Try asking about:\n"
        "• Main topics covered\n"
        "• Specific concepts from the lesson\n"
        "• A summary of the video\n\n"
        f"Example from transcript: \"{sentences[0][:200]}...\""
        if sentences
        else "Please read the generated notes for this video."
    )

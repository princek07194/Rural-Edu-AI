"""PDF generation service."""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER


def _escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def generate_notes_pdf(title: str, summary: str, notes: dict) -> bytes:
    """Generate PDF for notes and summary."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Heading1"],
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20,
    )
    story = [
        Paragraph(_escape(title), title_style),
        Spacer(1, 12),
        Paragraph("<b>Summary</b>", styles["Heading2"]),
        Paragraph(_escape(summary or "N/A"), styles["Normal"]),
        Spacer(1, 12),
    ]

    for note_type, content in notes.items():
        if content:
            story.append(Paragraph(f"<b>{note_type.replace('_', ' ').title()}</b>", styles["Heading2"]))
            for para in str(content).split("\n"):
                if para.strip():
                    story.append(Paragraph(_escape(para), styles["Normal"]))
            story.append(Spacer(1, 8))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_mcq_pdf(title: str, mcqs: list) -> bytes:
    """Generate PDF for MCQs."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(_escape(title), styles["Heading1"]),
        Spacer(1, 16),
    ]

    for i, mcq in enumerate(mcqs, 1):
        story.append(Paragraph(f"<b>Q{i}. {_escape(mcq.get('question', ''))}</b>", styles["Normal"]))
        for opt in ("a", "b", "c", "d"):
            key = f"option_{opt}"
            story.append(Paragraph(f"   {opt.upper()}) {_escape(mcq.get(key, ''))}", styles["Normal"]))
        story.append(
            Paragraph(
                f"<i>Answer: {mcq.get('correct_answer', '')} | {_escape(mcq.get('explanation', ''))}</i>",
                styles["Normal"],
            )
        )
        story.append(Spacer(1, 12))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_summary_pdf(title: str, summary: str) -> bytes:
    """Generate PDF for summary only."""
    return generate_notes_pdf(title, summary, {})

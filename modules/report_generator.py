"""
report_generator.py - create Markdown and PDF reports for download
"""
from typing import Dict, Any
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter

def generate_markdown_report(resume_text: str, domain: str, weights: Dict[str, float], result: Dict[str, Any], overall_score: float, tier: str) -> str:
    """
    Return a Markdown string summarizing the evaluation.
    """
    lines = []
    lines.append(f"# AI Resume Assistant Report")
    lines.append(f"**Domain:** {domain}")
    lines.append(f"**Overall Score:** {overall_score:.1f}/100  —  **{tier}**")
    lines.append("## Weights")
    for k, v in weights.items():
        lines.append(f"- {k}: {v}%")
    lines.append("## Scores & Suggestions")
    for k, v in result.get("scores", {}).items():
        lines.append(f"### {k} — {v}/100")
        lines.append(result.get("justifications", {}).get(k, ""))
        lines.append(f"- Tip: {result.get('tips', {}).get(k, '')}")
    lines.append("## Top missing keywords")
    lines.append(", ".join(result.get("missing_keywords", [])))
    lines.append("## Summary")
    lines.append(result.get("summary", ""))
    lines.append("## Original Resume (excerpt)")
    lines.append(resume_text[:2000])
    return "\n\n".join(lines)

def generate_pdf_report(markdown_text: str) -> bytes:
    """
    Convert a very simple markdown to PDF using reportlab.
    For robust rendering consider using markdown->html->pdf engines.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    flow = []
    for line in markdown_text.splitlines():
        if line.startswith("# "):
            flow.append(Paragraph(line[2:].strip(), styles["Title"]))
        elif line.startswith("## "):
            flow.append(Paragraph(line[3:].strip(), styles["Heading2"]))
        elif line.startswith("### "):
            flow.append(Paragraph(line[4:].strip(), styles["Heading3"]))
        else:
            flow.append(Paragraph(line.replace("_", "\\_").strip(), styles["BodyText"]))
        flow.append(Spacer(1, 6))
    doc.build(flow)
    buffer.seek(0)
    return buffer.read()
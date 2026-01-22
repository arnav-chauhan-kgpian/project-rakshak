import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle


def load_markdown_text(path: str) -> str:
    """Load the markdown report as plain text."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def markdown_to_paragraphs(text: str):
    """
    Very lightweight markdown-to-Paragraph conversion:
    - Lines starting with '## ' become section headings.
    - Other lines are treated as body text.
    - Blank lines create vertical spacing.
    """
    styles = getSampleStyleSheet()

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceAfter=8,
    )

    elements = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            elements.append(Spacer(1, 0.4 * cm))
            continue

        if line.startswith("## "):
            title = line[3:]
            elements.append(Paragraph(title, heading_style))
            elements.append(Spacer(1, 0.2 * cm))
        else:
            # Escape simple markdown bullets for nicer display
            if line.lstrip().startswith("- "):
                line = "• " + line.lstrip()[2:]
            elements.append(Paragraph(line, body_style))
    return elements


def build_pdf(
    input_md: str = "reports/disaster_mas_research_report.md",
    output_pdf: str = "reports/disaster_mas_research_report.pdf",
):
    if not os.path.exists(input_md):
        raise FileNotFoundError(f"Markdown report not found at: {input_md}")

    os.makedirs(os.path.dirname(output_pdf), exist_ok=True)

    text = load_markdown_text(input_md)
    elements = markdown_to_paragraphs(text)

    doc = SimpleDocTemplate(
        output_pdf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Multi-Agent Disaster Damage Assessment Report",
        author="Disaster Convolve System",
    )

    doc.build(elements)
    print(f"PDF generated at: {output_pdf}")


if __name__ == "__main__":
    build_pdf()



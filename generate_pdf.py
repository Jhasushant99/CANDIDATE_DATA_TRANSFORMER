import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def build_pdf(filename="Sushant_Shekhar_sushantshekhar@gmail.com_Eightfold.pdf"):
    """
    Renders the technical design document for the Multi-Source Candidate Data Transformer
    as a clean, modern, and compact single-page PDF using ReportLab flowables.
    """
    # 1. Initialize SimpleDocTemplate with compact margins (0.35 inches)
    # This maximizes the printable canvas area to guarantee a strict single-page limit.
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=25,
        rightMargin=25,
        topMargin=25,
        bottomMargin=25
    )
    
    # Get standard style dictionary
    styles = getSampleStyleSheet()
    
    # 2. Define custom styling rules for elements (Title, Section Titles, Table Headers, Body Text)
    # Font sizes and leading values are strictly proportioned to avoid text overflows.
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#0F172A'),
        alignment=0, # Left aligned
        spaceAfter=2
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=10
    )
    
    section_title_style = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#1E3A8A'),
        spaceBefore=5,
        spaceAfter=3
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#334155')
    )
    
    body_bold_style = ParagraphStyle(
        'DocBodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.white
    )
    
    story = []
    
    # 3. HEADER SECTION (Document Title & Candidate Metadata)
    story.append(Paragraph("TECHNICAL DESIGN: MULTI-SOURCE CANDIDATE DATA TRANSFORMER", title_style))
    story.append(Paragraph("<b>Candidate:</b> Sushant Shekhar | <b>Email:</b> sushantshekhar@gmail.com | <b>Role:</b> Engineering Intern Assignment (Jul-Dec 2026)", meta_style))
    
    # 4. SECTION 1: PIPELINE FLOW DIAGRAM (Implemented as a horizontal flow table)
    story.append(Paragraph("1. PIPELINE ARCHITECTURE & DATA FLOW", section_title_style))
    flow_data = [
        [
            Paragraph("<b>Ingestion</b><br/>Read CSV, JSON, TXT, PDF from CLI inputs.", body_style),
            Paragraph("<b>Parsing</b><br/>Extract candidate info using rules/regex.", body_style),
            Paragraph("<b>Normalization</b><br/>Format phones (E.164), dates (YYYY-MM), countries.", body_style),
            Paragraph("<b>Merging</b><br/>Deduplicate via keys & trust hierarchies.", body_style),
            Paragraph("<b>Projection</b><br/>Reshape profile using custom runtime config.", body_style),
            Paragraph("<b>Validation</b><br/>Validate fields & output final JSON.", body_style)
        ]
    ]
    flow_table = Table(flow_data, colWidths=[93]*6)
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 4))
    
    # 5. SECTION 2: CANONICAL SCHEMA & NORMALIZATION STANDARDS TABLE
    story.append(Paragraph("2. CANONICAL SCHEMA & NORMALIZATION STANDARDS", section_title_style))
    schema_data = [
        [Paragraph("Field", table_header_style), Paragraph("Type / Target Format", table_header_style), Paragraph("Normalization Rules", table_header_style), Paragraph("Example Raw -> Target", table_header_style)],
        [Paragraph("candidate_id", body_style), Paragraph("string (UUID v5)", body_style), Paragraph("Deterministic namespace UUID generated from primary email.", body_style), Paragraph("john@doe.com -> fd8b0826-...", body_style)],
        [Paragraph("full_name", body_style), Paragraph("string", body_style), Paragraph("Title-cased name, punctuation stripped.", body_style), Paragraph("john d. -> John D.", body_style)],
        [Paragraph("emails / phones", body_style), Paragraph("string[]", body_style), Paragraph("Emails lowercase. Phones converted to E.164 standard.", body_style), Paragraph("+1 (555) 019-9234 -> +15550199234", body_style)],
        [Paragraph("location", body_style), Paragraph("{ city, region, country }", body_style), Paragraph("Country standardized to ISO-3166 alpha-2.", body_style), Paragraph("United States -> US", body_style)],
        [Paragraph("skills", body_style), Paragraph("[{ name, confidence, sources }]", body_style), Paragraph("Mapped to standard skill names list. Confidence assigned.", body_style), Paragraph("reactjs -> React (Conf: 1.0)", body_style)],
        [Paragraph("experience", body_style), Paragraph("[{ company, title, start, end }]", body_style), Paragraph("Merged history; dates normalized to YYYY-MM.", body_style), Paragraph("Jan 2020 -> 2020-01", body_style)]
    ]
    schema_table = Table(schema_data, colWidths=[70, 110, 200, 180])
    schema_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E3A8A')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(schema_table)
    story.append(Spacer(1, 4))
    
    # 6. SECTION 3: MERGING RULES & TRUST SCORING METHODOLOGY
    story.append(Paragraph("3. MERGE POLICY & CONFIDENCE SCORING METHODOLOGY", section_title_style))
    
    merge_intro = Paragraph(
        "<b>Match Rules:</b> Profiles are linked if they share a normalized email or phone. Name-only matches are resolved using a token set similarity score.<br/>"
        "<b>Trust Hierarchy:</b> ATS JSON (1.0) &gt; Recruiter CSV (0.9) &gt; Unstructured Resume (0.8) &gt; Recruiter Notes (0.6). Merged fields (e.g. name, location, job title) are selected from the most trusted source.",
        body_style
    )
    story.append(merge_intro)
    story.append(Spacer(1, 3))
    
    # Trust Score Formula Highlight Box
    formula_data = [
        [
            Paragraph("<b>Overall Confidence Formula:</b>", body_bold_style),
            Paragraph("<i>Confidence Score = (Primary Source Trust * 0.5) + (Profile Completeness * 0.3) + (Multi-Source Agreement Bonus * 0.2)</i>", body_style),
            Paragraph("<b>Agreement Bonus:</b> +10% per extra agreeing source (max 20%).<br/><b>Completeness Ratio:</b> Fraction of core fields present.", body_style)
        ]
    ]
    formula_table = Table(formula_data, colWidths=[120, 260, 180])
    formula_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EFF6FF')),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#BFDBFE')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(formula_table)
    story.append(Spacer(1, 4))
    
    # 7. SECTION 4: CONFIGURATION OPTIONS & EDGE CASES RESOLUTION (Side-by-side Table)
    story.append(Paragraph("4. CONFIGURABLE PROJECTION & EDGE CASES HANDLED", section_title_style))
    
    # Left column: projection, Right column: edge cases
    col_data = [
        [
            Paragraph(
                "<b>Runtime Configurable Projection Engine:</b><br/>"
                "• <b>Field Selection & Remapping:</b> Reshapes canonical profile schema. Extracts path values like <code>emails[0]</code>, <code>skills[].name</code>.<br/>"
                "• <b>Per-field Normalization:</b> Allows overrides (e.g. E164 phone formatting or skill canonicalization).<br/>"
                "• <b>Missing Values Strategy:</b> Evaluates global policy rules (<code>null</code>, <code>omit</code>, <code>error</code>) for absent fields.<br/>"
                "• <b>Provenance Control:</b> Toggle switch to include/exclude metadata tracking and source trust confidence scores.",
                body_style
            ),
            Paragraph(
                "<b>Edge Case Handling & Mitigations:</b><br/>"
                "• <b>Name-only Matches:</b> Compares name tokens when email/phone are absent, preventing duplicates for matching candidates.<br/>"
                "• <b>Experience Overlaps:</b> Deduplicates overlapping jobs (company + dates), merging details based on trust scores.<br/>"
                "• <b>Garbage Inputs:</b> Parser errors degrade gracefully instead of crashing; values resolve to null, never invented.<br/>"
                "• <b>Required Field Failures:</b> Throws clear validation errors if a required field is missing under <code>on_missing: 'error'</code>.<br/>"
                "• <b>Descoped:</b> NLP name/entity models and skill taxonomy auto-updates (handled deterministically under time pressure).",
                body_style
            )
        ]
    ]
    col_table = Table(col_data, colWidths=[275, 275])
    col_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('BACKGROUND', (0,0), (0,0), colors.HexColor('#FFFFFF')),
        ('BACKGROUND', (1,0), (1,0), colors.HexColor('#FFFFFF')),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(col_table)
    
    # 8. Build and write the single page PDF document
    doc.build(story)
    print(f"Successfully generated {filename}", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        build_pdf(sys.argv[1])
    else:
        build_pdf()

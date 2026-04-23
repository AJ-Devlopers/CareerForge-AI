# app/routers/module3.py

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import os, json, re
from groq import Groq
from dotenv import load_dotenv
from io import BytesIO

load_dotenv()
router    = APIRouter()
templates = Jinja2Templates(directory="app/templates")
client    = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── PAGE ─────────────────────────────────────────────────────
@router.get("/module3", response_class=HTMLResponse)
def module3_page(request: Request):
    from app.routers.module1 import report_store

    session_id        = request.session.get("session_id")
    stored            = report_store.get(session_id, {})
    interview_results = request.session.get("interview_results", [])

    candidate_name = stored.get("name", "")
    ats_score      = stored.get("ats_score", 0)
    skills_found   = stored.get("skills_found", [])
    roles          = stored.get("roles", [])
    improvements   = stored.get("improvements", [])
    breakdown      = stored.get("breakdown", {})

    default_role = ""
    if roles:
        default_role = roles[0].get("role", "")
    elif interview_results:
        default_role = interview_results[0].get("role", "")

    valid_scores = [r.get("score", 0) for r in interview_results if r.get("score", 0) > 0]
    overall_interview_score = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0

    return templates.TemplateResponse(
        request=request,
        name="module3.html",
        context={
            "request":                 request,
            "candidate_name":          candidate_name,
            "ats_score":               ats_score,
            "skills_found":            skills_found,
            "roles":                   roles[:5],
            "interview_results":       interview_results,
            "overall_interview_score": overall_interview_score,
            "improvements":            improvements,
            "breakdown":               breakdown,
            "default_role":            default_role,
        }
    )


# ── GENERATE ROADMAP (uses agent pipeline) ───────────────────
@router.post("/module3/generate-roadmap")
async def generate_roadmap(request: Request):
    from app.routers.module1 import report_store
    from app.modules.module3_agents.agent_graph import run_module3_pipeline

    data       = await request.json()
    role       = data.get("role", "Software Engineer")
    duration   = data.get("duration", "3 months")
    goal       = data.get("goal", "Get hired")

    session_id        = request.session.get("session_id")
    stored            = report_store.get(session_id, {})
    skills_found      = stored.get("skills_found", [])
    improvements      = stored.get("improvements", [])
    breakdown         = stored.get("breakdown", {})
    resume_text       = stored.get("resume_text", "")
    candidate_name    = stored.get("name", "")
    ats_score         = stored.get("ats_score", 0)
    interview_results = request.session.get("interview_results", [])

    try:
        result = await run_module3_pipeline(
            role=role,
            duration=duration,
            goal=goal,
            candidate_name=candidate_name,
            ats_score=ats_score,
            skills_found=skills_found,
            interview_results=interview_results,
            improvements=improvements,
            breakdown=breakdown,
            resume_text=resume_text,
        )

        # Compute overall interview score
        valid_scores = [r.get("score", 0) for r in interview_results if r.get("score", 0) > 0]
        overall = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0

        return JSONResponse({
            "role":                   role,
            "duration":               duration,
            "goal":                   goal,
            "total_weeks":            result.get("total_weeks", 0),
            "phases":                 result.get("roadmap_phases", []),
            "suggestions":            result.get("suggestions", []),
            "project_ideas":          result.get("project_ideas", []),
            "overall_tips":           result.get("overall_tips", []),
            "interview_analysis":     result.get("interview_analysis", {}),
            "profile_summary":        result.get("profile_summary", ""),
            "combined_score":         result.get("combined_score", 0),
            "grade":                  result.get("grade", ""),
            "weak_areas":             result.get("weak_areas", []),
            "strong_areas":           result.get("strong_areas", []),
            "overall_interview_score": overall,
            "errors":                 result.get("errors", []),
        })

    except Exception as e:
        print(f"❌ module3 pipeline error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ── DOWNLOAD PDF ─────────────────────────────────────────────
@router.post("/module3/download-pdf")
async def download_pdf(request: Request):
    from app.routers.module1 import report_store

    data              = await request.json()
    roadmap_data      = data.get("roadmap", {})
    session_id        = request.session.get("session_id")
    stored            = report_store.get(session_id, {})
    interview_results = request.session.get("interview_results", [])

    candidate_name = stored.get("name", "Candidate")
    ats_score      = stored.get("ats_score", 0)
    skills_found   = stored.get("skills_found", [])

    pdf_bytes = _generate_pdf(
        candidate_name=candidate_name,
        ats_score=ats_score,
        skills_found=skills_found,
        interview_results=interview_results,
        roadmap_data=roadmap_data,
    )

    safe_name = (candidate_name or "career").replace(" ", "_").lower()
    filename  = f"careerforge_{safe_name}_report.pdf"

    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ══════════════════════════════════════════════════════════════
# PDF GENERATOR — Beautiful dark-themed CareerForge style
# ══════════════════════════════════════════════════════════════
def _generate_pdf(candidate_name, ats_score, skills_found,
                  interview_results, roadmap_data):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable,
                                     KeepTogether, PageBreak)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String
    from reportlab.graphics import renderPDF

    # ── Colors ────────────────────────────────────────────────
    C_BG      = colors.HexColor('#0c0c0c')
    C_SURFACE = colors.HexColor('#161616')
    C_CARD    = colors.HexColor('#1e1e1e')
    C_BORDER  = colors.HexColor('#2a2a2a')
    C_ACCENT  = colors.HexColor('#e8d5a3')
    C_ACCENT2 = colors.HexColor('#c9a96e')
    C_WHITE   = colors.HexColor('#f0ede8')
    C_MUTED   = colors.HexColor('#707070')
    C_GREEN   = colors.HexColor('#4ade80')
    C_AMBER   = colors.HexColor('#fbbf24')
    C_RED     = colors.HexColor('#f87171')
    C_BLUE    = colors.HexColor('#60a5fa')
    C_PURPLE  = colors.HexColor('#a78bfa')

    W, H = A4
    buffer = BytesIO()

    # ── Helper styles ─────────────────────────────────────────
    def ps(name, size, color, bold=False, align=TA_LEFT,
           space_before=0, space_after=4, leading=None, tracking=0):
        fn = 'Helvetica-Bold' if bold else 'Helvetica'
        return ParagraphStyle(
            name, fontName=fn, fontSize=size, textColor=color,
            alignment=align, spaceBefore=space_before,
            spaceAfter=space_after,
            leading=leading or max(size + 4, size * 1.35),
        )

    TITLE   = ps('T',  26, C_ACCENT,  bold=True,  align=TA_CENTER, space_after=2)
    SUBTITLE= ps('ST', 9,  C_MUTED,               align=TA_CENTER, space_after=2)
    SEC_HDR = ps('SH', 7,  C_MUTED,               space_before=14, space_after=6)
    BODY    = ps('B',  9,  C_WHITE,               space_after=4,   leading=14)
    SMALL   = ps('S',  8,  C_MUTED,               space_after=3,   leading=12)
    PHASE_T = ps('PH', 11, C_ACCENT,  bold=True,  space_before=10, space_after=3)
    STEP_T  = ps('ST2',9,  C_WHITE,   bold=True,  space_after=2)
    BULLET  = ps('BU', 8,  C_WHITE,               leading=13, space_after=2)
    TIP_T   = ps('TT', 8,  C_ACCENT,  bold=True,  space_after=2)
    GREEN_T = ps('GT', 8,  C_GREEN,               leading=12)
    MUTED_T = ps('MT', 8,  C_MUTED,               leading=12)
    FOOTER  = ps('FT', 7,  C_MUTED,               align=TA_CENTER)

    # ── Table style helper ────────────────────────────────────
    def dark_table(data, col_widths, header_bg=C_SURFACE, row_bg=colors.HexColor('#111111')):
        tbl = Table(data, colWidths=col_widths)
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), header_bg),
            ('BACKGROUND', (0, 1), (-1, -1), row_bg),
            ('TEXTCOLOR',  (0, 0), (-1, -1), C_WHITE),
            ('FONTNAME',   (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, 0),  7),
            ('FONTNAME',   (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',   (0, 1), (-1, -1), 8),
            ('BOX',        (0, 0), (-1, -1), 0.5, C_BORDER),
            ('INNERGRID',  (0, 0), (-1, -1), 0.3, C_BORDER),
            ('TOPPADDING', (0, 0), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ]
        tbl.setStyle(TableStyle(style))
        return tbl

    def score_color(s):
        if s >= 75: return C_GREEN
        if s >= 50: return C_AMBER
        return C_RED

    # ── Build story ───────────────────────────────────────────
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=16*mm, bottomMargin=16*mm,
        title=f"CareerForge Report — {candidate_name}",
        author="CareerForge AI",
    )

    story = []
    role     = roadmap_data.get("role", "—")
    duration = roadmap_data.get("duration", "")
    goal     = roadmap_data.get("goal", "")
    phases   = roadmap_data.get("phases", [])
    suggestions = roadmap_data.get("suggestions", [])
    project_ideas = roadmap_data.get("project_ideas", [])
    overall_tips  = roadmap_data.get("overall_tips", [])
    profile_summary = roadmap_data.get("profile_summary", "")

    valid_scores = [r.get("score", 0) for r in interview_results if r.get("score", 0) > 0]
    overall_iv   = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0

    # ═══════════════════════════════════════════
    # PAGE 1 — HEADER + HERO STATS
    # ═══════════════════════════════════════════

    story.append(Spacer(1, 6*mm))

    # Brand line
    story.append(Paragraph("CAREERFORGE AI", ps('BR', 7, C_MUTED, align=TA_CENTER,
                            space_after=4)))

    # Name
    story.append(Paragraph(candidate_name or "Career Report", TITLE))

    # Role + duration pill
    story.append(Paragraph(
        f"Career Roadmap &amp; Analysis  ·  {role}  ·  {duration}",
        SUBTITLE
    ))
    story.append(Spacer(1, 4*mm))

    # Horizontal rule (accent colored)
    story.append(HRFlowable(width="100%", thickness=1.5,
                             color=C_ACCENT, spaceAfter=6*mm))

    # ── Profile summary ───────────────────────────────────────
    if profile_summary:
        story.append(Paragraph(profile_summary, ps('PS', 9, C_WHITE,
                               align=TA_CENTER, space_after=6,
                               leading=15)))
        story.append(Spacer(1, 3*mm))

    # ── Hero stats table ──────────────────────────────────────
    ats_c  = score_color(ats_score)
    iv_c   = score_color(overall_iv)

    stats_data = [
        # Headers
        [Paragraph("ATS SCORE", ps('SL', 7, C_MUTED, bold=True, align=TA_CENTER)),
         Paragraph("SKILLS",    ps('SL2',7, C_MUTED, bold=True, align=TA_CENTER)),
         Paragraph("INTERVIEWS",ps('SL3',7, C_MUTED, bold=True, align=TA_CENTER)),
         Paragraph("AVG SCORE", ps('SL4',7, C_MUTED, bold=True, align=TA_CENTER)),
         Paragraph("TARGET",    ps('SL5',7, C_MUTED, bold=True, align=TA_CENTER))],
        # Values
        [Paragraph(str(ats_score), ps('SV', 26, ats_c, bold=True, align=TA_CENTER, space_after=0)),
         Paragraph(str(len(skills_found)), ps('SV2',26, C_ACCENT, bold=True, align=TA_CENTER, space_after=0)),
         Paragraph(str(len(interview_results)), ps('SV3',26, C_BLUE, bold=True, align=TA_CENTER, space_after=0)),
         Paragraph(str(overall_iv) if overall_iv else "—", ps('SV4',26, iv_c, bold=True, align=TA_CENTER, space_after=0)),
         Paragraph(role[:14], ps('SV5',10, C_WHITE, bold=True, align=TA_CENTER, space_after=0))],
        # Sub-labels
        [Paragraph("/100", ps('SS', 7, C_MUTED, align=TA_CENTER)),
         Paragraph("detected", ps('SS2',7, C_MUTED, align=TA_CENTER)),
         Paragraph("attempts", ps('SS3',7, C_MUTED, align=TA_CENTER)),
         Paragraph("/100", ps('SS4',7, C_MUTED, align=TA_CENTER)),
         Paragraph("role", ps('SS5',7, C_MUTED, align=TA_CENTER))],
    ]
    stats_tbl = Table(stats_data, colWidths=['20%','20%','20%','20%','20%'])
    stats_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), C_SURFACE),
        ('BOX',        (0,0), (-1,-1), 1, C_BORDER),
        ('LINEAFTER',  (0,0), (3,2),   0.5, C_BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(stats_tbl)
    story.append(Spacer(1, 8*mm))

    # ═══════════════════════════════════════════
    # INTERVIEW RESULTS SECTION
    # ═══════════════════════════════════════════
    if interview_results:
        story.append(Paragraph("INTERVIEW PERFORMANCE", SEC_HDR))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4))

        ir_header = [
            Paragraph("ROUND",   ps('IH', 7, C_MUTED, bold=True)),
            Paragraph("SCORE",   ps('IH2',7, C_MUTED, bold=True, align=TA_CENTER)),
            Paragraph("GRADE",   ps('IH3',7, C_MUTED, bold=True, align=TA_CENTER)),
            Paragraph("STRENGTHS",ps('IH4',7,C_MUTED, bold=True)),
            Paragraph("TO IMPROVE",ps('IH5',7,C_MUTED,bold=True)),
        ]
        ir_rows = [ir_header]

        for ir in interview_results:
            sc  = ir.get("score", 0)
            sc_c = score_color(sc)
            rnd  = ir.get("round", "").replace("_", " ").title()
            strs = ", ".join(ir.get("strengths", [])[:2]) or "—"
            imps = ", ".join(ir.get("improvements", [])[:2]) or "—"

            ir_rows.append([
                Paragraph(rnd, ps('IC', 9, C_WHITE)),
                Paragraph(f"{sc}/100", ps('IC2',11, sc_c, bold=True, align=TA_CENTER)),
                Paragraph(ir.get("grade", ""), ps('IC3',8, sc_c, align=TA_CENTER)),
                Paragraph(strs[:60], ps('IC4',7, C_GREEN)),
                Paragraph(imps[:60], ps('IC5',7, C_MUTED)),
            ])

        # Overall row
        if overall_iv:
            ir_rows.append([
                Paragraph("OVERALL", ps('OA', 8, C_ACCENT, bold=True)),
                Paragraph(f"{overall_iv}/100", ps('OB',12, score_color(overall_iv), bold=True, align=TA_CENTER)),
                Paragraph("Average", ps('OC',7, C_MUTED, align=TA_CENTER)),
                Paragraph("", SMALL),
                Paragraph("", SMALL),
            ])

        ir_tbl = dark_table(ir_rows, ['22%','14%','14%','25%','25%'])
        story.append(ir_tbl)
        story.append(Spacer(1, 8*mm))

    # ═══════════════════════════════════════════
    # SKILLS SECTION
    # ═══════════════════════════════════════════
    if skills_found:
        story.append(Paragraph("SKILLS DETECTED", SEC_HDR))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4))

        # Skills in a wrapped grid — 4 per row
        chunk_size = 4
        for i in range(0, min(len(skills_found), 32), chunk_size):
            chunk = skills_found[i:i+chunk_size]
            while len(chunk) < chunk_size:
                chunk.append("")
            row = [Paragraph(s, ps(f'SK{i+j}', 8, C_WHITE if s else C_MUTED,
                                   align=TA_CENTER)) for j, s in enumerate(chunk)]
            t = Table([row], colWidths=['25%','25%','25%','25%'])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), C_CARD),
                ('BOX',        (0,0), (-1,-1), 0.3, C_BORDER),
                ('INNERGRID',  (0,0), (-1,-1), 0.3, C_BORDER),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING',(0,0),(-1,-1),5),
                ('VALIGN',     (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(t)

        story.append(Spacer(1, 8*mm))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # PAGE 2 — ROADMAP
    # ═══════════════════════════════════════════

    story.append(Paragraph("CAREERFORGE AI", ps('BR2', 7, C_MUTED, align=TA_CENTER, space_after=6)))
    story.append(Paragraph("LEARNING ROADMAP", ps('RMT', 18, C_ACCENT, bold=True,
                            align=TA_CENTER, space_after=3)))
    story.append(Paragraph(
        f"{role}  ·  {duration}  ·  Goal: {goal}",
        SUBTITLE
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_ACCENT, spaceAfter=6*mm))

    phase_color_map = {
        'amber':  C_AMBER,
        'green':  C_GREEN,
        'blue':   C_BLUE,
        'purple': C_PURPLE,
        'red':    C_RED,
        'teal':   colors.HexColor('#2dd4bf'),
    }

    for phase in phases:
        ph_c = phase_color_map.get(phase.get("color", "amber"), C_AMBER)

        # Phase header block
        ph_header_data = [[
            Paragraph(f"{phase.get('emoji','→')} PHASE {phase.get('phase','')} — {phase.get('title','').upper()}",
                      ps('PH2', 10, ph_c, bold=True)),
            Paragraph(f"{phase.get('duration_weeks',1)} week{'s' if phase.get('duration_weeks',1)!=1 else ''}",
                      ps('PD', 8, ph_c, align=TA_RIGHT)),
        ]]
        ph_hdr_tbl = Table(ph_header_data, colWidths=['80%','20%'])
        ph_hdr_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,-1), colors.HexColor(
                '#' + ''.join(f'{int(c*0.12):02x}' for c in ph_c.rgb()) if hasattr(ph_c,'rgb') else '1e1a10'
            )),
            ('LINEBELOW',  (0,0),(-1,0), 1, ph_c),
            ('TOPPADDING', (0,0),(-1,-1), 8),
            ('BOTTOMPADDING',(0,0),(-1,-1), 8),
            ('LEFTPADDING', (0,0),(-1,-1), 10),
            ('RIGHTPADDING',(0,0),(-1,-1), 10),
            ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ]))

        if phase.get("focus"):
            focus_p = Paragraph(phase["focus"], ps('PF', 8, C_MUTED, space_before=2, space_after=6))
        else:
            focus_p = Spacer(1, 4)

        story.append(KeepTogether([ph_hdr_tbl, focus_p]))

        # Steps
        for step in phase.get("steps", []):
            step_rows = []

            # Step title row
            step_rows.append([
                Paragraph(step.get("day_range", ""), ps('DR', 7, ph_c, bold=True)),
                Paragraph(step.get("title", ""), ps('STT', 9, C_WHITE, bold=True)),
            ])

            # Description
            if step.get("description"):
                step_rows.append([
                    Paragraph("", SMALL),
                    Paragraph(step["description"], ps('SD', 8, C_MUTED, leading=12, space_after=2)),
                ])

            # Topics with subtopics
            for topic in step.get("topics", []):
                step_rows.append([
                    Paragraph("", SMALL),
                    Paragraph(f"▸ {topic.get('name','')}", ps('TN', 8, ph_c, bold=True, space_after=1)),
                ])
                if topic.get("subtopics"):
                    subs = "  ·  ".join(topic["subtopics"][:4])
                    step_rows.append([
                        Paragraph("", SMALL),
                        Paragraph(subs, ps('TS', 7, C_MUTED, leading=11, space_after=1)),
                    ])
                if topic.get("practice"):
                    step_rows.append([
                        Paragraph("", SMALL),
                        Paragraph(f"Practice: {topic['practice']}", ps('TP', 7, C_ACCENT, leading=11, space_after=2)),
                    ])

            # Milestone
            if step.get("milestone"):
                step_rows.append([
                    Paragraph("", SMALL),
                    Paragraph(f"✓ {step['milestone']}", ps('SM', 7, C_GREEN, leading=11, space_before=2)),
                ])

            step_tbl = Table(step_rows, colWidths=['18%', '82%'])
            step_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,-1), colors.HexColor('#101010')),
                ('BOX',        (0,0),(-1,-1), 0.5, C_BORDER),
                ('LINEBEFORE', (1,0),(1,-1), 2, colors.HexColor(
                    '#' + ''.join(f'{max(0,int(c*0.4)):02x}' for c in [0x2a,0x2a,0x2a])
                )),
                ('LEFTPADDING', (0,0),(-1,-1), 8),
                ('RIGHTPADDING',(0,0),(-1,-1), 8),
                ('TOPPADDING', (0,0),(-1,-1), 5),
                ('BOTTOMPADDING',(0,0),(-1,-1), 4),
                ('VALIGN',     (0,0),(-1,-1), 'TOP'),
            ]))
            story.append(step_tbl)
            story.append(Spacer(1, 2*mm))

        story.append(Spacer(1, 4*mm))

    story.append(PageBreak())

    # ═══════════════════════════════════════════
    # PAGE 3 — SUGGESTIONS + TIPS + PROJECTS
    # ═══════════════════════════════════════════

    story.append(Paragraph("CAREERFORGE AI", ps('BR3', 7, C_MUTED, align=TA_CENTER, space_after=6)))
    story.append(Paragraph("SUGGESTIONS & IMPROVEMENTS", ps('SGT', 18, C_ACCENT,
                            bold=True, align=TA_CENTER, space_after=8)))
    story.append(HRFlowable(width="100%", thickness=1.5, color=C_ACCENT, spaceAfter=6*mm))

    # ── Resume suggestions ─────────────────────────────────────
    if suggestions:
        story.append(Paragraph("RESUME IMPROVEMENT PLAN", SEC_HDR))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4))

        for sug in suggestions:
            priority = sug.get("priority", "Medium")
            p_color  = C_RED if priority == "High" else (C_AMBER if priority == "Medium" else C_GREEN)

            sug_rows = [[
                Paragraph(f"#{sug.get('id','')}  {sug.get('title','')}", STEP_T),
                Paragraph(priority, ps('PR', 7, p_color, bold=True, align=TA_CENTER)),
            ]]
            if sug.get("summary"):
                sug_rows.append([
                    Paragraph(sug["summary"], MUTED_T),
                    Paragraph("", SMALL),
                ])

            # Detail plan topics
            dp = sug.get("detail_plan", {})
            if dp.get("why"):
                sug_rows.append([
                    Paragraph(f"Why: {dp['why'][:100]}", ps('DW', 7, C_MUTED, leading=11)),
                    Paragraph("", SMALL),
                ])
            for topic in dp.get("topics", [])[:2]:
                sug_rows.append([
                    Paragraph(f"▸ {topic.get('topic','')}: {topic.get('description','')[:80]}",
                              ps('DT', 7, C_WHITE, leading=11)),
                    Paragraph(f"~{topic.get('time_needed','')}", ps('TM', 7, C_MUTED, align=TA_CENTER)),
                ])

            if dp.get("quick_wins"):
                qw = "  ·  ".join(dp["quick_wins"][:3])
                sug_rows.append([
                    Paragraph(f"Quick wins: {qw}", GREEN_T),
                    Paragraph("", SMALL),
                ])

            sug_tbl = Table(sug_rows, colWidths=['82%', '18%'])
            sug_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,-1), C_CARD),
                ('BOX',        (0,0),(-1,-1), 0.5, C_BORDER),
                ('LINEBEFORE', (0,0),(0,-1), 2, p_color),
                ('LEFTPADDING',(0,0),(-1,-1), 10),
                ('RIGHTPADDING',(0,0),(-1,-1), 8),
                ('TOPPADDING', (0,0),(-1,-1), 6),
                ('BOTTOMPADDING',(0,0),(-1,-1), 5),
                ('VALIGN',     (0,0),(-1,-1), 'TOP'),
            ]))
            story.append(sug_tbl)
            story.append(Spacer(1, 2*mm))

        story.append(Spacer(1, 6*mm))

    # ── Project ideas ─────────────────────────────────────────
    if project_ideas:
        story.append(Paragraph("RECOMMENDED PROJECTS", SEC_HDR))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4))

        for proj in project_ideas:
            diff  = proj.get("difficulty", "Intermediate")
            d_col = C_RED if diff == "Advanced" else (C_AMBER if diff == "Intermediate" else C_GREEN)

            proj_rows = [[
                Paragraph(f"◆ {proj.get('title','')}", TIP_T),
                Paragraph(f"{diff} · {proj.get('time_estimate','')}",
                          ps('PJ', 7, d_col, align=TA_RIGHT)),
            ]]
            if proj.get("description"):
                proj_rows.append([
                    Paragraph(proj["description"], MUTED_T),
                    Paragraph("", SMALL),
                ])
            if proj.get("tech_stack"):
                proj_rows.append([
                    Paragraph("Stack: " + " · ".join(proj["tech_stack"][:5]),
                              ps('PS2', 7, C_ACCENT)),
                    Paragraph("", SMALL),
                ])
            if proj.get("impact"):
                proj_rows.append([
                    Paragraph(f"✓ {proj['impact']}", GREEN_T),
                    Paragraph("", SMALL),
                ])

            proj_tbl = Table(proj_rows, colWidths=['75%','25%'])
            proj_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0,0),(-1,-1), C_CARD),
                ('BOX',        (0,0),(-1,-1), 0.5, C_BORDER),
                ('LINEBEFORE', (0,0),(0,-1), 2, C_ACCENT),
                ('LEFTPADDING',(0,0),(-1,-1), 10),
                ('RIGHTPADDING',(0,0),(-1,-1), 8),
                ('TOPPADDING', (0,0),(-1,-1), 7),
                ('BOTTOMPADDING',(0,0),(-1,-1), 6),
                ('VALIGN',     (0,0),(-1,-1), 'TOP'),
            ]))
            story.append(proj_tbl)
            story.append(Spacer(1, 2*mm))

        story.append(Spacer(1, 6*mm))

    # ── Career tips ───────────────────────────────────────────
    if overall_tips:
        story.append(Paragraph("CAREER TIPS", SEC_HDR))
        story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORDER, spaceAfter=4))

        tips_data = [[
            Paragraph(f"0{i+1}", ps(f'TN{i}', 20, colors.HexColor('#2a2a2a'), bold=True)),
            Paragraph(tip, ps(f'TB{i}', 8, C_WHITE, leading=13))
        ] for i, tip in enumerate(overall_tips[:4])]

        tips_tbl = Table(tips_data, colWidths=['12%', '88%'])
        tips_tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0),(-1,-1), C_CARD),
            ('BOX',        (0,0),(-1,-1), 0.5, C_BORDER),
            ('INNERGRID',  (0,0),(-1,-1), 0.3, C_BORDER),
            ('LEFTPADDING',(0,0),(-1,-1), 10),
            ('RIGHTPADDING',(0,0),(-1,-1), 10),
            ('TOPPADDING', (0,0),(-1,-1), 8),
            ('BOTTOMPADDING',(0,0),(-1,-1), 8),
            ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
        ]))
        story.append(tips_tbl)
        story.append(Spacer(1, 8*mm))

    # ── Footer ────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=C_BORDER, spaceAfter=3*mm))
    story.append(Paragraph(
        "Generated by CareerForge AI  ·  Powered by Groq LLaMA-3.3-70b  ·  careerforge.ai",
        FOOTER
    ))

    # ── Build with background ─────────────────────────────────
    def draw_bg(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(C_BG)
        canvas.rect(0, 0, W, H, fill=1, stroke=0)

        # Top accent bar
        canvas.setFillColor(C_ACCENT)
        canvas.rect(0, H - 3, W, 3, fill=1, stroke=0)

        # Page number
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(C_MUTED)
        canvas.drawCentredString(W/2, 8*mm, f"Page {doc.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_bg, onLaterPages=draw_bg)
    buffer.seek(0)
    return buffer.read()
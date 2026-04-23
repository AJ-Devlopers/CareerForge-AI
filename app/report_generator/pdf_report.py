# app/report_generator/pdf_report.py
"""
PDF Report Generator — CareerForge AI
"""

from io import BytesIO


def generate_pdf(
    candidate_name:    str,
    ats_score:         int,
    skills_found:      list,
    interview_results: list,
    roadmap_data:      dict,
) -> bytes:

    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer,
        Table, TableStyle, HRFlowable,
        KeepTogether, PageBreak,
    )
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

    # ── Palette ───────────────────────────────────────────────
    C_PAPER   = colors.HexColor('#f5f0e8')
    C_PAPER2  = colors.HexColor('#ede8dc')
    C_CARD    = colors.HexColor('#ffffff')
    C_BORDER  = colors.HexColor('#ddd8cc')
    C_BORDER2 = colors.HexColor('#c8c2b4')

    C_CORAL   = colors.HexColor('#e8490e')
    C_CORAL_L = colors.HexColor('#fff0eb')
    C_GOLD    = colors.HexColor('#c9940a')
    C_GOLD_L  = colors.HexColor('#fef9ee')

    C_INK     = colors.HexColor('#1a1614')
    C_INK2    = colors.HexColor('#3d3530')
    C_MUTED   = colors.HexColor('#7a7268')
    C_MUTED2  = colors.HexColor('#a8a098')

    C_GREEN   = colors.HexColor('#166534')
    C_GREEN_L = colors.HexColor('#f0fdf4')
    C_GREEN_B = colors.HexColor('#bbf7d0')
    C_AMBER   = colors.HexColor('#92400e')
    C_AMBER_L = colors.HexColor('#fffbeb')
    C_AMBER_B = colors.HexColor('#fde68a')
    C_RED     = colors.HexColor('#991b1b')
    C_RED_L   = colors.HexColor('#fef2f2')
    C_RED_B   = colors.HexColor('#fecaca')
    C_BLUE    = colors.HexColor('#1e3a8a')
    C_BLUE_L  = colors.HexColor('#eff6ff')
    C_BLUE_B  = colors.HexColor('#bfdbfe')
    C_PURPLE  = colors.HexColor('#581c87')
    C_TEAL    = colors.HexColor('#134e4a')
    C_TEAL_L  = colors.HexColor('#f0fdfa')
    C_TEAL_B  = colors.HexColor('#99f6e4')

    PHASE_C  = {'amber':C_AMBER,'green':C_GREEN,'blue':C_BLUE,'purple':C_PURPLE,'red':C_RED,'teal':C_TEAL}
    PHASE_BG = {'amber':C_AMBER_L,'green':C_GREEN_L,'blue':C_BLUE_L,'purple':colors.HexColor('#faf5ff'),'red':C_RED_L,'teal':C_TEAL_L}
    PHASE_BD = {'amber':C_AMBER_B,'green':C_GREEN_B,'blue':C_BLUE_B,'purple':colors.HexColor('#e9d5ff'),'red':C_RED_B,'teal':C_TEAL_B}

    W, H = A4
    buffer = BytesIO()

    # ── Style factory — NO inline XML ─────────────────────────
    _style_cache = {}
    def ps(name, size, color=C_INK, bold=False, align=TA_LEFT,
           sb=0, sa=4, leading=None):
        key = f"{name}_{id(color)}_{bold}_{align}"
        if key not in _style_cache:
            _style_cache[key] = ParagraphStyle(
                name,
                fontName='Helvetica-Bold' if bold else 'Helvetica',
                fontSize=size, textColor=color,
                alignment=align, spaceBefore=sb, spaceAfter=sa,
                leading=leading or max(size + 3, size * 1.32),
            )
        return _style_cache[key]

    def sc(s):
        return C_GREEN if s >= 75 else (C_AMBER if s >= 50 else C_RED)
    def sc_bg(s):
        return C_GREEN_L if s >= 75 else (C_AMBER_L if s >= 50 else C_RED_L)
    def sc_bd(s):
        return C_GREEN_B if s >= 75 else (C_AMBER_B if s >= 50 else C_RED_B)

    # ── Doc ───────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=18*mm, leftMargin=18*mm,
        topMargin=24*mm, bottomMargin=20*mm,
        title=f"CareerForge — {candidate_name}",
        author="CareerForge AI",
    )

    # ── Data ──────────────────────────────────────────────────
    role            = str(roadmap_data.get("role", "") or "")
    duration        = str(roadmap_data.get("duration", "") or "")
    goal            = str(roadmap_data.get("goal", "") or "")
    phases          = roadmap_data.get("phases", []) or []
    suggestions     = roadmap_data.get("suggestions", []) or []
    project_ideas   = roadmap_data.get("project_ideas", []) or []
    overall_tips    = roadmap_data.get("overall_tips", []) or []
    profile_summary = str(roadmap_data.get("profile_summary", "") or "")
    combined_score  = int(roadmap_data.get("combined_score", 0) or 0)
    grade           = str(roadmap_data.get("grade", "—") or "—")

    valid_scores = [r.get("score", 0) for r in interview_results
                    if isinstance(r.get("score"), (int, float)) and r["score"] > 0]
    overall_iv = round(sum(valid_scores) / len(valid_scores)) if valid_scores else 0

    story = []

    # ── Helper: safe plain text (no XML chars) ────────────────
    def safe(text):
        if not text:
            return ""
        return (str(text)
                .replace("&", "and")
                .replace("<", "")
                .replace(">", "")
                .replace('"', "'"))

    def truncate(text, n):
        text = safe(text)
        return text[:n] + ("..." if len(text) > n else "")

    # ── Helper: section header ────────────────────────────────
    def section_hdr(title, color=C_CORAL):
        t = Table(
            [[Paragraph(title, ps(f"sh_{title[:8]}", 7, color, bold=True))]],
            colWidths=["100%"]
        )
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), C_PAPER2),
            ("LINEBEFORE",    (0,0),(0,-1),  3, color),
            ("LINEBELOW",     (0,0),(-1,-1), 0.5, C_BORDER),
            ("LEFTPADDING",   (0,0),(-1,-1), 10),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ]))
        return [t, Spacer(1, 3*mm)]

    # ── Helper: stat card ─────────────────────────────────────
    def stat_card(label, value, sub, bg, border, val_color):
        d = [
            [Paragraph(safe(label), ps(f"sl_{label}", 6, C_MUTED, bold=True, align=TA_CENTER, sa=1))],
            [Paragraph(safe(str(value)), ps(f"sv_{label}", 22, val_color, bold=True, align=TA_CENTER, sa=0, leading=24))],
            [Paragraph(safe(sub), ps(f"ss_{label}", 6, C_MUTED2, align=TA_CENTER, sa=0))],
        ]
        t = Table(d, colWidths=["100%"])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), bg),
            ("BOX",           (0,0),(-1,-1), 1, border),
            ("TOPPADDING",    (0,0),(-1,-1), 8),
            ("BOTTOMPADDING", (0,0),(-1,-1), 8),
            ("LEFTPADDING",   (0,0),(-1,-1), 4),
            ("RIGHTPADDING",  (0,0),(-1,-1), 4),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        return t

    # ════════════════════════════════════════════
    # PAGE 1 — COVER + STATS + INTERVIEWS + SKILLS
    # ════════════════════════════════════════════
    story.append(Spacer(1, 4*mm))

    # Brand
    story.append(Paragraph("CAREERFORGE AI",
        ps("brand", 7, C_MUTED, align=TA_CENTER, sa=3)))

    # Name
    story.append(Paragraph(safe(candidate_name) or "Career Report",
        ps("cname", 30, C_INK, bold=True, align=TA_CENTER, sa=3, leading=34)))

    # Role + duration (plain text, no inline color XML)
    subtitle_parts = []
    if role:     subtitle_parts.append(role)
    if duration: subtitle_parts.append(duration)
    subtitle_parts.append("Career Analysis and Roadmap")
    story.append(Paragraph("  |  ".join(subtitle_parts),
        ps("rsub", 9, C_MUTED, align=TA_CENTER, sa=6)))

    story.append(HRFlowable(width="100%", thickness=2.5,
                             color=C_CORAL, spaceAfter=5*mm))

    # Profile summary — plain text, styled via ParagraphStyle
    if profile_summary:
        sum_data = [[Paragraph(safe(profile_summary),
            ps("psm", 9, C_INK2, align=TA_CENTER, leading=15, sa=0))]]
        sum_tbl = Table(sum_data, colWidths=["100%"])
        sum_tbl.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), C_CORAL_L),
            ("BOX",           (0,0),(-1,-1), 1, C_CORAL),
            ("LEFTPADDING",   (0,0),(-1,-1), 16),
            ("RIGHTPADDING",  (0,0),(-1,-1), 16),
            ("TOPPADDING",    (0,0),(-1,-1), 12),
            ("BOTTOMPADDING", (0,0),(-1,-1), 12),
        ]))
        story.append(sum_tbl)
        story.append(Spacer(1, 6*mm))

    # Hero stat cards
    cards = [
        stat_card("ATS SCORE",  ats_score,            "/100",     sc_bg(ats_score),    sc_bd(ats_score),   sc(ats_score)),
        stat_card("SKILLS",     len(skills_found),     "detected", C_GOLD_L,            C_AMBER_B,          C_GOLD),
        stat_card("INTERVIEWS", len(interview_results),"attempts", C_BLUE_L,            C_BLUE_B,           C_BLUE),
        stat_card("AVG SCORE",  overall_iv or "—",    "/100",     sc_bg(overall_iv),   sc_bd(overall_iv),  sc(overall_iv) if overall_iv else C_MUTED),
        stat_card("GRADE",      grade,                 "overall",  C_CORAL_L,           C_CORAL,            C_CORAL),
    ]
    cards_row = Table([cards], colWidths=["20%"]*5)
    cards_row.setStyle(TableStyle([
        ("LEFTPADDING",  (0,0),(-1,-1), 2),
        ("RIGHTPADDING", (0,0),(-1,-1), 2),
        ("TOPPADDING",   (0,0),(-1,-1), 0),
        ("BOTTOMPADDING",(0,0),(-1,-1), 0),
        ("VALIGN",       (0,0),(-1,-1), "TOP"),
    ]))
    story.append(cards_row)
    story.append(Spacer(1, 8*mm))

    # ── Interview Performance ─────────────────────────────────
    if interview_results:
        story.extend(section_hdr("INTERVIEW PERFORMANCE", C_CORAL))

        hdr = [
            Paragraph("ROUND",      ps("ih1",7,C_MUTED,bold=True)),
            Paragraph("SCORE",      ps("ih2",7,C_MUTED,bold=True,align=TA_CENTER)),
            Paragraph("GRADE",      ps("ih3",7,C_MUTED,bold=True,align=TA_CENTER)),
            Paragraph("STRENGTHS",  ps("ih4",7,C_MUTED,bold=True)),
            Paragraph("TO IMPROVE", ps("ih5",7,C_MUTED,bold=True)),
        ]
        rows = [hdr]
        for i, ir in enumerate(interview_results):
            s   = int(ir.get("score", 0) or 0)
            s_c = sc(s)
            s_bg= sc_bg(s)
            rnd = safe((ir.get("round") or "").replace("_", " ").title())
            strs= safe(", ".join((ir.get("strengths") or [])[:2]) or "—")
            imps= safe(", ".join((ir.get("improvements") or [])[:2]) or "—")
            rows.append([
                Paragraph(rnd[:40],      ps(f"ir1{i}",9,C_INK)),
                Paragraph(f"{s}/100",    ps(f"ir2{i}",11,s_c,bold=True,align=TA_CENTER)),
                Paragraph(safe(ir.get("grade","") or ""), ps(f"ir3{i}",8,s_c,align=TA_CENTER)),
                Paragraph(strs[:55],     ps(f"ir4{i}",7,C_GREEN)),
                Paragraph(imps[:55],     ps(f"ir5{i}",7,C_AMBER)),
            ])
        if overall_iv:
            ov_c = sc(overall_iv)
            rows.append([
                Paragraph("OVERALL AVERAGE", ps("oa",8,C_INK,bold=True)),
                Paragraph(f"{overall_iv}/100", ps("ob",11,ov_c,bold=True,align=TA_CENTER)),
                Paragraph("Average", ps("oc",7,C_MUTED,align=TA_CENTER)),
                Paragraph("", ps("od",7,C_MUTED)),
                Paragraph("", ps("oe",7,C_MUTED)),
            ])

        t = Table(rows, colWidths=["22%","13%","13%","26%","26%"])
        n = len(rows)
        style = [
            ("BOX",           (0,0),(-1,-1), 0.8, C_BORDER),
            ("INNERGRID",     (0,0),(-1,-1), 0.3, C_BORDER),
            ("BACKGROUND",    (0,0),(-1,0),  C_PAPER2),
            ("BACKGROUND",    (0,n-1),(-1,n-1), C_CORAL_L),
            ("TOPPADDING",    (0,0),(-1,-1), 7),
            ("BOTTOMPADDING", (0,0),(-1,-1), 7),
            ("LEFTPADDING",   (0,0),(-1,-1), 8),
            ("RIGHTPADDING",  (0,0),(-1,-1), 8),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]
        for ri in range(1, n-1):
            bg = C_CARD if ri % 2 == 0 else C_PAPER
            style.append(("BACKGROUND", (0,ri),(-1,ri), bg))
        t.setStyle(TableStyle(style))
        story.append(t)
        story.append(Spacer(1, 8*mm))

    # ── Skills ────────────────────────────────────────────────
    if skills_found:
        story.extend(section_hdr("SKILLS DETECTED", C_GOLD))
        chunk = 5
        for i in range(0, min(len(skills_found), 30), chunk):
            row = skills_found[i:i+chunk]
            while len(row) < chunk:
                row.append("")
            cells = [
                Paragraph(safe(s), ps(f"sk{i+j}",8, C_INK if s else C_MUTED2, align=TA_CENTER))
                for j, s in enumerate(row)
            ]
            t = Table([cells], colWidths=["20%"]*chunk)
            style = [
                ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
                ("INNERGRID",     (0,0),(-1,-1), 0.5, C_BORDER),
                ("TOPPADDING",    (0,0),(-1,-1), 6),
                ("BOTTOMPADDING", (0,0),(-1,-1), 6),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ]
            for ci, s in enumerate(row):
                style.append(("BACKGROUND", (ci,0),(ci,0), C_GOLD_L if s else C_PAPER))
            t.setStyle(TableStyle(style))
            story.append(t)
        story.append(Spacer(1, 6*mm))

    story.append(PageBreak())

    # ════════════════════════════════════════════
    # PAGE 2 — ROADMAP
    # ════════════════════════════════════════════
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("CareerForge AI",
        ps("br2",7,C_MUTED,align=TA_CENTER,sa=1)))
    story.append(Paragraph(safe(candidate_name) or "Career Report",
        ps("cn2",11,C_CORAL,bold=True,align=TA_CENTER,sa=2)))
    story.append(Paragraph("LEARNING ROADMAP",
        ps("rmt",22,C_INK,bold=True,align=TA_CENTER,sa=3,leading=26)))

    rm_parts = []
    if role:     rm_parts.append(role)
    if duration: rm_parts.append(duration)
    if goal:     rm_parts.append(goal)
    story.append(Paragraph("  |  ".join(rm_parts),
        ps("rsub2",8,C_MUTED,align=TA_CENTER,sa=5)))
    story.append(HRFlowable(width="100%",thickness=2,color=C_CORAL,spaceAfter=6*mm))

    for pi, phase in enumerate(phases):
        ph_key = str(phase.get("color","amber"))
        ph_c   = PHASE_C.get(ph_key, C_AMBER)
        ph_bg  = PHASE_BG.get(ph_key, C_AMBER_L)
        ph_bd  = PHASE_BD.get(ph_key, C_AMBER_B)

        ph_title = safe(phase.get("title",""))
        ph_num   = phase.get("phase", pi+1)
        ph_emoji = safe(phase.get("emoji",""))
        ph_wks   = int(phase.get("duration_weeks",1) or 1)
        ph_focus = safe(phase.get("focus",""))

        ph_hdr = Table([[
            Paragraph(
                f"{ph_emoji}  PHASE {ph_num} - {ph_title.upper()}",
                ps(f"phh{pi}",10,ph_c,bold=True)
            ),
            Paragraph(
                f"{ph_wks} week{'s' if ph_wks!=1 else ''}",
                ps(f"phd{pi}",8,ph_c,align=TA_RIGHT)
            ),
        ]], colWidths=["76%","24%"])
        ph_hdr.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1), ph_bg),
            ("BOX",           (0,0),(-1,-1), 1, ph_bd),
            ("LINEBEFORE",    (0,0),(0,-1),  4, ph_c),
            ("TOPPADDING",    (0,0),(-1,-1), 10),
            ("BOTTOMPADDING", (0,0),(-1,-1), 10),
            ("LEFTPADDING",   (0,0),(-1,-1), 12),
            ("RIGHTPADDING",  (0,0),(-1,-1), 12),
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ]))
        focus_p = (
            Paragraph(ph_focus, ps(f"phf{pi}",8,C_MUTED,sb=2,sa=4))
            if ph_focus else Spacer(1, 3)
        )
        story.append(KeepTogether([ph_hdr, focus_p]))

        for si, step in enumerate(phase.get("steps") or []):
            step_rows = []
            step_rows.append([
                Paragraph(safe(step.get("day_range","")), ps(f"dr{pi}{si}",6,ph_c,bold=True)),
                Paragraph(safe(step.get("title","")),     ps(f"st{pi}{si}",9,C_INK,bold=True)),
            ])
            if step.get("description"):
                step_rows.append([
                    Paragraph("", ps("e0",7,C_MUTED)),
                    Paragraph(truncate(step["description"],200),
                              ps(f"sd{pi}{si}",8,C_MUTED,leading=12,sa=2)),
                ])
            for ti, topic in enumerate(step.get("topics") or []):
                step_rows.append([
                    Paragraph("", ps("e1",7,C_MUTED)),
                    Paragraph(f"-> {safe(topic.get('name',''))}",
                              ps(f"tn{pi}{si}{ti}",8,ph_c,bold=True,sa=1)),
                ])
                subs = topic.get("subtopics") or []
                if subs:
                    step_rows.append([
                        Paragraph("", ps("e2",7,C_MUTED)),
                        Paragraph("  |  ".join(safe(s) for s in subs[:4]),
                                  ps(f"ts{pi}{si}{ti}",7,C_MUTED,leading=11,sa=1)),
                    ])
                if topic.get("practice"):
                    step_rows.append([
                        Paragraph("", ps("e3",7,C_MUTED)),
                        Paragraph(f"Practice: {truncate(topic['practice'],80)}",
                                  ps(f"tp{pi}{si}{ti}",7,C_CORAL,leading=11,sa=2)),
                    ])
            if step.get("milestone"):
                step_rows.append([
                    Paragraph("", ps("e5",7,C_MUTED)),
                    Paragraph(f"OK  {truncate(step['milestone'],100)}",
                              ps(f"sm{pi}{si}",7,C_GREEN,leading=11,sb=2)),
                ])

            if step_rows:
                st = Table(step_rows, colWidths=["17%","83%"])
                st.setStyle(TableStyle([
                    ("BACKGROUND",    (0,0),(-1,-1), C_CARD),
                    ("BACKGROUND",    (0,0),(0,-1),  C_PAPER2),
                    ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
                    ("LINEBEFORE",    (1,0),(1,-1),  3, ph_c),
                    ("LEFTPADDING",   (0,0),(-1,-1), 8),
                    ("RIGHTPADDING",  (0,0),(-1,-1), 8),
                    ("TOPPADDING",    (0,0),(-1,-1), 5),
                    ("BOTTOMPADDING", (0,0),(-1,-1), 4),
                    ("VALIGN",        (0,0),(-1,-1), "TOP"),
                ]))
                story.append(st)
                story.append(Spacer(1, 2*mm))

        story.append(Spacer(1, 5*mm))

    story.append(PageBreak())

    # ════════════════════════════════════════════
    # PAGE 3 — SUGGESTIONS + PROJECTS + TIPS
    # ════════════════════════════════════════════
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph("CareerForge AI",
        ps("br3",7,C_MUTED,align=TA_CENTER,sa=1)))
    story.append(Paragraph(safe(candidate_name) or "Career Report",
        ps("cn3",11,C_CORAL,bold=True,align=TA_CENTER,sa=2)))
    story.append(Paragraph("SUGGESTIONS AND IMPROVEMENTS",
        ps("sgt",20,C_INK,bold=True,align=TA_CENTER,sa=5,leading=24)))
    story.append(HRFlowable(width="100%",thickness=2,color=C_CORAL,spaceAfter=6*mm))

    # ── Suggestions ───────────────────────────────────────────
    if suggestions:
        story.extend(section_hdr("RESUME IMPROVEMENT PLAN", C_CORAL))

        PRI_C  = {"High":C_RED,   "Medium":C_AMBER,   "Low":C_GREEN}
        PRI_BG = {"High":C_RED_L, "Medium":C_AMBER_L, "Low":C_GREEN_L}
        PRI_BD = {"High":C_RED_B, "Medium":C_AMBER_B, "Low":C_GREEN_B}

        for sug in suggestions:
            pri   = str(sug.get("priority","Medium") or "Medium")
            p_c   = PRI_C.get(pri, C_AMBER)
            p_bg  = PRI_BG.get(pri, C_AMBER_L)
            p_bd  = PRI_BD.get(pri, C_AMBER_B)
            dp    = sug.get("detail_plan") or {}
            cat   = safe(sug.get("category","General") or "General")
            title = safe(sug.get("title","") or "")
            summ  = safe(sug.get("summary","") or "")

            rows = [[
                Paragraph(f"{cat} - {title}", ps(f"stt{id(sug)}",9,C_INK,bold=True)),
                Paragraph(pri, ps(f"spr{id(sug)}",7,p_c,bold=True,align=TA_CENTER)),
            ]]
            if summ:
                rows.append([
                    Paragraph(summ[:120], ps(f"ssum{id(sug)}",7,C_MUTED,leading=11)),
                    Paragraph("", ps("se0",7,C_MUTED)),
                ])
            why = safe(dp.get("why","") or "")
            if why:
                rows.append([
                    Paragraph(f"Why: {why[:130]}", ps(f"sw{id(sug)}",7,C_MUTED,leading=11)),
                    Paragraph("", ps("se1",7,C_MUTED)),
                ])
            for topic in (dp.get("topics") or [])[:2]:
                t_name = safe(topic.get("topic","") or "")
                t_desc = truncate(topic.get("description","") or "",90)
                t_time = safe(topic.get("time_needed","") or "")
                rows.append([
                    Paragraph(f"-> {t_name}: {t_desc}", ps(f"sto{id(topic)}",7,C_INK2,leading=11)),
                    Paragraph(f"~{t_time}" if t_time else "", ps(f"stm{id(topic)}",7,C_MUTED,align=TA_CENTER)),
                ])
            qw = [safe(q) for q in (dp.get("quick_wins") or [])[:3] if q]
            if qw:
                rows.append([
                    Paragraph("Quick wins: " + "  |  ".join(qw),
                              ps(f"sqw{id(sug)}",7,C_GREEN)),
                    Paragraph("", ps("se2",7,C_MUTED)),
                ])

            t = Table(rows, colWidths=["80%","20%"])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), C_CARD),
                ("BACKGROUND",    (1,0),(1,0),   p_bg),
                ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
                ("LINEBEFORE",    (0,0),(0,-1),  3, p_c),
                ("LINEABOVE",     (0,0),(-1,0),  0.5, p_bd),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("RIGHTPADDING",  (0,0),(-1,-1), 8),
                ("TOPPADDING",    (0,0),(-1,-1), 7),
                ("BOTTOMPADDING", (0,0),(-1,-1), 6),
                ("VALIGN",        (0,0),(-1,-1), "TOP"),
            ]))
            story.append(t)
            story.append(Spacer(1, 2*mm))
        story.append(Spacer(1, 5*mm))

    # ── Projects ──────────────────────────────────────────────
    if project_ideas:
        story.extend(section_hdr("RECOMMENDED PROJECTS", C_GOLD))

        DIFF_C  = {"Advanced":C_RED,   "Intermediate":C_AMBER,   "Beginner":C_GREEN}
        DIFF_BG = {"Advanced":C_RED_L, "Intermediate":C_AMBER_L, "Beginner":C_GREEN_L}

        for proj in project_ideas:
            diff  = str(proj.get("difficulty","Intermediate") or "Intermediate")
            d_c   = DIFF_C.get(diff, C_AMBER)
            d_bg  = DIFF_BG.get(diff, C_AMBER_L)
            p_title = safe(proj.get("title","") or "")
            p_desc  = truncate(proj.get("description","") or "",140)
            p_time  = safe(proj.get("time_estimate","") or "")
            p_impact= truncate(proj.get("impact","") or "",100)
            stack   = "  |  ".join(safe(s) for s in (proj.get("tech_stack") or [])[:5])

            rows = [[
                Paragraph(p_title, ps(f"pt{id(proj)}",9,C_INK,bold=True)),
                Paragraph(f"{diff}  {p_time}", ps(f"pd{id(proj)}",7,d_c,bold=True,align=TA_RIGHT)),
            ]]
            if p_desc:
                rows.append([Paragraph(p_desc, ps(f"pds{id(proj)}",8,C_MUTED,leading=12)), Paragraph("",ps("pde",7,C_MUTED))])
            if stack:
                rows.append([Paragraph(f"Stack: {stack}", ps(f"pst{id(proj)}",7,C_CORAL)), Paragraph("",ps("pse",7,C_MUTED))])
            if p_impact:
                rows.append([Paragraph(f"OK  {p_impact}", ps(f"pi{id(proj)}",7,C_GREEN)), Paragraph("",ps("pie",7,C_MUTED))])
            for step in (proj.get("implementation_steps") or [])[:3]:
                s_title = safe(step.get("title","") or "")
                s_desc  = truncate(step.get("description","") or "",70)
                s_dur   = safe(step.get("duration","") or "")
                rows.append([
                    Paragraph(f"{step.get('step','')}. {s_title}: {s_desc}", ps(f"pis{id(step)}",7,C_MUTED,leading=11)),
                    Paragraph(s_dur, ps(f"pid{id(step)}",6,C_AMBER,align=TA_CENTER)),
                ])

            t = Table(rows, colWidths=["72%","28%"])
            t.setStyle(TableStyle([
                ("BACKGROUND",    (0,0),(-1,-1), C_CARD),
                ("BACKGROUND",    (1,0),(1,0),   d_bg),
                ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
                ("LINEBEFORE",    (0,0),(0,-1),  3, C_GOLD),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("RIGHTPADDING",  (0,0),(-1,-1), 8),
                ("TOPPADDING",    (0,0),(-1,-1), 7),
                ("BOTTOMPADDING", (0,0),(-1,-1), 6),
                ("VALIGN",        (0,0),(-1,-1), "TOP"),
            ]))
            story.append(t)
            story.append(Spacer(1, 2*mm))
        story.append(Spacer(1, 5*mm))

    # ── Career Tips ───────────────────────────────────────────
    if overall_tips:
        story.extend(section_hdr("CAREER TIPS", C_TEAL))
        tip_rows = []
        for i, tip in enumerate(overall_tips[:6]):
            tip_rows.append([
                Paragraph(f"0{i+1}", ps(f"tnum{i}",18,C_BORDER2,bold=True,align=TA_CENTER,sa=0)),
                Paragraph(safe(tip), ps(f"ttxt{i}",8,C_INK,leading=13)),
            ])
        if tip_rows:
            t = Table(tip_rows, colWidths=["10%","90%"])
            style = [
                ("BOX",           (0,0),(-1,-1), 0.5, C_BORDER),
                ("INNERGRID",     (0,0),(-1,-1), 0.3, C_BORDER),
                ("LINEBEFORE",    (0,0),(0,-1),  3, C_TEAL),
                ("LEFTPADDING",   (0,0),(-1,-1), 10),
                ("RIGHTPADDING",  (0,0),(-1,-1), 10),
                ("TOPPADDING",    (0,0),(-1,-1), 9),
                ("BOTTOMPADDING", (0,0),(-1,-1), 9),
                ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ]
            for ri in range(len(tip_rows)):
                style.append(("BACKGROUND",(0,ri),(-1,ri), C_CARD if ri%2==0 else C_PAPER))
            t.setStyle(TableStyle(style))
            story.append(t)
            story.append(Spacer(1, 7*mm))

    # Footer
    story.append(HRFlowable(width="100%",thickness=1,color=C_BORDER,spaceAfter=3*mm))
    story.append(Paragraph(
        f"Generated for {safe(candidate_name) or 'Candidate'}  |  CareerForge AI  |  Powered by Groq LLaMA-3.3-70b",
        ps("footer",7,C_MUTED,align=TA_CENTER)
    ))

    # ── Page background + header ──────────────────────────────
    def draw_page(canvas, doc):
        try:
            canvas.saveState()
            canvas.setFillColor(C_PAPER)
            canvas.rect(0, 0, W, H, fill=1, stroke=0)

            # Top coral bar
            canvas.setFillColor(C_CORAL)
            canvas.rect(0, H - 6*mm, W, 6*mm, fill=1, stroke=0)

            # CF logo box
            lx, ly, lsz = 16*mm, H - 5.5*mm, 4.5*mm
            canvas.setFillColor(C_GOLD)
            canvas.roundRect(lx, ly, lsz, lsz, radius=1, fill=1, stroke=0)
            canvas.setFont("Helvetica-Bold", 5)
            canvas.setFillColor(C_PAPER)
            canvas.drawCentredString(lx + lsz/2, ly + lsz/2 - 1.5, "CF")

            # Brand text
            canvas.setFont("Helvetica-Bold", 6.5)
            canvas.setFillColor(C_PAPER)
            canvas.drawString(lx + lsz + 2*mm, H - 3.5*mm, "CareerForge AI")

            # Page number
            canvas.setFont("Helvetica", 6.5)
            canvas.drawRightString(W - 16*mm, H - 3.5*mm, f"Page {doc.page} of 3")

            # Left accent line
            canvas.setStrokeColor(C_CORAL)
            canvas.setLineWidth(0.3)
            canvas.line(10*mm, 18*mm, 10*mm, H - 7*mm)

            # Bottom rule
            canvas.setStrokeColor(C_BORDER)
            canvas.setLineWidth(0.5)
            canvas.line(16*mm, 14*mm, W - 16*mm, 14*mm)

            # Footer text
            canvas.setFont("Helvetica", 6)
            canvas.setFillColor(C_MUTED)
            canvas.drawString(16*mm, 10*mm,
                              f"{safe(candidate_name) or 'Career Report'}  |  CareerForge AI")
            canvas.drawRightString(W - 16*mm, 10*mm, safe(role) or "")

        except Exception as e:
            print(f"draw_page error: {e}")
        finally:
            canvas.restoreState()

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
    buffer.seek(0)
    return buffer.read()
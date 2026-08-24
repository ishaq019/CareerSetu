"""Render a tailored resume (see ``LatexResumeContent``) into a compilable
LaTeX document.

The template mirrors a clean single-column technical-resume style (article
class, tight margins, custom section rules). All user/LLM-provided text is
escaped for LaTeX so arbitrary resume content cannot break compilation or inject
control sequences. The output is a ``.tex`` string the frontend can offer for
download and/or compile on Overleaf.
"""
from __future__ import annotations

from app.ai.llm.schemas import LatexResumeContent

# Order matters: backslash must be replaced first.
_LATEX_REPLACEMENTS = [
    ("\\", r"\textbackslash{}"),
    ("&", r"\&"),
    ("%", r"\%"),
    ("$", r"\$"),
    ("#", r"\#"),
    ("_", r"\_"),
    ("{", r"\{"),
    ("}", r"\}"),
    ("~", r"\textasciitilde{}"),
    ("^", r"\textasciicircum{}"),
]


def esc(value: str | None) -> str:
    """Escape a plain string so it is safe to embed in LaTeX body text."""
    if not value:
        return ""
    text = str(value)
    for old, new in _LATEX_REPLACEMENTS:
        text = text.replace(old, new)
    return text.strip()


def _url(value: str) -> str:
    """Normalise a URL/handle to a bare href target (no escaping of the URL
    itself beyond stripping); returns '' when empty."""
    v = (value or "").strip()
    return v


PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage[margin=0.5in]{geometry}
\usepackage{enumitem}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}
\usepackage{xcolor}

\definecolor{accent}{HTML}{1F2937}
\hypersetup{colorlinks=true, urlcolor=accent, linkcolor=accent}

\pagestyle{empty}
\setlength{\parindent}{0pt}
\setlist[itemize]{leftmargin=1.2em, itemsep=1pt, topsep=2pt, parsep=0pt}

\titleformat{\section}{\large\bfseries\scshape\color{accent}}{}{0em}{}[\vspace{-0.6em}\hrule\vspace{0.2em}]
\titlespacing{\section}{0pt}{8pt}{4pt}

% Left/right aligned line used for entry headers.
\newcommand{\LineLR}[2]{\noindent\textbf{#1}\hfill{#2}\par}
\newcommand{\SubLR}[2]{\noindent\textit{#1}\hfill\textit{#2}\par}
"""


def _header(c) -> str:
    contacts: list[str] = []
    if c.phone:
        contacts.append(esc(c.phone))
    if c.email:
        contacts.append(rf"\href{{mailto:{_url(c.email)}}}{{{esc(c.email)}}}")
    if c.location:
        contacts.append(esc(c.location))
    if c.portfolio:
        contacts.append(rf"\href{{{_url(c.portfolio)}}}{{Portfolio}}")
    if c.linkedin:
        contacts.append(rf"\href{{{_url(c.linkedin)}}}{{LinkedIn}}")
    if c.github:
        contacts.append(rf"\href{{{_url(c.github)}}}{{GitHub}}")

    name = esc(c.name) or "Your Name"
    lines = [r"\begin{center}", rf"{{\Huge \scshape {name}}}\\[2pt]"]
    if c.title:
        lines.append(rf"{{\small {esc(c.title)}}}\\[2pt]")
    if contacts:
        lines.append(r"{\small " + r" \quad\textbar\quad ".join(contacts) + r"}")
    lines.append(r"\end{center}")
    return "\n".join(lines)


def _section(title: str, body: str) -> str:
    body = body.strip()
    if not body:
        return ""
    return f"\\section*{{{esc(title)}}}\n{body}\n"


def _bullets(items: list[str]) -> str:
    items = [esc(b) for b in (items or []) if b and b.strip()]
    if not items:
        return ""
    inner = "\n".join(rf"  \item {b}" for b in items)
    return f"\\begin{{itemize}}\n{inner}\n\\end{{itemize}}"


def _education(entries) -> str:
    parts: list[str] = []
    for e in entries or []:
        if not (e.institution or e.degree):
            continue
        parts.append(_LineLR(e.institution, esc(e.date)))
        sub = " -- ".join(x for x in [e.degree, e.detail] if x)
        if sub:
            parts.append(rf"\SubLR{{{esc(sub)}}}{{}}")
        parts.append(r"\vspace{2pt}")
    return "\n".join(parts)


def _LineLR(left: str, right_tex: str) -> str:
    """Header line. ``left`` is escaped as plain text; ``right_tex`` is inserted
    as-is so callers can pass either an escaped date or ready-made LaTeX (links)."""
    return rf"\LineLR{{{esc(left)}}}{{{right_tex}}}"


def _skills(groups) -> str:
    rows: list[str] = []
    for g in groups or []:
        items = ", ".join(esc(i) for i in (g.items or []) if i and i.strip())
        if not items:
            continue
        rows.append(rf"\noindent\textbf{{{esc(g.category)}:}} {items}\par")
    return "\n".join(rows)


def _experience(entries) -> str:
    parts: list[str] = []
    for x in entries or []:
        if not (x.company or x.role):
            continue
        title = " -- ".join(t for t in [x.role, x.company] if t)
        parts.append(_LineLR(title, esc(x.date)))
        if x.location:
            parts.append(rf"\SubLR{{{esc(x.location)}}}{{}}")
        b = _bullets(x.bullets)
        if b:
            parts.append(b)
        parts.append(r"\vspace{3pt}")
    return "\n".join(parts)


def _projects(entries) -> str:
    parts: list[str] = []
    for p in entries or []:
        if not p.name:
            continue
        links: list[str] = []
        if p.github:
            links.append(rf"\href{{{_url(p.github)}}}{{Code}}")
        if p.live:
            links.append(rf"\href{{{_url(p.live)}}}{{Live}}")
        right = " \\textbar\\ ".join(links)
        if p.date:
            right = (right + r" \quad " if right else "") + esc(p.date)
        parts.append(_LineLR(p.name, right))
        if p.tech_stack:
            parts.append(rf"\SubLR{{{esc(p.tech_stack)}}}{{}}")
        b = _bullets(p.bullets)
        if b:
            parts.append(b)
        parts.append(r"\vspace{3pt}")
    return "\n".join(parts)


def render_latex(content: LatexResumeContent) -> str:
    """Assemble a full, compilable LaTeX document from tailored resume content."""
    body_sections = [
        _header(content.contact),
        _section("Summary", esc(content.objective)),
        _section("Skills", _skills(content.skill_groups)),
        _section("Experience", _experience(content.experience)),
        _section("Projects", _projects(content.projects)),
        _section("Education", _education(content.education)),
        _section(
            "Certifications",
            _bullets(content.certifications) if content.certifications else "",
        ),
    ]
    body = "\n\n".join(s for s in body_sections if s.strip())
    return f"{PREAMBLE}\n\\begin{{document}}\n\n{body}\n\n\\end{{document}}\n"

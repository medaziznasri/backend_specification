import os
import json
import logging
from fpdf import FPDF
from fpdf.fonts import FontFace
from datetime import datetime

logger = logging.getLogger(__name__)

UPLOAD_DIR = "storage/specifications"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

# Theme
INK = (33, 37, 41)
PRIMARY = (52, 73, 94)
HEADER_BG = (44, 62, 80)
MUTED = (130, 140, 150)
SUBQ = (90, 116, 140)  # sub-question label color (lighter than PRIMARY)


# Common Unicode punctuation that isn't in Latin-1 → clean ASCII equivalents,
# so dashes/quotes/etc. don't turn into "?".
_PUNCT = {
    "–": "-", "—": "-",          # en / em dash
    "‘": "'", "’": "'",          # smart single quotes
    "“": '"', "”": '"',          # smart double quotes
    "…": "...",                        # ellipsis
    " ": " ", " ": " ",          # (narrow) non-breaking space
    "•": "-",                          # bullet
    "€": "EUR",                        # euro sign
}


def _safe(text: str) -> str:
    """Core PDF fonts are Latin-1 only. Normalize common typographic
    characters to ASCII, then replace anything still unsupported so generation
    never crashes on Arabic/emoji/other characters."""
    if text is None:
        return ""
    s = str(text)
    for bad, good in _PUNCT.items():
        s = s.replace(bad, good)
    return s.encode("latin-1", "replace").decode("latin-1")


def _format_answer(val) -> str:
    """Turn a stored answer (often a JSON string) into readable text."""
    if val is None:
        return "Non repondu"
    # Answers are stored as JSON strings in the DB; unwrap them.
    if isinstance(val, str):
        try:
            val = json.loads(val)
        except (json.JSONDecodeError, ValueError):
            pass
    if isinstance(val, list):
        return ", ".join(str(x) for x in val) if val else "Non repondu"
    if isinstance(val, dict):
        return "; ".join(f"{k}: {v}" for k, v in val.items())
    s = str(val).strip().replace("\\n", "\n")
    if len(s) >= 2 and s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s if s else "Non repondu"


def _flatten_hierarchy(items):
    """Order answers so triggered sub-questions sit under their parent.
    Returns a list of (item, depth, number) where number is like '1', '1.1'.
    Works whether or not the items carry qid/parent_id (falls back to flat)."""
    has_hierarchy = any(it.get("qid") for it in items)
    if not has_hierarchy:
        return [(it, 0, str(i)) for i, it in enumerate(items, 1)]

    by_id = {it["qid"]: it for it in items if it.get("qid")}
    children: dict = {}
    roots = []
    for it in items:
        pid = it.get("parent_id")
        if pid and pid in by_id:
            children.setdefault(pid, []).append(it)
        else:
            roots.append(it)

    def order_key(it):
        # Mirror the client form order: display_order first, then the general
        # category before others, then category name (stable tie-break).
        return (
            it.get("order") or 0,
            0 if it.get("is_general") else 1,
            (it.get("category") or "").lower(),
        )

    roots.sort(key=order_key)
    result = []

    def walk(it, depth, number):
        result.append((it, depth, number))
        kids = sorted(children.get(it.get("qid"), []), key=order_key)
        for j, kid in enumerate(kids, 1):
            walk(kid, depth + 1, f"{number}.{j}")

    for i, root in enumerate(roots, 1):
        walk(root, 0, str(i))
    return result


class SpecPDF(FPDF):
    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*MUTED)
        self.cell(0, 10, f"Cahier des charges  -  Page {self.page_no()}/{{nb}}", align="C")


def generate_physical_pdf(structured_answers, file_path, session_id, project_metadata=None):
    try:
        pdf = SpecPDF()
        pdf.set_auto_page_break(auto=True, margin=20)
        pdf.add_page()

        # ── Title band ──────────────────────────────────────────────
        pdf.set_fill_color(*HEADER_BG)
        pdf.rect(0, 0, pdf.w, 34, style="F")
        pdf.set_y(9)
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 11, _safe("Cahier des Charges Technique"), ln=True, align="C")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 6, _safe(f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')}"), ln=True, align="C")
        pdf.set_y(40)
        pdf.set_text_color(*INK)

        # ── Project information ─────────────────────────────────────
        if project_metadata:
            pdf.set_font("Helvetica", "B", 13)
            pdf.set_text_color(*PRIMARY)
            pdf.cell(0, 8, _safe("Informations du Projet"), ln=True)
            pdf.set_draw_color(*PRIMARY)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.l_margin + 45, pdf.get_y())
            pdf.ln(4)

            def kv(label, value):
                pdf.set_x(pdf.l_margin)
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(90, 90, 90)
                pdf.cell(32, 7, _safe(label), new_x="RIGHT", new_y="TOP")
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(*INK)
                pdf.multi_cell(0, 7, _safe(value), new_x="LMARGIN", new_y="NEXT")

            kv("Projet :", project_metadata.get("project_name", "N/A"))

            cats = project_metadata.get("categories", []) or []
            cats_clean = [c.replace("[GENERAL] ", "") for c in cats]
            kv("Categories :", ", ".join(cats_clean) if cats_clean else "Aucune categorie")

            desc = project_metadata.get("project_description")
            if desc:
                kv("Description :", desc)
            pdf.ln(8)

        # ── Specifications table ────────────────────────────────────
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(*PRIMARY)
        pdf.cell(0, 8, _safe("Specifications detaillees"), ln=True)
        pdf.ln(2)

        ordered = _flatten_hierarchy(list(structured_answers))

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*INK)
        pdf.set_draw_color(220, 224, 229)
        # Reset fill to white so the title-band color doesn't leak into the table.
        pdf.set_fill_color(255, 255, 255)
        headings_style = FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=PRIMARY)
        question_style = FontFace(emphasis="BOLD", color=PRIMARY)
        subq_style = FontFace(emphasis="BOLD", color=SUBQ)

        with pdf.table(
            width=pdf.epw,
            col_widths=(45, 55),
            text_align=("LEFT", "LEFT"),
            line_height=7,
            padding=2.5,
            headings_style=headings_style,
            cell_fill_color=(247, 249, 251),
            cell_fill_mode="ROWS",
            borders_layout="ALL",
        ) as table:
            table.row(["Question", "Reponse"])  # repeats on each page automatically
            if ordered:
                for item, depth, number in ordered:
                    q = _safe(item.get("question", ""))
                    a = _safe(_format_answer(item.get("answer", "")))
                    if depth > 0:
                        # Indent sub-questions and mark them with an arrow.
                        label = f"{'    ' * depth}> {number}  {q}"
                        style = subq_style
                    else:
                        label = f"{number}.  {q}"
                        style = question_style
                    row = table.row()
                    row.cell(label, style=style)
                    row.cell(a)
            else:
                table.row(["Aucune reponse", "-"])

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        pdf.output(file_path)

        logger.info(f"PDF saved at: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error in pdf_generator: {str(e)}")
        raise

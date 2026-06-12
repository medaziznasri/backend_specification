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
STRIPE = (245, 247, 250)


def _safe(text: str) -> str:
    """Core PDF fonts are Latin-1 only. Replace anything outside that range so
    generation never crashes on Arabic/emoji/other unsupported characters."""
    if text is None:
        return ""
    return str(text).encode("latin-1", "replace").decode("latin-1")


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

        rows = []
        for item in structured_answers:
            q = _safe(item.get("question", ""))
            a = _safe(_format_answer(item.get("answer", "")))
            rows.append((q, a))

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(*INK)
        headings_style = FontFace(emphasis="BOLD", color=(255, 255, 255), fill_color=PRIMARY)

        with pdf.table(
            width=pdf.epw,
            col_widths=(42, 58),
            text_align=("LEFT", "LEFT"),
            line_height=6,
            headings_style=headings_style,
            cell_fill_color=STRIPE,
            cell_fill_mode="ROWS",
            borders_layout="MINIMAL",
        ) as table:
            table.row(["Question", "Reponse"])  # repeats on each page automatically
            if rows:
                for q, a in rows:
                    table.row([q, a])
            else:
                table.row(["Aucune reponse", "-"])

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        pdf.output(file_path)

        logger.info(f"PDF saved at: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error in pdf_generator: {str(e)}")
        raise

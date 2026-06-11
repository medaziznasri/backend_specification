import os
import logging
from fpdf import FPDF
from datetime import datetime

logger = logging.getLogger(__name__)

UPLOAD_DIR = "storage/specifications"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def generate_physical_pdf(structured_answers, file_path, session_id, project_metadata=None):

    try:

        pdf = FPDF()
        pdf.add_page()
        

        pdf.set_font("Helvetica", 'B', 20)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 15, "Cahier des Charges Technique", ln=True, align='C')
        
        pdf.set_font("Helvetica", 'I', 10)
        pdf.set_text_color(127, 140, 141)
        pdf.cell(0, 10, f"ID Session: {session_id}", ln=True, align='C')
        pdf.cell(0, 5, f"Généré le: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
        pdf.ln(15)
        

        if project_metadata:
            pdf.set_font("Helvetica", 'B', 14)
            pdf.set_text_color(52, 73, 94)
            pdf.cell(0, 10, "Informations du Projet", ln=True)
            pdf.ln(2)
            

            pdf.set_font("Helvetica", 'B', 11)
            pdf.set_text_color(0, 0, 0)
            pdf.cell(40, 8, "Projet : ", ln=False)
            pdf.set_font("Helvetica", size=11)
            pdf.cell(0, 8, project_metadata.get("project_name", "N/A"), ln=True)
            

            pdf.set_font("Helvetica", 'B', 11)
            pdf.cell(40, 8, "Catégories : ", ln=False)
            pdf.set_font("Helvetica", size=11)
            
            categories = project_metadata.get("categories", [])
            categories_str = ", ".join(categories) if categories else "Aucune catégorie"
            pdf.multi_cell(0, 8, categories_str)
            pdf.ln(2)
            

            if project_metadata.get("project_description"):
                pdf.set_font("Helvetica", 'B', 11)
                pdf.cell(40, 8, "Description : ", ln=True)
                pdf.set_font("Helvetica", size=11)
                pdf.multi_cell(0, 8, project_metadata["project_description"])
            
            pdf.ln(10)
        

        pdf.set_font("Helvetica", size=11)
        pdf.set_text_color(0, 0, 0)

        def sanitize(val):
            if val is None:
                return "Non répondu"
            if isinstance(val, (list, dict)):
                import json
                val = json.dumps(val, ensure_ascii=False)
            s = str(val)

            s = s.replace('\\n', '\n')

            if s.startswith('"') and s.endswith('"'):
                s = s[1:-1]
            return s

        table_data = []
        for item in structured_answers:
            q = sanitize(item.get('question', ''))
            a = sanitize(item.get('answer', ''))
            table_data.append((q, a))

        with pdf.table(
            borders_layout="ALL",
            cell_fill_color=(255, 255, 255),
            cell_fill_mode="ALL",
            col_widths=(40, 60),
            line_height=pdf.font_size * 1.5,
            text_align=("LEFT", "LEFT"),
            width=pdf.epw,
        ) as table:

            pdf.set_font("Helvetica", 'B', 12)
            pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(0, 0, 0)
            header = table.row()
            header.cell("Question")
            header.cell("Réponses")
            

            pdf.set_font("Helvetica", size=11)
            pdf.set_text_color(0, 0, 0)
            for q, a in table_data:
                row = table.row()
                row.cell(q)
                row.cell(a)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        pdf.output(file_path)
        
        logger.info(f"PDF saved at: {file_path}")
        return True

    except Exception as e:
        logger.error(f"Error in pdf_generator: {str(e)}")
        raise
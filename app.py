import streamlit as st
from google import genai
from PIL import Image
import pypdf
from fpdf import FPDF

def clean_text_for_pdf(text):
    """Clean text for Latin-1 safe rendering without destroying structure."""
    text = text.replace('**', '').replace('##', '').replace('#', '')
    text = text.replace('?', '-').replace('"', '').replace('•', '-')
    return text.strip()

def generate_pdf_one_page(text_content):
    pdf = FPDF()
    pdf.add_page()
    
    # Standard A4 layout margins
    pdf.set_margins(15, 12, 15)
    pdf.set_auto_page_break(auto=True, margin=10)
    
    lines = text_content.split('\n')
    for line in lines:
        clean_line = clean_text_for_pdf(line)
        if not clean_line:
            pdf.ln(1.5)
            continue
            
        # Encode safely to latin-1 while keeping spanish characters like Ó, Á, É, Ñ
        try:
            safe_text = clean_line.encode('latin-1', 'replace').decode('latin-1')
        except Exception:
            safe_text = clean_line

        # Section Titles (Headers)
        if line.strip().startswith('#') or (clean_line.isupper() and len(clean_line) < 40):
            pdf.ln(3)
            pdf.set_font("Arial", 'B', size=11)
            pdf.multi_cell(0, 5, safe_text)
            pdf.ln(1)
        # Bullet points and body text
        elif clean_line.startswith('-'):
            pdf.set_font("Arial", size=9.5)
            pdf.multi_cell(0, 4.8, "  " + safe_text)
            pdf.ln(0.5)
        # Main text/sub-headers
        else:
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 5, safe_text)
            pdf.ln(1)
            
    return bytes(pdf.output())

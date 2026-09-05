def generate_pdf_one_page(text_content):
    pdf = FPDF()
    pdf.add_page()
    
    # Optimized margins to maximize printable area (10mm top/sides)
    pdf.set_margins(10, 8, 10)
    pdf.set_auto_page_break(auto=False)  # Strict 1-page layout
    
    lines = text_content.split('\n')
    for line in lines:
        clean_line = clean_text_for_pdf(line)
        if not clean_line:
            pdf.ln(1)
            continue
            
        try:
            safe_text = clean_line.encode('latin-1', 'replace').decode('latin-1')
        except Exception:
            safe_text = clean_line

        # Section Titles / Headers
        if line.strip().startswith('#') or (clean_line.isupper() and len(clean_line) < 40):
            pdf.ln(2)
            pdf.set_font("Arial", 'B', size=10.5)
            pdf.multi_cell(0, 4.5, safe_text)
            pdf.ln(0.8)
        # Bullet points
        elif clean_line.startswith('*') or clean_line.startswith('-'):
            pdf.set_font("Arial", size=9)
            pdf.multi_cell(0, 4.2, "  " + safe_text)
            pdf.ln(0.3)
        # Main text / Subheaders
        else:
            pdf.set_font("Arial", size=9.5)
            pdf.multi_cell(0, 4.5, safe_text)
            pdf.ln(0.5)
            
    return bytes(pdf.output())

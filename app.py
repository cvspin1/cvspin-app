def generate_pdf_one_page(text_content):
    pdf = FPDF()
    pdf.add_page()
    
    # Standard margins to keep clean borders
    pdf.set_margins(12, 10, 12)
    pdf.set_auto_page_break(auto=False)
    
    lines = text_content.split('\n')
    for line in lines:
        clean_line = clean_text_for_pdf(line)
        if not clean_line:
            pdf.ln(2.5) # تباعد متوازن بين الأقسام
            continue
            
        try:
            safe_text = clean_line.encode('latin-1', 'replace').decode('latin-1')
        except Exception:
            safe_text = clean_line

        # عناوين الأقسام (Section Titles)
        if line.strip().startswith('#') or (clean_line.isupper() and len(clean_line) < 40):
            pdf.ln(3)
            pdf.set_font("Arial", 'B', size=11)
            pdf.multi_cell(0, 5, safe_text)
            pdf.ln(1)
        # العوارض (Bullet points) باش يعمرو المساحة بلا ما ينقصو
        elif clean_line.startswith('*') or clean_line.startswith('-'):
            pdf.set_font("Arial", size=9)
            pdf.multi_cell(0, 4.5, "  " + safe_text)
            pdf.ln(0.5)
        # النص العادي
        else:
            pdf.set_font("Arial", size=9.5)
            pdf.multi_cell(0, 4.8, safe_text)
            pdf.ln(0.8)
            
    return bytes(pdf.output())

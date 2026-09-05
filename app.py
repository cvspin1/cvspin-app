import streamlit as st
from google import genai
from PIL import Image
import pypdf
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Page Configuration
st.set_page_config(
    page_title="CVSpin España 🇪🇸",
    page_icon="💼",
    layout="centered"
)

# Custom Styling (Hide Streamlit Branding)
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stButton>button {
        background-color: #0E1117;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: 1px solid #4B5563;
        width: 100%;
        padding: 10px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("CVSpin España 🇪🇸")
st.subheader("Generador Profesional de CV para el Mercado Español")

# Fetch API Key securely from Secrets
api_key = st.secrets.get("GEMINI_API_KEY")

def create_pdf(text):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    # Custom PDF Styles
    body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=6)
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, alignment=TA_CENTER, spaceAfter=12)
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontSize=13, leading=16, spaceBefore=10, spaceAfter=4)
    
    story = []
    lines = text.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('# '):
            clean_text = line.replace('# ', '').replace('*', '').strip()
            story.append(Paragraph(f"<b>{clean_text}</b>", title_style))
        elif line.startswith('### ') or line.startswith('## '):
            clean_text = line.replace('### ', '').replace('## ', '').replace('*', '').strip()
            story.append(Paragraph(f"<b>{clean_text}</b>", heading_style))
        else:
            clean_text = line.replace('**', '<b>').replace('**', '</b>')
            clean_text = clean_text.replace('*', '')
            story.append(Paragraph(clean_text, body_style))
            
    doc.build(story)
    buffer.seek(0)
    return buffer

# Mode Selection
option = st.radio(
    "Seleccione la opción de entrada / اختار طريقة إدخال البيانات:",
    ("1. Ingresar datos manualmente (إدخال يدوياً)", "2. Subir documento / foto del CV (PDF, PNG, JPG)")
)

if "1. Ingresar datos" in option:
    with st.form("cv_form_manual"):
        full_name = st.text_input("Nombre Completo")
        job_title = st.text_input("Puesto de Trabajo Objetivo en España")
        experience = st.text_area("Experiencia Laboral (Empresas, Fechas, Funciones)")
        education = st.text_area("Formación Académica y Certificaciones")
        skills = st.text_input("Habilidades, Idiomas y Carné de Conducir")
        
        submitted = st.form_submit_button("Generar CV Profesional ✨")

    if submitted:
        if not api_key:
            st.error("Error de configuración en el servidor. Falta la API Key en Secrets.")
        elif not full_name or not job_title:
            st.warning("Por favor, complete los campos obligatorios.")
        else:
            with st.spinner("Procesando y optimizando el CV..."):
                try:
                    client = genai.Client(api_key=api_key)
                    prompt_input = f"""
You are an expert ATS-optimized Resume Writer for the Spanish Job Market (CV Español).
Generate a professional Spanish CV based on these details:
- Full Name: {full_name}
- Target Job: {job_title}
- Experience: {experience}
- Education: {education}
- Skills/Languages: {skills}

FORMAT RULES:
- Spanish Language strictly.
- Professional Summary (Perfil Profesional).
- Experiencia Laboral (using Spanish ATS action verbs).
- Formación Académica.
- Habilidades e Idiomas.
"""
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=prompt_input,
                    )
                    
                    st.success("¡CV generado con éxito!")
                    st.markdown("---")
                    st.markdown(response.text)
                    
                    pdf_bytes = create_pdf(response.text)
                    
                    st.download_button(
                        label="📥 Descargar CV Profesional en PDF",
                        data=pdf_bytes,
                        file_name=f"CV_{full_name.replace(' ', '_')}.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Ocurrió un error: {e}")

else:
    uploaded_file = st.file_uploader(
        "Suba un archivo PDF o una imagen del CV (PDF, PNG, JPG, JPEG)", 
        type=["pdf", "png", "jpg", "jpeg"]
    )
    job_target_file = st.text_input("Puesto de Trabajo Objetivo en España (Opcional)")
    
    if uploaded_file is not None:
        if st.button("Extraer datos y Generar CV Optimizado ✨"):
            if not api_key:
                st.error("Error de configuración en el servidor. Falta la API Key en Secrets.")
            else:
                with st.spinner("Analizando el archivo y reescribiendo el CV para España..."):
                    try:
                        client = genai.Client(api_key=api_key)
                        
                        prompt_base = f"""
You are an expert ATS-optimized Resume Writer for the Spanish Job Market (CV Español).
Analyze the provided document/image of a CV and extract all relevant information (Name, Contact, Experience, Education, Skills).
Re-write and structure it into a brand new, highly professional Spanish CV optimized for ATS.
Target Job Title in Spain: {job_target_file if job_target_file else 'Same as extracted or professional role'}

FORMAT RULES:
- Spanish Language strictly.
- Professional Summary (Perfil Profesional).
- Experiencia Laboral (using Spanish ATS action verbs).
- Formación Académica.
- Habilidades e Idiomas.
"""

                        if uploaded_file.type == "application/pdf":
                            pdf_reader = pypdf.PdfReader(uploaded_file)
                            pdf_text = ""
                            for page in pdf_reader.pages:
                                text = page.extract_text()
                                if text:
                                    pdf_text += text + "\n"
                            
                            full_prompt = f"{prompt_base}\n\nHere is the extracted content from the PDF:\n{pdf_text}"
                            
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=full_prompt,
                            )
                        else:
                            image = Image.open(uploaded_file)
                            response = client.models.generate_content(
                                model='gemini-3.6-flash',
                                contents=[image, prompt_base],
                            )
                        
                        st.success("¡CV extraído y generado con éxito!")
                        st.markdown("---")
                        st.markdown(response.text)
                        
                        pdf_bytes = create_pdf(response.text)
                        
                        st.download_button(
                            label="📥 Descargar CV Profesional en PDF",
                            data=pdf_bytes,
                            file_name="CV_Optimizado_Espana.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"Ocurrió un error al procesar el archivo: {e}")

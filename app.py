import streamlit as st
from google import genai
from PIL import Image
import pypdf

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

def generate_with_fallback(client, contents):
    # Try models in order of stability and performance
    models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-2.0-flash']
    last_exception = None
    
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )
            return response
        except Exception as e:
            last_exception = e
            continue
            
    raise last_exception

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
                    response = generate_with_fallback(client, prompt_input)
                    
                    st.success("¡CV generado con éxito!")
                    st.markdown("---")
                    st.markdown(response.text)
                    
                    st.download_button(
                        label="📥 Descargar CV (.txt / Formato Documento)",
                        data=response.text,
                        file_name=f"CV_{full_name.replace(' ', '_')}.txt",
                        mime="text/plain"
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
                            response = generate_with_fallback(client, full_prompt)
                        else:
                            image = Image.open(uploaded_file)
                            response = generate_with_fallback(client, [image, prompt_base])
                        
                        st.success("¡CV extraído y generado con éxito!")
                        st.markdown("---")
                        st.markdown(response.text)
                        
                        st.download_button(
                            label="📥 Descargar CV (.txt / Formato Documento)",
                            data=response.text,
                            file_name="CV_Optimizado_Espana.txt",
                            mime="text/plain"
                        )
                    except Exception as e:
                        st.error(f"Ocurrió un error al procesar el archivo: {e}")

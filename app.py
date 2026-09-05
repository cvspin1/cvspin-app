import streamlit as st
from google import genai

# Page Configuration & Branding
st.set_page_config(page_title="Spain CV Builder", page_icon="📄")

# Your Brand Logo URL (You can replace this URL with your own logo link later)
st.image("https://via.placeholder.com/150x50.png?text=YOUR+LOGO", width=150)
st.title("Spain CV Generator 🇪🇸")
st.write("Enter client details to generate a professional, ATS-optimized Spanish CV instantly.")

# API Key Input Sidebar
api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

# Data Entry Form
with st.form("client_form"):
    full_name = st.text_input("Full Name")
    job_title = st.text_input("Target Job / Profession in Spain")
    experience = st.text_area("Work Experience (Companies, Duration, Tasks)")
    education = st.text_area("Education & Certifications")
    skills = st.text_input("Skills, Languages & Driving License")
    
    submitted = st.form_submit_button("Generate Spanish CV 🚀")

if submitted:
    if not api_key:
        st.error("Please enter your Gemini API Key first!")
    else:
        try:
            client = genai.Client(api_key=api_key)
            
            prompt = f"""
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
                model='gemini-2.5-flash',
                contents=prompt,
            )
            
            st.success("CV generated successfully!")
            st.markdown(response.text)
            
            # Download Button
            st.download_button("Download CV (TXT)", response.text, file_name=f"CV_{full_name}.txt")
            
        except Exception as e:
            st.error(f"An error occurred: {e}")

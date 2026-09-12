import streamlit as st
from google import genai
from PIL import Image
import pypdf
from fpdf import FPDF
import json
import re
import io


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="CVSpin España 🇪🇸",
    page_icon="💼",
    layout="centered"
)


# =========================================================
# CUSTOM UI
# =========================================================

st.markdown("""
<style>

#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header {
    visibility: hidden;
}

.stButton > button {
    background-color: #111827;
    color: white;
    font-weight: 700;
    border-radius: 8px;
    border: 1px solid #374151;
    width: 100%;
    padding: 11px;
}

.stDownloadButton > button {
    width: 100%;
    font-weight: 700;
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)


st.title("CVSpin España 🇪🇸")
st.caption("Generador profesional de CV para el mercado español")


# =========================================================
# API KEY
# =========================================================

api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.warning(
        "La API Key no está configurada. "
        "Añade GEMINI_API_KEY en Streamlit Secrets."
    )


# =========================================================
# GEMINI MODEL
# =========================================================

def get_client():
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")

    return genai.Client(api_key=api_key)


def call_gemini(client, contents):

    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash"
    ]

    last_error = None

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents
            )

            if response and response.text:
                return response

        except Exception as e:
            last_error = e

    if last_error:
        raise last_error

    raise RuntimeError("No Gemini model was available.")


# =========================================================
# AI PROMPT
# =========================================================

STRICT_SPANISH_CV_PROMPT = """
YOU ARE AN EXPERT SPANISH CV FORMATTER AND RECRUITMENT SPECIALIST.

Your ONLY task is to organize the information supplied by the user
into a clean professional CV structure suitable for the Spanish job market.

IMPORTANT:

1. DO NOT INVENT INFORMATION.
2. DO NOT CREATE FAKE JOBS.
3. DO NOT CREATE FAKE EDUCATION.
4. DO NOT CREATE FAKE CERTIFICATIONS.
5. DO NOT CREATE FAKE DATES.
6. DO NOT CREATE FAKE SKILLS.
7. DO NOT CHANGE facts supplied by the user.
8. Preserve the user's information as faithfully as possible.
9. You may correct obvious formatting problems and organize the information.
10. Do not add achievements unless they already exist in the input.
11. Do not add a photo.
12. Do not add nationality unless supplied.
13. Do not add date of birth unless supplied.
14. Do not add marital status.
15. Do not add unnecessary personal information.

TARGET FORMAT:

- Name
- Target professional title
- Location
- Phone
- Email
- LinkedIn
- Professional Profile
- Professional Experience
- Education
- Certifications
- Technical Skills
- Languages
- Driving Licence / Additional Information if supplied

SPANISH LANGUAGE RULE:

If the information is written in another language, translate it into
professional Spanish while preserving its meaning.

IMPORTANT:

Return ONLY valid JSON.

Do NOT use Markdown.
Do NOT use ```json.
Do NOT add explanations before or after the JSON.

Use exactly this JSON structure:

{
  "name": "",
  "title": "",
  "location": "",
  "phone": "",
  "email": "",
  "linkedin": "",
  "profile": "",
  "experience": [
    {
      "position": "",
      "company": "",
      "location": "",
      "start_date": "",
      "end_date": "",
      "bullets": []
    }
  ],
  "education": [
    {
      "degree": "",
      "institution": "",
      "date": "",
      "location": ""
    }
  ],
  "certifications": [],
  "skills": [],
  "languages": [
    {
      "language": "",
      "level": ""
    }
  ],
  "additional": []
}
"""


# =========================================================
# JSON CLEANING
# =========================================================

def extract_json(text):

    if not text:
        raise ValueError("Gemini returned an empty response.")

    text = text.strip()

    # Remove markdown fences if Gemini accidentally adds them
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    # Find first { and last }
    first = text.find("{")
    last = text.rfind("}")

    if first == -1 or last == -1:
        raise ValueError("Could not find valid JSON in Gemini response.")

    text = text[first:last + 1]

    try:
        return json.loads(text)

    except json.JSONDecodeError as e:
        raise ValueError(
            f"Gemini returned invalid JSON: {e}"
        )


# =========================================================
# SAFE HELPERS
# =========================================================

def safe(value):
    if value is None:
        return ""
    return str(value).strip()


def get_list(data, key):
    value = data.get(key, [])

    if not isinstance(value, list):
        return []

    return value


# =========================================================
# PDF CLASS
# =========================================================

class SpanishCV(FPDF):

    def __init__(self, font_size=9.2):
        super().__init__(
            orientation="P",
            unit="mm",
            format="A4"
        )

        self.font_size = font_size

        self.set_margins(
            left=13,
            top=11,
            right=13
        )

        self.set_auto_page_break(
            auto=False
        )

        self.add_page()

        # Unicode-capable font if available.
        # Fallback to Arial if DejaVu is not available.
        try:
            self.add_font(
                "DejaVu",
                "",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            )

            self.add_font(
                "DejaVu",
                "B",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            )

            self.font_regular = "DejaVu"
            self.font_bold = "DejaVu"

        except Exception:

            self.font_regular = "Arial"
            self.font_bold = "Arial"

        self.set_text_color(25, 25, 25)


# =========================================================
# PDF TEXT FUNCTIONS
# =========================================================

def section_title(pdf, title):

    pdf.ln(2)

    pdf.set_font(
        pdf.font_bold,
        "B",
        10
    )

    pdf.set_text_color(
        20,
        20,
        20
    )

    pdf.cell(
        0,
        5,
        title.upper()
    )

    pdf.ln(1)

    # Small separator
    pdf.set_draw_color(
        190,
        190,
        190
    )

    pdf.line(
        pdf.l_margin,
        pdf.get_y(),
        pdf.w - pdf.r_margin,
        pdf.get_y()
    )

    pdf.ln(2)


def normal_text(pdf, text, size=None):

    text = safe(text)

    if not text:
        return

    if size is None:
        size = pdf.font_size

    pdf.set_font(
        pdf.font_regular,
        "",
        size
    )

    pdf.set_text_color(
        40,
        40,
        40
    )

    pdf.multi_cell(
        0,
        4.1,
        text
    )

    pdf.ln(0.7)


def bullet(pdf, text, size=None):

    text = safe(text)

    if not text:
        return

    if size is None:
        size = 8.5

    pdf.set_font(
        pdf.font_regular,
        "",
        size
    )

    pdf.set_text_color(
        45,
        45,
        45
    )

    x = pdf.get_x()

    pdf.cell(
        4,
        4,
        "-"
    )

    pdf.multi_cell(
        0,
        4,
        text
    )

    pdf.set_x(x)

    pdf.ln(0.4)


# =========================================================
# HEADER
# =========================================================

def render_header(pdf, data):

    name = safe(data.get("name"))
    title = safe(data.get("title"))

    pdf.set_font(
        pdf.font_bold,
        "B",
        20
    )

    pdf.set_text_color(
        15,
        15,
        15
    )

    pdf.cell(
        0,
        8,
        name
    )

    pdf.ln(7)

    if title:

        pdf.set_font(
            pdf.font_regular,
            "",
            11
        )

        pdf.set_text_color(
            75,
            75,
            75
        )

        pdf.cell(
            0,
            5,
            title
        )

        pdf.ln(6)

    contact_parts = []

    for key in [
        "location",
        "phone",
        "email",
        "linkedin"
    ]:

        value = safe(data.get(key))

        if value:
            contact_parts.append(value)

    if contact_parts:

        contact_text = "  |  ".join(contact_parts)

        pdf.set_font(
            pdf.font_regular,
            "",
            8
        )

        pdf.set_text_color(
            80,
            80,
            80
        )

        pdf.multi_cell(
            0,
            4,
            contact_text
        )

        pdf.ln(2)


# =========================================================
# PROFILE
# =========================================================

def render_profile(pdf, data):

    profile = safe(
        data.get("profile")
    )

    if not profile:
        return

    section_title(
        pdf,
        "Perfil profesional"
    )

    normal_text(
        pdf,
        profile,
        8.8
    )


# =========================================================
# EXPERIENCE
# =========================================================

def render_experience(pdf, data):

    experiences = get_list(
        data,
        "experience"
    )

    if not experiences:
        return

    section_title(
        pdf,
        "Experiencia profesional"
    )

    for exp in experiences:

        if not isinstance(exp, dict):
            continue

        position = safe(
            exp.get("position")
        )

        company = safe(
            exp.get("company")
        )

        location = safe(
            exp.get("location")
        )

        start = safe(
            exp.get("start_date")
        )

        end = safe(
            exp.get("end_date")
        )

        dates = ""

        if start and end:
            dates = f"{start} – {end}"

        elif start:
            dates = start

        elif end:
            dates = end

        # Position
        if position:

            pdf.set_font(
                pdf.font_bold,
                "B",
                9.2
            )

            pdf.set_text_color(
                20,
                20,
                20
            )

            pdf.multi_cell(
                0,
                4.2,
                position
            )

        # Company / dates
        meta_parts = []

        if company:
            meta_parts.append(company)

        if location:
            meta_parts.append(location)

        if dates:
            meta_parts.append(dates)

        if meta_parts:

            pdf.set_font(
                pdf.font_regular,
                "",
                8.2
            )

            pdf.set_text_color(
                95,
                95,
                95
            )

            pdf.multi_cell(
                0,
                3.8,
                " | ".join(meta_parts)
            )

        bullets = exp.get(
            "bullets",
            []
        )

        if isinstance(bullets, list):

            for item in bullets:

                bullet(
                    pdf,
                    item,
                    8.2
                )

        pdf.ln(1)


# =========================================================
# EDUCATION
# =========================================================

def render_education(pdf, data):

    education = get_list(
        data,
        "education"
    )

    if not education:
        return

    section_title(
        pdf,
        "Educación"
    )

    for edu in education:

        if not isinstance(edu, dict):
            continue

        degree = safe(
            edu.get("degree")
        )

        institution = safe(
            edu.get("institution")
        )

        date = safe(
            edu.get("date")
        )

        location = safe(
            edu.get("location")
        )

        if degree:

            pdf.set_font(
                pdf.font_bold,
                "B",
                8.8
            )

            pdf.set_text_color(
                30,
                30,
                30
            )

            pdf.multi_cell(
                0,
                4,
                degree
            )

        meta = []

        if institution:
            meta.append(institution)

        if location:
            meta.append(location)

        if date:
            meta.append(date)

        if meta:

            pdf.set_font(
                pdf.font_regular,
                "",
                8.1
            )

            pdf.set_text_color(
                90,
                90,
                90
            )

            pdf.multi_cell(
                0,
                3.7,
                " | ".join(meta)
            )

        pdf.ln(1)


# =========================================================
# SKILLS
# =========================================================

def render_skills(pdf, data):

    skills = get_list(
        data,
        "skills"
    )

    certifications = get_list(
        data,
        "certifications"
    )

    additional = get_list(
        data,
        "additional"
    )

    if not skills and not certifications and not additional:
        return

    section_title(
        pdf,
        "Competencias y certificaciones"
    )

    if skills:

        skills_text = " • ".join(
            safe(x)
            for x in skills
            if safe(x)
        )

        normal_text(
            pdf,
            skills_text,
            8.2
        )

    if certifications:

        pdf.set_font(
            pdf.font_bold,
            "B",
            8.4
        )

        pdf.cell(
            0,
            4,
            "Certificaciones"
        )

        pdf.ln(4)

        for cert in certifications:

            bullet(
                pdf,
                cert,
                8
            )

    if additional:

        pdf.set_font(
            pdf.font_bold,
            "B",
            8.4
        )

        pdf.cell(
            0,
            4,
            "Información adicional"
        )

        pdf.ln(4)

        for item in additional:

            bullet(
                pdf,
                item,
                8
            )


# =========================================================
# LANGUAGES
# =========================================================

def render_languages(pdf, data):

    languages = get_list(
        data,
        "languages"
    )

    if not languages:
        return

    section_title(
        pdf,
        "Idiomas"
    )

    language_parts = []

    for lang in languages:

        if not isinstance(lang, dict):
            continue

        name = safe(
            lang.get("language")
        )

        level = safe(
            lang.get("level")
        )

        if name and level:
            language_parts.append(
                f"{name}: {level}"
            )

        elif name:
            language_parts.append(
                name
            )

    if language_parts:

        normal_text(
            pdf,
            " • ".join(language_parts),
            8.2
        )


# =========================================================
# BUILD PDF
# =========================================================

def build_pdf(data, font_size=9.2):

    pdf = SpanishCV(
        font_size=font_size
    )

    render_header(
        pdf,
        data
    )

    render_profile(
        pdf,
        data
    )

    render_experience(
        pdf,
        data
    )

    render_education(
        pdf,
        data
    )

    render_skills(
        pdf,
        data
    )

    render_languages(
        pdf,
        data
    )

    # Footer
    pdf.set_y(
        286
    )

    pdf.set_font(
        pdf.font_regular,
        "",
        6.5
    )

    pdf.set_text_color(
        150,
        150,
        150
    )

    pdf.cell(
        0,
        3,
        "CVSpin España",
        align="C"
    )

    return bytes(
        pdf.output()
    )


# =========================================================
# AUTOMATIC ONE-PAGE FIT
# =========================================================

def generate_fitted_pdf(data):

    # First attempt
    sizes = [
        9.2,
        8.9,
        8.6,
        8.3,
        8.0
    ]

    last_pdf = None

    for size in sizes:

        pdf_bytes = build_pdf(
            data,
            font_size=size
        )

        # FPDF produces exactly one page because
        # auto page break is disabled.
        # We additionally inspect the PDF page count.
        try:

            reader = pypdf.PdfReader(
                io.BytesIO(pdf_bytes)
            )

            pages = len(reader.pages)

            if pages <= 1:
                return pdf_bytes

        except Exception:
            pass

        last_pdf = pdf_bytes

    return last_pdf


# =========================================================
# INPUT NORMALIZATION
# =========================================================

def prepare_manual_input(
    full_name,
    job_title,
    experience,
    education,
    skills
):

    return f"""
USER INFORMATION:

Name:
{full_name}

Target Job:
{job_title}

Professional Experience:
{experience}

Education and Certifications:
{education}

Skills, Languages and Driving Licence:
{skills}
"""


# =========================================================
# DISPLAY PREVIEW
# =========================================================

def display_cv_preview(data):

    st.markdown("---")

    st.markdown(
        f"### {safe(data.get('name'))}"
    )

    if safe(data.get("title")):
        st.caption(
            safe(data.get("title"))
        )

    contact = []

    for key in [
        "location",
        "phone",
        "email",
        "linkedin"
    ]:

        value = safe(
            data.get(key)
        )

        if value:
            contact.append(value)

    if contact:
        st.caption(
            " | ".join(contact)
        )

    if safe(data.get("profile")):

        st.markdown(
            "#### Perfil profesional"
        )

        st.write(
            safe(data.get("profile"))
        )

    experiences = get_list(
        data,
        "experience"
    )

    if experiences:

        st.markdown(
            "#### Experiencia profesional"
        )

        for exp in experiences:

            if not isinstance(exp, dict):
                continue

            st.markdown(
                f"**{safe(exp.get('position'))}**"
            )

            meta = []

            for key in [
                "company",
                "location",
                "start_date",
                "end_date"
            ]:

                value = safe(
                    exp.get(key)
                )

                if value:
                    meta.append(value)

            if meta:
                st.caption(
                    " | ".join(meta)
                )

            bullets = exp.get(
                "bullets",
                []
            )

            if isinstance(bullets, list):

                for b in bullets:

                    if safe(b):
                        st.markdown(
                            f"- {safe(b)}"
                        )


# =========================================================
# APP
# =========================================================

option = st.radio(
    "Seleccione la opción de entrada / اختار طريقة إدخال البيانات:",
    (
        "1. Ingresar datos manualmente (إدخال يدوياً)",
        "2. Subir documento / foto del CV (PDF, PNG, JPG)"
    )
)


# =========================================================
# MANUAL MODE
# =========================================================

if option.startswith("1."):

    with st.form(
        "cv_form_manual"
    ):

        full_name = st.text_input(
            "Nombre Completo"
        )

        job_title = st.text_input(
            "Puesto de Trabajo Objetivo en España"
        )

        experience = st.text_area(
            "Experiencia Laboral (Empresas, Fechas, Funciones)",
            height=180
        )

        education = st.text_area(
            "Formación Académica y Certificaciones",
            height=120
        )

        skills = st.text_area(
            "Habilidades, Idiomas y Carné de Conducir",
            height=100
        )

        submitted = st.form_submit_button(
            "Generar CV Profesional ✨"
        )

    if submitted:

        if not api_key:

            st.error(
                "Error de configuración: falta GEMINI_API_KEY."
            )

        elif not full_name or not job_title:

            st.warning(
                "Por favor, complete Nombre y Puesto Objetivo."
            )

        else:

            with st.spinner(
                "Organizando el CV según el formato profesional español..."
            ):

                try:

                    client = get_client()

                    user_input = prepare_manual_input(
                        full_name,
                        job_title,
                        experience,
                        education,
                        skills
                    )

                    prompt = (
                        STRICT_SPANISH_CV_PROMPT
                        + "\n\n"
                        + user_input
                    )

                    response = call_gemini(
                        client,
                        prompt
                    )

                    cv_data = extract_json(
                        response.text
                    )

                    pdf_bytes = generate_fitted_pdf(
                        cv_data
                    )

                    st.success(
                        "CV generado correctamente."
                    )

                    display_cv_preview(
                        cv_data
                    )

                    st.download_button(
                        label="📥 Descargar CV en PDF",
                        data=pdf_bytes,
                        file_name=(
                            f"CV_{full_name.replace(' ', '_')}"
                            "_Espana.pdf"
                        ),
                        mime="application/pdf"
                    )

                except Exception as e:

                    st.error(
                        f"Ocurrió un error: {e}"
                    )


# =========================================================
# FILE MODE
# =========================================================

else:

    uploaded_file = st.file_uploader(
        "Suba un archivo PDF o una imagen del CV",
        type=[
            "pdf",
            "png",
            "jpg",
            "jpeg"
        ]
    )

    job_target_file = st.text_input(
        "Puesto de Trabajo Objetivo en España (Opcional)"
    )

    if uploaded_file is not None:

        if st.button(
            "Extraer datos y Generar CV Optimizado ✨"
        ):

            if not api_key:

                st.error(
                    "Error de configuración: falta GEMINI_API_KEY."
                )

            else:

                with st.spinner(
                    "Analizando el CV y organizando la información..."
                ):

                    try:

                        client = get_client()

                        target = (
                            job_target_file
                            if job_target_file
                            else
                            "No especificado"
                        )

                        prompt_base = f"""
{STRICT_SPANISH_CV_PROMPT}

TARGET JOB IN SPAIN:
{target}
"""

                        # =====================================
                        # PDF INPUT
                        # =====================================

                        if uploaded_file.type == "application/pdf":

                            pdf_reader = pypdf.PdfReader(
                                uploaded_file
                            )

                            pdf_text = ""

                            for page in pdf_reader.pages:

                                text = page.extract_text()

                                if text:

                                    pdf_text += (
                                        text + "\n"
                                    )

                            if not pdf_text.strip():

                                st.warning(
                                    "No se pudo extraer texto del PDF. "
                                    "Si es un PDF escaneado, súbelo como imagen."
                                )

                            full_prompt = f"""
{prompt_base}

ORIGINAL CV CONTENT:

{pdf_text}
"""

                            response = call_gemini(
                                client,
                                full_prompt
                            )

                        # =====================================
                        # IMAGE INPUT
                        # =====================================

                        else:

                            image = Image.open(
                                uploaded_file
                            )

                            response = call_gemini(
                                client,
                                [
                                    image,
                                    prompt_base
                                ]
                            )

                        cv_data = extract_json(
                            response.text
                        )

                        pdf_bytes = generate_fitted_pdf(
                            cv_data
                        )

                        st.success(
                            "CV optimizado correctamente."
                        )

                        display_cv_preview(
                            cv_data
                        )

                        filename_name = safe(
                            cv_data.get("name")
                        )

                        if not filename_name:
                            filename_name = "CV"

                        st.download_button(
                            label="📥 Descargar CV en PDF",
                            data=pdf_bytes,
                            file_name=(
                                filename_name.replace(" ", "_")
                                + "_Espana.pdf"
                            ),
                            mime="application/pdf"
                        )

                    except Exception as e:

                        st.error(
                            f"Ocurrió un error al procesar el archivo: {e}"
                        )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "CVSpin España • CV formatting and optimization tool"
)

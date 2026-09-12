#def call_gemini(client, contents):
    # Modelos actualizados
    models_to_try = ["gemini-3.6-flash", "gemini-2.5-flash"]
    last_error = None

    config = types.GenerateContentConfig(
        response_mime_type="application/json"
    )

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            if response and response.text:
                return response
        except Exception as e:
            last_error = e

    if last_error:
        raise last_error

    raise RuntimeError("No Gemini model was available.")st.markdown(f"**{safe(exp.get('position'))}**")
                meta = [safe(exp.get(k)) for k in ["company", "location", "start_date", "end_date"] if safe(exp.get(k))]
                if meta:
                    st.caption(" | ".join(meta))
                for b in get_list(exp, "bullets"):
                    if safe(b):
                        st.markdown(f"- {safe(b)}")

option = st.radio(
    "Seleccione la opción de entrada / اختار طريقة إدخال البيانات:",
    ("1. Ingresar datos manualmente (إدخال يدوياً)", "2. Subir documento / foto del CV (PDF, PNG, JPG)")
)

if option.startswith("1."):
    with st.form("cv_form_manual"):
        full_name = st.text_input("Nombre Completo")
        job_title = st.text_input("Puesto de Trabajo Objetivo en España")
        experience = st.text_area("Experiencia Laboral (Empresas, Fechas, Funciones)", height=180)
        education = st.text_area("Formación Académica y Certificaciones", height=120)
        skills = st.text_area("Habilidades, Idiomas y Carné de Conducir", height=100)
        submitted = st.form_submit_button("Generar CV Profesional ✨")

    if submitted:
        if not api_key:
            st.error("Error de configuración: falta GEMINI_API_KEY.")
        elif not full_name or not job_title:
            st.warning("Por favor, complete Nombre y Puesto Objetivo.")
        else:
            with st.spinner("Organizando el CV según el formato profesional español..."):
                try:
                    client = get_client()
                    user_input = prepare_manual_input(full_name, job_title, experience, education, skills)
                    prompt = STRICT_SPANISH_CV_PROMPT + "\n\n" + user_input
                    
                    response = call_gemini(client, prompt)
                    cv_data = extract_json(response.text)
                    pdf_bytes = generate_fitted_pdf(cv_data)

                    st.success("CV generado correctamente.")
                    display_cv_preview(cv_data)
                    st.download_button(
                        label="📥 Descargar CV en PDF",
                        data=pdf_bytes,
                        file_name=f"CV_{full_name.replace(' ', '_')}_Espana.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Ocurrió un error: {e}")
else:
    uploaded_file = st.file_uploader("Suba un archivo PDF o una imagen del CV", type=["pdf", "png", "jpg", "jpeg"])
    job_target_file = st.text_input("Puesto de Trabajo Objetivo en España (Opcional)")

    if uploaded_file is not None and st.button("Extraer datos y Generar CV Optimizado ✨"):
        if not api_key:
            st.error("Error de configuración: falta GEMINI_API_KEY.")
        else:
            with st.spinner("Analizando el CV y organizando la información..."):
                try:
                    client = get_client()
                    target = job_target_file if job_target_file else "No especificado"
                    prompt_base = f"{STRICT_SPANISH_CV_PROMPT}\n\nTARGET JOB IN SPAIN:\n{target}"

                    if uploaded_file.type == "application/pdf":
                        pdf_reader = pypdf.PdfReader(uploaded_file)
                        pdf_text = "".join([page.extract_text() or "" for page in pdf_reader.pages])
                        if not pdf_text.strip():
                            st.warning("No se pudo extraer texto del PDF. Si es escaneado, súbelo como imagen.")
                        
                        full_prompt = f"{prompt_base}\n\nORIGINAL CV CONTENT:\n{pdf_text}"
                        response = call_gemini(client, full_prompt)
                    else:
                        image = Image.open(uploaded_file)
                        response = call_gemini(client, [image, prompt_base])

                    cv_data = extract_json(response.text)
                    pdf_bytes = generate_fitted_pdf(cv_data)

                    st.success("CV optimizado correctamente.")
                    display_cv_preview(cv_data)

                    filename_name = safe(cv_data.get("name")) or "CV"
                    st.download_button(
                        label="📥 Descargar CV en PDF",
                        data=pdf_bytes,
                        file_name=f"{filename_name.replace(' ', '_')}_Espana.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Ocurrió un error al procesar el archivo: {e}")

st.markdown("---")
st.caption("CVSpin España • CV formatting and optimization tool")

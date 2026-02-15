import streamlit as st
from google import genai
from google.genai import types
import PIL.Image
from io import BytesIO

# Configuración de página
st.set_page_config(page_title="Image Gen DeMos + Prompt Improver", layout="wide", page_icon="🏗️")

# --- ESTADOS DE SESIÓN ---
if "referencias" not in st.session_state:
    st.session_state.referencias = [] 
if "historial" not in st.session_state:
    st.session_state.historial = []
# Estado para guardar el prompt y permitir su edición
if "prompt_actual" not in st.session_state:
    st.session_state.prompt_actual = ""

# --- SEGURIDAD ---
PASSWORD_ACCESO = "archviz2026"

def check_password():
    if "authenticated" not in st.session_state:
        st.sidebar.title("Acceso")
        pwd = st.sidebar.text_input("Contraseña", type="password")
        if st.sidebar.button("Entrar"):
            if pwd == PASSWORD_ACCESO:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.sidebar.error("Incorrecta")
        return False
    return True

if check_password():
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

    st.title("Image Gen DeMos")
    st.caption("ArchViz Specialized | Nano Banana Series + Ultimate Prompt Engine")

    # --- SIDEBAR: CONFIGURACIÓN ---
    with st.sidebar:
        st.header("Ajustes Técnicos")
        modelo_nombre = st.selectbox("Motor de Render", [
            "Nano Banana Pro (Gemini 3 Pro Image)",
            "Nano Banana (Gemini 2.5 Flash Image)"
        ])
        
        model_map = {
            "Nano Banana Pro (Gemini 3 Pro Image)": "gemini-3-pro-image-preview",
            "Nano Banana (Gemini 2.5 Flash Image)": "gemini-2.5-flash-image"
        }
        
        aspect_ratio = st.selectbox("Formato (Aspect Ratio)", 
                                   ["16:9", "1:1", "9:16", "3:2", "2:3", "4:5", "5:4", "4:3", "3:4"])
        
        # Nota: Esto es simulado en Gemini Image por ahora, pero lo mantenemos para el prompt
        upscale_option = st.select_slider("Resolución Objetivo", options=["Nativo", "2K", "3K", "4K"])

    # --- BIBLIOTECA DE REFERENCIAS ---
    st.subheader("1. Contexto Visual (Referencias)")
    
    uploaded_files = st.file_uploader("Arrastra imágenes de referencia", 
                                     type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if uploaded_files:
        for f in uploaded_files:
            img = PIL.Image.open(f)
            if not any(d['name'] == f.name for d in st.session_state.referencias):
                st.session_state.referencias.append({"img": img, "name": f.name})

    if st.session_state.referencias:
        cols = st.columns(6)
        refs_activas = []
        for i, ref in enumerate(st.session_state.referencias):
            with cols[i % 6]:
                st.image(ref["img"], use_container_width=True)
                if st.checkbox(f"Usar", key=f"check_{ref['name']}"):
                    refs_activas.append(ref["img"])
        if st.button("Limpiar Biblioteca"):
            st.session_state.referencias = []
            st.rerun()
    else:
        refs_activas = [] # Lista vacía si no hay nada

    st.divider()

    # --- ÁREA DE PROMPT IMPROVER (INTEGRACIÓN NUEVA) ---
    st.subheader("2. Composición del Prompt")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("**Idea Base**")
        prompt_input = st.text_area("Describe tu idea brevemente:", 
                                  height=150,
                                  placeholder="Ej: Casa moderna de hormigón en el bosque, lluvia...",
                                  key="input_base")
        
        # Lógica del Prompt Improver
        if st.button("🪄 Mejorar con Estructura Ultimate"):
            if prompt_input:
                with st.spinner("Consultando base de conocimientos de estilos..."):
                    try:
                        # Usamos Gemini Flash (rápido) para simular la estructura JSON del repositorio
                        sistema_prompt = """
                        Act as an expert Prompt Engineer utilizing the 'Ultimate AI Prompt Generator' structure.
                        Analyze the user's request and rewrite it into a single, cohesive, comma-separated prompt following this specific order:
                        
                        1. **Subject**: Refine the core subject.
                        2. **Medium**: (e.g., Professional Architectural Photography, 3D Render).
                        3. **Style**: (e.g., Brutalist, Minimalist, Contemporary).
                        4. **Lighting**: (e.g., Golden hour, Volumetric lighting, Soft overcast).
                        5. **Color**: (e.g., Earthy tones, Cool palette, High contrast).
                        6. **Materials/Texture**: (e.g., Raw concrete, Travertine, Glass).
                        7. **Technical**: (e.g., 8k, Unreal Engine 5, Octane Render, Ray Tracing, Wide angle lens).
                        
                        Output ONLY the final English prompt. No explanations.
                        """
                        
                        response_improver = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=f"{sistema_prompt}\n\nUSER INPUT: {prompt_input}"
                        )
                        
                        # Actualizamos el estado para que aparezca en la columna derecha
                        st.session_state.prompt_actual = response_improver.text.strip()
                        st.rerun() # Recargamos para mostrar el resultado
                    except Exception as e:
                        st.error(f"Error al mejorar prompt: {e}")
            else:
                st.warning("Escribe una idea base primero.")

    with col2:
        st.markdown("**Prompt Final (Editable)**")
        # Este es el prompt que finalmente se usará. El usuario puede tocarlo.
        # El value viene del session_state para persistir la mejora de la AI
        prompt_final_usuario = st.text_area("Revisa y ajusta antes de generar:", 
                                            value=st.session_state.prompt_actual,
                                            height=150,
                                            key="txt_final")
        
        # Actualizamos el estado si el usuario edita manualmente
        if prompt_final_usuario != st.session_state.prompt_actual:
            st.session_state.prompt_actual = prompt_final_usuario

    # --- BOTÓN DE GENERACIÓN ---
    st.divider()
    
    # Inyectamos el formato y la resolución en el prompt técnico
    prompt_tecnico_completo = f"{prompt_final_usuario}, aspect ratio {aspect_ratio}, detailed output {upscale_option}"

    if st.button("Generar Visualización ✨", type="primary"):
        if prompt_final_usuario:
            with st.status("Renderizando...", expanded=False) as status:
                try:
                    # Construcción de la solicitud Multimodal
                    contenido_solicitud = [prompt_tecnico_completo] + refs_activas

                    st.write(f"Invocando {modelo_nombre}...")
                    
                    response = client.models.generate_content(
                        model=model_map[modelo_nombre],
                        contents=contenido_solicitud,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"]
                        )
                    )

                    # Validación de respuesta
                    if response and response.parts:
                        resultado = None
                        for part in response.parts:
                            if part.inline_data:
                                resultado = PIL.Image.open(BytesIO(part.inline_data.data))
                                break
                        
                        if resultado:
                            # Guardar en historial
                            st.session_state.historial.insert(0, resultado)
                            if len(st.session_state.historial) > 5:
                                st.session_state.historial.pop()

                            st.subheader("Resultado")
                            st.image(resultado, use_container_width=True, caption=f"Prompt: {prompt_final_usuario[:50]}...")
                            status.update(label="Generación exitosa", state="complete")
                        else:
                            st.error("El modelo no devolvió una imagen válida.")
                    else:
                        st.error("La API no devolvió contenido (Posible filtro de seguridad).")

                except Exception as e:
                    st.error(f"Error detectado: {e}")
        else:
            st.warning("El campo de Prompt Final está vacío. Usa el mejorador o escribe algo.")

    # --- HISTORIAL ---
    if st.session_state.historial:
        st.divider()
        st.subheader("Historial Reciente")
        h_cols = st.columns(5)
        for i, h_img in enumerate(st.session_state.historial):
            with h_cols[i]:
                st.image(h_img, use_container_width=True)
                buf = BytesIO()
                h_img.save(buf, format="JPEG")
                st.download_button(f"Descargar", buf.getvalue(), f"archviz_{i}.jpg", "image/jpeg", key=f"dl_{i}")

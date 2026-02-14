import streamlit as st
from google import genai
from google.genai import types
import PIL.Image
from io import BytesIO

# Configuración de página
st.set_page_config(page_title="Image Gen DeMos", layout="wide")

# --- ESTADOS DE SESIÓN ---
if "referencias" not in st.session_state:
    st.session_state.referencias = [] # Lista de diccionarios {"img": PIL, "name": str}
if "historial" not in st.session_state:
    st.session_state.historial = []

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
    st.caption("ArchViz Specialized | Nano Banana Series")

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
                                   ["1:1", "16:9", "9:16", "3:2", "2:3", "4:5", "5:4", "4:3", "3:4"])
        
        upscale_option = st.select_slider("Resolución de Salida", options=["Nativo", "2K", "3K", "4K"])

    # --- BIBLIOTECA DE REFERENCIAS (CON MINIATURAS) ---
    st.subheader("Biblioteca de Referencias")
    
    # Subida de archivos
    uploaded_files = st.file_uploader("Arrastra imágenes aquí para usarlas como contexto (Opcional)", 
                                     type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if uploaded_files:
        for f in uploaded_files:
            img = PIL.Image.open(f)
            # Evitar duplicados por nombre
            if not any(d['name'] == f.name for d in st.session_state.referencias):
                st.session_state.referencias.append({"img": img, "name": f.name})

    # Mostrar galería de miniaturas
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
        st.info("No hay referencias cargadas. Puedes generar solo con texto.")

    # --- ÁREA DE PROMPT Y GENERACIÓN ---
    st.divider()
    prompt_usuario = st.text_area("Descripción ArchViz", placeholder="Ej: Minimalist villa interior, travertine walls, floor to ceiling windows, soft morning light...")

    if st.button("Generar Visualización ✨"):
        if prompt_usuario:
            with st.status("Procesando...", expanded=False) as status:
                try:
                    # 1. Optimización interna con Gemini 3 Pro (Texto)
                    st.write("Refinando prompt arquitectónico...")
                    res_text = client.models.generate_content(
                        model="gemini-3-pro-preview",
                        contents=f"Improve this ArchViz prompt with technical details (lighting, materials, camera): {prompt_usuario}"
                    )
                    prompt_final = res_text.text if res_text.text else prompt_usuario

                    # 2. Construcción de la solicitud Multimodal
                    # Combinamos texto + lista de imágenes seleccionadas
                    contenido_solicitud = [prompt_final] + refs_activas

                    # 3. Llamada al modelo Nano Banana
                    st.write(f"Invocando {modelo_nombre}...")
                    response = client.models.generate_content(
                        model=model_map[modelo_nombre],
                        contents=contenido_solicitud,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"]
                        )
                    )

                    # Validación de respuesta para evitar el 'NoneType' error
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
                            st.image(resultado, use_container_width=True, caption=f"Renderizado en {upscale_option}")
                            status.update(label="Generación exitosa", state="complete")
                        else:
                            st.error("El modelo no devolvió una imagen válida. Intenta ajustar el prompt.")
                    else:
                        st.error("La API no devolvió contenido. Puede ser un bloqueo de seguridad por el prompt.")

                except Exception as e:
                    st.error(f"Error detectado: {e}")
        else:
            st.warning("Escribe una descripción.")

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

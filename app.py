import streamlit as st
from google import genai
from google.genai import types
import PIL.Image
from io import BytesIO

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Ultimate DeMos Gen", layout="wide", page_icon="🎨")

# --- ESTADOS DE SESIÓN ---
if "referencias" not in st.session_state:
    st.session_state.referencias = [] 
if "historial" not in st.session_state:
    st.session_state.historial = []
if "prompt_final" not in st.session_state:
    st.session_state.prompt_final = "" # Aquí se guarda el prompt ya procesado

# --- LÓGICA DEL SISTEMA "ULTIMATE PROMPT" (Simulación de JSONs) ---
# Esta instrucción le enseña a Gemini Flash a comportarse como tu aplicación de comandos
SYSTEM_INSTRUCTION_ULTIMATE = """
You are the 'Ultimate AI Image Prompt Generator'. You are NOT a chat bot. You are a CLI (Command Line Interface) for prompt engineering.
Your goal is to accept commands and output strictly formatted image prompts or variations.

COMMANDS LOGIC:
1. 'improve: <text>' -> Apply the 'Ultimate Structure': Subject + Medium + Style + Artist + Website + Resolution + Additional Details + Color + Lighting.
2. 'edit: <text>' -> Fix grammar, clarity, and add slight detail without changing the core style.
3. 'subject: <text>' -> Focus purely on describing the subject, ignoring style/lighting commands.
4. 'style: <text>' -> Focus purely on describing an aesthetic style (e.g., Cyberpunk, Baroque).
5. 'multiple: <text>' -> Generate 3 distinct variations of the prompt numbered 1, 2, 3.

RULES:
- If no command is provided, assume 'improve:'.
- Output ONLY the prompt text. No "Here is your prompt" or conversational filler.
- For 'improve:', ensure the output is a single, comma-separated, high-quality prompt optimized for generative AI.
"""

# --- SEGURIDAD ---
PASSWORD_ACCESO = "archviz2026"

def check_password():
    if "authenticated" not in st.session_state:
        st.sidebar.title("Login")
        pwd = st.sidebar.text_input("Contraseña", type="password")
        if st.sidebar.button("Entrar"):
            if pwd == PASSWORD_ACCESO:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.sidebar.error("Acceso Denegado")
        return False
    return True

if check_password():
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

    # --- ENCABEZADO Y TUTORIAL ---
    st.title("Ultimate DeMos Gen 🎨")
    
    with st.expander("📘 Tutorial y Comandos (Léeme primero)", expanded=True):
        st.markdown("""
        **Bienvenido a la integración de Ultimate Prompt Generator.**
        Esta herramienta funciona mediante **comandos** para estructurar tus prompts antes de generar la imagen.
        
        **Lista de Comandos Disponibles:**
        * `improve: tu idea` -> Aplica la estructura completa (Sujeto, Medio, Estilo, Iluminación, etc.). **(Recomendado)**
        * `edit: tu prompt` -> Corrige gramática y claridad sin cambiar mucho el estilo.
        * `style: estilo` -> Genera solo una descripción de estilo artístico.
        * `multiple: tu idea` -> Crea 3 variaciones diferentes para que elijas.
        
        **Flujo de trabajo:**
        1. Escribe tu comando en el cuadro "Entrada de Comandos".
        2. Presiona **"Procesar Comando"**.
        3. Revisa y edita el resultado en el cuadro de abajo.
        4. Presiona **"Generar Imagen Final"**.
        """)

    # --- SIDEBAR: CONFIGURACIÓN SIMPLE ---
    with st.sidebar:
        st.header("Motor")
        modelo_nombre = st.selectbox("Modelo", [
            "Nano Banana Pro (Gemini 3 Pro Image)",
            "Nano Banana (Gemini 2.5 Flash Image)"
        ])
        
        model_map = {
            "Nano Banana Pro (Gemini 3 Pro Image)": "gemini-3-pro-image-preview",
            "Nano Banana (Gemini 2.5 Flash Image)": "gemini-2.5-flash-image"
        }
        st.info("Ajustes de resolución y formato eliminados por solicitud. Controlar vía Prompt.")

    # --- ZONA 1: REFERENCIAS (OPCIONAL) ---
    st.subheader("1. Referencias Visuales")
    uploaded_files = st.file_uploader("Sube imágenes para guiar al modelo (Opcional)", 
                                     type=["png", "jpg", "jpeg"], accept_multiple_files=True)
    
    if uploaded_files:
        for f in uploaded_files:
            img = PIL.Image.open(f)
            if not any(d['name'] == f.name for d in st.session_state.referencias):
                st.session_state.referencias.append({"img": img, "name": f.name})

    refs_activas = []
    if st.session_state.referencias:
        cols = st.columns(6)
        for i, ref in enumerate(st.session_state.referencias):
            with cols[i % 6]:
                st.image(ref["img"], use_container_width=True)
                if st.checkbox(f"Usar", key=f"check_{ref['name']}"):
                    refs_activas.append(ref["img"])
        if st.button("Limpiar Referencias"):
            st.session_state.referencias = []
            st.rerun()

    st.divider()

    # --- ZONA 2: ULTIMATE PROMPT ENGINE (Lógica JSON) ---
    st.subheader("2. Ultimate Prompt Engine")
    
    col_input, col_output = st.columns([1, 1])
    
    with col_input:
        st.markdown("**Entrada de Comandos**")
        user_command = st.text_area("Escribe aquí (ej: 'improve: casa en el lago')", height=150, key="cmd_input")
        
        if st.button("🪄 Procesar Comando", type="primary"):
            if user_command:
                with st.spinner("Ejecutando lógica Ultimate Prompt..."):
                    try:
                        # Usamos Gemini Flash como el motor lógico del JSON
                        response_logic = client.models.generate_content(
                            model="gemini-2.5-flash",
                            contents=f"{SYSTEM_INSTRUCTION_ULTIMATE}\n\nINPUT COMMAND: {user_command}"
                        )
                        st.session_state.prompt_final = response_logic.text.strip()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error en el motor de comandos: {e}")
            else:
                st.warning("Escribe un comando primero.")

    with col_output:
        st.markdown("**Resultado (Prompt Final)**")
        st.caption("Aquí puedes editar el resultado antes de generar la imagen.")
        # El usuario ve el resultado del comando y puede modificarlo manualmente
        prompt_para_generar = st.text_area("Prompt Listo:", 
                                         value=st.session_state.prompt_final, 
                                         height=150,
                                         key="final_output")
        
        # Sincronización manual si el usuario edita
        if prompt_para_generar != st.session_state.prompt_final:
            st.session_state.prompt_final = prompt_para_generar

    # --- ZONA 3: GENERACIÓN ---
    st.divider()
    
    if st.button("🎨 Generar Imagen Final", use_container_width=True):
        if prompt_para_generar:
            with st.status("Renderizando...", expanded=False) as status:
                try:
                    # Construcción de solicitud
                    # CORRECCIÓN IMPORTANTE: Manejo de lista vacía de referencias
                    contenido_solicitud = [prompt_para_generar]
                    
                    if refs_activas:
                        contenido_solicitud = contenido_solicitud + refs_activas
                        st.write(f"Usando {len(refs_activas)} imágenes de referencia + Texto.")
                    else:
                        st.write("Generando solo con Texto (Zero-shot).")

                    # Llamada a API
                    response = client.models.generate_content(
                        model=model_map[modelo_nombre],
                        contents=contenido_solicitud,
                        config=types.GenerateContentConfig(
                            response_modalities=["IMAGE"]
                        )
                    )

                    # Procesamiento de respuesta
                    if response and response.parts:
                        resultado = None
                        for part in response.parts:
                            if part.inline_data:
                                resultado = PIL.Image.open(BytesIO(part.inline_data.data))
                                break
                        
                        if resultado:
                            st.session_state.historial.insert(0, resultado)
                            if len(st.session_state.historial) > 5:
                                st.session_state.historial.pop()
                            
                            st.subheader("Resultado")
                            st.image(resultado, use_container_width=True)
                            status.update(label="¡Imagen creada!", state="complete")
                        else:
                            st.error("El modelo no devolvió imagen (Bloqueo de seguridad o error interno).")
                    else:
                        st.error("Error: La API devolvió una respuesta vacía.")

                except Exception as e:
                    st.error(f"Error crítico: {e}")
        else:
            st.warning("El campo de Prompt Final está vacío. Usa un comando o escribe algo.")

    # --- HISTORIAL ---
    if st.session_state.historial:
        st.divider()
        st.subheader("Galería Reciente")
        h_cols = st.columns(5)
        for i, h_img in enumerate(st.session_state.historial):
            with h_cols[i]:
                st.image(h_img, use_container_width=True)
                buf = BytesIO()
                h_img.save(buf, format="PNG")
                st.download_button("💾", buf.getvalue(), f"gen_{i}.png", "image/png", key=f"dl_{i}")

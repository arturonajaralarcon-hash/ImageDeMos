import streamlit as st
from google import genai
import PIL.Image
import io

# Configuración visual
st.set_page_config(page_title="Gemini Image Studio", page_icon="🍌")

# --- SEGURIDAD ---
# Cambia 'amigo123' por la contraseña que quieras darle a tu amigo
PASSWORD_REQUERIDA = "DeMos2026" 

st.sidebar.title("Configuración")
password_input = st.sidebar.text_input("Contraseña de acceso", type="password")

if password_input == PASSWORD_REQUERIDA:
    # Inicializamos el cliente con la API Key guardada en Secrets
    client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

    st.title("🎨 Gemini Image Studio")
    st.info("Usando Gemini 3 Pro para procesar tus peticiones.")

    # --- SELECTOR DE MODELOS ---
    model_options = {
        "Nano Banana Pro (Gemini 3 Pro Image)": "gemini-3-pro",
        "Nano Banana (Gemini 2.5 Flash Preview Image)": "gemini-2.5-flash-preview",
        "Imagen 4 Ultra Generate": "imagen-4-ultra",
        "Imagen 4 Generate": "imagen-4"
    }

    modelo_seleccionado = st.sidebar.selectbox(
        "Selecciona el modelo de imagen:",
        options=list(model_options.keys())
    )
    
    id_modelo = model_options[modelo_seleccionado]

    # --- INTERFAZ DE USUARIO ---
    user_prompt = st.text_area("Describe la imagen que quieres generar:", 
                              placeholder="Un paisaje futurista con tonos neón...")

    if st.button("Generar Magia ✨"):
        if user_prompt:
            with st.spinner(f"Generando con {modelo_seleccionado}..."):
                try:
                    # Usamos la sintaxis solicitada adaptada a generación de imagen
                    # Nota: Para modelos Imagen se suele usar generate_image
                    response = client.models.generate_images(
                        model=id_modelo,
                        prompt=user_prompt,
                    )
                    
                    # Mostrar la imagen (asumiendo el formato de respuesta del SDK 2026)
                    for img in response.generated_images:
                        st.image(img.image, caption=f"Generada por {modelo_seleccionado}")
                        
                    st.success("¡Imagen generada con éxito!")
                except Exception as e:
                    st.error(f"Hubo un error con la API: {e}")
        else:
            st.warning("Por favor, escribe un prompt primero.")

else:
    if password_input:
        st.error("Contraseña incorrecta.")
    st.warning("Introduce la contraseña en la barra lateral para usar los tokens.")

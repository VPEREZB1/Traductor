import os
import re
import glob
import time
import streamlit as st
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
from gtts import gTTS
from googletrans import Translator

# ------------------ Config ------------------
st.set_page_config(page_title="TRADUCTOR INTERACTIVO", layout="centered")
st.title("TRADUCTOR INTERACTIVO")
st.subheader("HABLA Y LO TRADUCIRÉ")

# Imagen (si no existe, muestra aviso en lugar de crash)
IMAGE_PATH = "imagen_2025-09-12_155805756.png"
if os.path.exists(IMAGE_PATH):
    st.image(Image.open(IMAGE_PATH), width=300)
else:
    st.warning(f"No se encontró la imagen '{IMAGE_PATH}'. Puedes subirla o quitar esa línea.")

with st.sidebar:
    st.subheader("Traductor")
    st.write(
        "Presiona el botón para grabar tu voz (Chrome/Chromium en localhost o HTTPS). "
        "Cuando escuches la señal, di lo que quieras traducir. Si no funciona, escribe el texto abajo."
    )

st.write("Presiona el botón y di lo que quieres traducir (solo en Chrome/Chromium).")

# botón Bokeh + JS para usar webkitSpeechRecognition en el navegador
button = Button(label=" Escuchar  🎤", width=300, height=50)
button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'es-ES'; // puedes cambiar si quieres
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if ( value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.onerror = function(e) {
        document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: "__ERROR__:"+e.error}));
    }
    recognition.start();
"""))

result = streamlit_bokeh_events(
    button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0,
)

# Si llega texto desde JS, lo usamos; si no, permitimos escribir manualmente
detected_text = ""
if result and "GET_TEXT" in result:
    detected_text = result.get("GET_TEXT")
    if detected_text.startswith("__ERROR__:"):
        st.error("Error en reconocimiento de voz del navegador: " + detected_text.replace("__ERROR__:", ""))
        detected_text = ""
    else:
        st.success("Texto detectado: " + detected_text)

text = st.text_area("Texto a traducir (detectado o escribe manualmente):", value=detected_text, height=120)

# Crear carpeta temporal (segura)
os.makedirs("temp", exist_ok=True)

# Mapas de idiomas
LANG_MAP = {
    "Inglés": "en",
    "Español": "es",
    "Bengali": "bn",
    "Coreano": "ko",
    "Mandarín": "zh-cn",
    "Japonés": "ja",
}

in_lang = st.selectbox("Selecciona el lenguaje de Entrada", list(LANG_MAP.keys()))
out_lang = st.selectbox("Selecciona el lenguaje de salida", list(LANG_MAP.keys()))

input_language = LANG_MAP.get(in_lang, "auto")
output_language = LANG_MAP.get(out_lang, "es")

english_accent = st.selectbox(
    "Selecciona el acento (solo afecta cuando se pide tld para gTTS en inglés)",
    ("Defecto", "Español", "Reino Unido", "Estados Unidos", "Canada", "Australia", "Irlanda", "Sudáfrica"),
)

TLD_MAP = {
    "Defecto": "com",
    "Español": "com.mx",
    "Reino Unido": "co.uk",
    "Estados Unidos": "com",
    "Canada": "ca",
    "Australia": "com.au",
    "Irlanda": "ie",
    "Sudáfrica": "co.za",
}
tld = TLD_MAP.get(english_accent, "com")

display_output_text = st.checkbox("Mostrar el texto traducido")

# utilidades
def safe_filename(s):
    s = s or "audio"
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^A-Za-z0-9_.-]", "", s)
    return s[:40] or "audio"

def text_to_speech(input_language, output_language, text, tld):
    translator = Translator()
    try:
        # intenta traducir con src definido; si falla, deja autodetección
        translation = translator.translate(text, src=input_language if input_language != "auto" else None, dest=output_language)
        trans_text = translation.text
    except Exception as e:
        # intentar con autodetección
        try:
            translation = translator.translate(text, dest=output_language)
            trans_text = translation.text
        except Exception as e2:
            raise RuntimeError(f"Error en traducción: {e2}") from e2

    # gTTS
    try:
        tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
    except Exception as e:
        raise RuntimeError(f"gTTS error: {e}") from e

    filename = safe_filename(text[:40])
    out_path = os.path.join("temp", f"{filename}.mp3")
    tts.save(out_path)
    return out_path, trans_text

if st.button("Convertir a audio"):
    if not text or text.strip() == "":
        st.warning("No hay texto para convertir. Habla o escribe algo primero.")
    else:
        try:
            path, translated = text_to_speech(input_language, output_language, text, tld)
            with open(path, "rb") as f:
                audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/mp3")
            st.success("Audio generado correctamente.")
            st.download_button("Descargar MP3", data=audio_bytes, file_name=os.path.basename(path), mime="audio/mpeg")
            if display_output_text:
                st.markdown("### Texto de salida:")
                st.write(translated)
        except Exception as e:
            st.error(f"Ocurrió un error al generar el audio: {e}")

# limpieza: borrar mp3 más antiguos (en días)
def remove_old_files(days=7):
    mp3_files = glob.glob("temp/*.mp3")
    if mp3_files:
        now = time.time()
        threshold = now - days * 86400
        for f in mp3_files:
            try:
                if os.stat(f).st_mtime < threshold:
                    os.remove(f)
            except Exception:
                pass

remove_old_files(7)


        
    



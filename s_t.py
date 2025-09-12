import os
import re
import glob
import time
import streamlit as st
from bokeh.models import Button, CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
from gtts import gTTS
from deep_translator import GoogleTranslator

# ------------------ Config ------------------
st.set_page_config(page_title="TRADUCTOR INTERACTIVO", layout="centered")
st.title("TRADUCTOR INTERACTIVO")
st.subheader("HABLA Y LO TRADUCIRÉ")

# Imagen (segura)
IMAGE_PATH = "imagen_2025-09-12_155805756.png"
if os.path.exists(IMAGE_PATH):
    st.image(Image.open(IMAGE_PATH), width=300)
else:
    st.warning(f"No se encontró la imagen '{IMAGE_PATH}'.")

with st.sidebar:
    st.subheader("Traductor")
    st.write(
        "Presiona el botón para grabar tu voz (Chrome/Chromium en localhost o HTTPS). "
        "Cuando escuches la señal, di lo que quieras traducir. "
        "Si no funciona, escribe el texto abajo."
    )

st.write("Presiona el botón y di lo que quieres traducir:")

# botón Bokeh + JS para usar webkitSpeechRecognition
button = Button(label=" Escuchar  🎤", width=300, height=50)
button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'es-ES'; 
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

# texto detectado o manual
detected_text = ""
if result and "GET_TEXT" in result:
    detected_text = result.get("GET_TEXT")
    if detected_text.startswith("__ERROR__:"):
        st.error("Error en reconocimiento de voz: " + detected_text.replace("__ERROR__:", ""))
        detected_text = ""
    else:
        st.success("Texto detectado: " + detected_text)

text = st.text_area("Texto a traducir:", value=detected_text, height=120)

# carpeta temp
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
    "Selecciona el acento",
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
    try:
        trans_text = GoogleTranslator(source=input_language, target=output_language).translate(text)
    except Exception as e:
        raise RuntimeError(f"Error en traducción: {e}")

    try:
        tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
    except Exception as e:
        raise RuntimeError(f"Error en gTTS: {e}")

    filename = safe_filename(text[:40])
    out_path = os.path.join("temp", f"{filename}.mp3")
    tts.save(out_path)
    return out_path, trans_text

if st.button("Convertir a audio"):
    if not text.strip():
        st.warning("No hay texto para convertir.")
    else:
        try:
            path, translated = text_to_speech(input_language, output_language, text, tld)
            with open(path, "rb") as f:
                audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/mp3")
            st.success("Audio generado correctamente.")
            st.download_button("Descargar MP3", data=audio_bytes, file_name=os.path.basename(path), mime="audio/mpeg")
            if display_output_text:
                st.markdown("### Texto traducido:")
                st.write(translated)
        except Exception as e:
            st.error(f"Ocurrió un error: {e}")

# limpiar audios viejos
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

        
    



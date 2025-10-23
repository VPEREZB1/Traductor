import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import glob
from gtts import gTTS
from googletrans import Translator

# Estilos personalizados actualizados
st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Rubik:wght@300;400;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Rubik', sans-serif;
            background: linear-gradient(135deg, #f0f4ff, #e0ecff);
            color: #222;
        }

        .main {
            background-color: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            margin-top: 2rem;
        }

        .stButton>button {
            background: linear-gradient(to right, #6a11cb, #2575fc);
            color: white;
            font-weight: bold;
            font-size: 18px;
            border: none;
            border-radius: 12px;
            padding: 12px 28px;
            transition: 0.3s ease;
        }

        .stButton>button:hover {
            background: linear-gradient(to right, #4e0ec1, #1b5bda);
            transform: scale(1.02);
        }

        .stSelectbox, .stCheckbox {
            background-color: #ffffffaa !important;
            border-radius: 10px;
            padding: 0.3rem 0.5rem;
        }

        h1, h2, h3 {
            color: #0b1f47;
        }

        .stSidebar {
            background: #f8faff !important;
        }

        .stSidebar > div {
            color: black !important;
        }

        .css-1kyxreq {  /* Oculta los créditos de Streamlit abajo */
            display: none;
        }
    </style>
""", unsafe_allow_html=True)

# Contenido de la app
with st.container():
    st.title("💫Traductor💫")
    st.subheader("Habla y traduzco lo que digiste")

    image = Image.open("traductor.jpg")
    st.image(image, width=300)

    with st.sidebar:
        st.header("🔧 Instrucciones")
        st.markdown("""
        1. Presiona el botón para grabar tu voz.  
        2. Espera la señal y habla.  
        3. Luego elige el idioma al que deseas traducir.  
        4. ¡Escucha tu traducción en voz alta! 🎙️
        """)

    st.markdown("## 🎤 Graba tu voz")
    st.markdown("Presiona el botón y habla la frase que deseas traducir:")

    stt_button = Button(label="🎙️ Escuchar", width=300, height=50)
    stt_button.js_on_event("button_click", CustomJS(code="""
        var recognition = new webkitSpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;

        recognition.onresult = function (e) {
            var value = "";
            for (var i = e.resultIndex; i < e.results.length; ++i) {
                if (e.results[i].isFinal) {
                    value += e.results[i][0].transcript;
                }
            }
            if (value != "") {
                document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
            }
        }
        recognition.start();
    """))

    result = streamlit_bokeh_events(
        stt_button,
        events="GET_TEXT",
        key="listen",
        refresh_on_update=False,
        override_height=75,
        debounce_time=0
    )

    if result and "GET_TEXT" in result:
        text = str(result.get("GET_TEXT"))
        st.markdown("### 📝 Texto capturado:")
        st.success(text)

        try:
            os.mkdir("temp")
        except:
            pass

        st.markdown("## 🌐 Configuración de Traducción")
        translator = Translator()

        in_lang = st.selectbox("Idioma de entrada:", ("Inglés", "Español", "Bengali", "Coreano", "Mandarín", "Japonés"))
        lang_map = {"Inglés": "en", "Español": "es", "Bengali": "bn", "Coreano": "ko", "Mandarín": "zh-cn", "Japonés": "ja"}
        input_language = lang_map[in_lang]

        out_lang = st.selectbox("Idioma de salida:", ("Inglés", "Español", "Bengali", "Coreano", "Mandarín", "Japonés"))
        output_language = lang_map[out_lang]

        english_accent = st.selectbox("Acento:", (
            "Defecto", "Español", "Reino Unido", "Estados Unidos", 
            "Canada", "Australia", "Irlanda", "Sudáfrica"
        ))
        accent_map = {
            "Defecto": "com", "Español": "com.mx", "Reino Unido": "co.uk",
            "Estados Unidos": "com", "Canada": "ca", "Australia": "com.au",
            "Irlanda": "ie", "Sudáfrica": "co.za"
        }
        tld = accent_map[english_accent]

        def text_to_speech(input_language, output_language, text, tld):
            translation = translator.translate(text, src=input_language, dest=output_language)
            trans_text = translation.text
            tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
            try:
                my_file_name = text[0:20].strip().replace(" ", "_")
            except:
                my_file_name = "audio"
            tts.save(f"temp/{my_file_name}.mp3")
            return my_file_name, trans_text

        display_output_text = st.checkbox("Mostrar texto traducido")

        if st.button("🎧 Generar Audio"):
            result, output_text = text_to_speech(input_language, output_language, text, tld)
            audio_file = open(f"temp/{result}.mp3", "rb")
            audio_bytes = audio_file.read()
            st.markdown("### ▶️ Audio traducido:")
            st.audio(audio_bytes, format="audio/mp3", start_time=0)

            if display_output_text:
                st.markdown("### 📄 Texto traducido:")
                st.info(output_text)

        def remove_files(n):
            mp3_files = glob.glob("temp/*mp3")
            if len(mp3_files) != 0:
                now = time.time()
                n_days = n * 86400
                for f in mp3_files:
                    if os.stat(f).st_mtime < now - n_days:
                        os.remove(f)

        remove_files(7)

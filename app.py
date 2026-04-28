import streamlit as st
import pysrt
import os
import tempfile
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from src.core.ai_transcription import genera_sottotitoli_da_video
from src.core.timeline_manager import applica_vincoli_timeline_continua
from src.utils.helpers import genera_contenuto_ass
from src.core.video_processing import ottieni_durata_video, applica_sottotitoli
from src.ui.components import applica_css_globale, renderizza_timer_video, renderizza_anteprima_stile
from src.ui.editor import render_editor_interface

st.set_page_config(layout="wide", page_title="CapSyncStudio", page_icon="🎬")

# Directory temporanea
if 'temp_dir_obj' not in st.session_state:
    st.session_state.temp_dir_obj = tempfile.TemporaryDirectory()
TMP = st.session_state.temp_dir_obj.name

# Percorsi fissi
SRT_FILE = os.path.join(TMP, "sottotitoli_generati.srt")
VIDEO_UPLOAD = os.path.join(TMP, "temp_video_upload.mp4")
ASS_FILE = os.path.join(TMP, "temp_export.ass")

applica_css_globale()


@st.dialog("Processing", width="small")
def esegui_operazione(azione, **kwargs):
    if azione == "transcription":
        with st.spinner("Transcribing"):
            st.session_state.subs = genera_sottotitoli_da_video(
                st.session_state.video_corrente,
                custom_prompt=kwargs.get("prompt", "")
            )
            applica_vincoli_timeline_continua()
            st.session_state.subs.save(SRT_FILE, encoding='utf-8')
        st.rerun()   # chiude il dialog e aggiorna l'editor con i nuovi subs

    elif azione == "export":
        with st.spinner("Exporting video"):
            k = kwargs
            stile = k["stile_base"]
            nome_orig = st.session_state.get("nome_ultimo_file", "video_finale.mp4")
            output = os.path.join(TMP, f"sub_{nome_orig}")

            ass_content = genera_contenuto_ass(
                st.session_state.subs,
                "Testo Colorato (Karaoke)" if k["karaoke_attivo"] else "Nessuno",
                k["colore_karaoke"],
                stile,
                maiuscolo=k["maiuscolo_pulito"],
                parola_singola=k["parola_singola"]
            )
            with open(ASS_FILE, "w", encoding="utf-8") as f:
                f.write(ass_content)

            applica_sottotitoli(VIDEO_UPLOAD, ASS_FILE, output, speed=kwargs.get("speed", 1.0))

        # Qui fuori dallo spinner: il dialog resta aperto per il download
        st.success("Video exported successfully")
        with open(output, "rb") as f:
            st.download_button(
                label="Download Video",
                data=f,
                file_name=os.path.basename(output),
                mime="video/mp4",
                use_container_width=True
            )


# ---------- SIDEBAR ----------
with st.sidebar:
    display_mode = st.selectbox("Display Mode", ["Full Phrase", "Single Word"])
    speed_factor = st.slider(
        "Export Speed",
        min_value=0.25,
        max_value=2.0,
        value=1.0,
        step=0.05,
        format="%.2fx"
    )
    font_list = ["Arial","Verdana","Impact","Georgia","Trebuchet MS",
                 "Courier New","Comic Sans MS","Bradley Hand",
                 "Lucida Handwriting","Brush Script MT"]
    font = st.selectbox("Font Family", font_list)
    size = st.slider("Text Size", 10, 100, 15)
    outline = st.slider("Outline Thickness", 0.0, 10.0, 4.0, 0.5)
    glow = st.slider("Glow Intensity", 0.0, 10.0, 4.0, 0.5)
    zoom = st.slider("Focus Zoom Scale", 100, 200, 110, 5)

    c1, c2 = st.columns(2)
    with c1:
        bold = st.toggle("Bold", True)
        italic = st.toggle("Italic", False)
    with c2:
        uppercase = st.toggle("Uppercase", True)
        karaoke = st.toggle("Karaoke", value=True)

    col1, col2 = st.columns(2)
    with col1:
        color = st.color_picker("Main Color", "#FFFFFF")
    with col2:
        color_k = st.color_picker("Highlight", "#FFBF00", disabled=not karaoke)

    fw = "bold" if bold else "normal"
    fs = "italic" if italic else "normal"
    tt = "uppercase" if uppercase else "none"
    renderizza_anteprima_stile(font, size, fw, fs, tt, color)

    whisper_prompt = st.text_area("Context Prompt",
        value="Intelligenza Artificiale, Yann LeCun, Demis Hassabis, LLM, Large Language Models, paper, deep learning, lavoro, DeepSeek, Claude, Gemini, ChatGPT, GLM, Kimi, Qwen, Gemma",
        height=110)


# ---------- INIZIALIZZAZIONE SESSIONE ----------
defaults = {
    "video_corrente": None,
    "subs": pysrt.SubRipFile(),
    "durata_video": pysrt.SubRipTime(0),
    "nome_ultimo_file": None
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------- LAYOUT PRINCIPALE ----------
col_video, col_editor = st.columns([2, 5], gap="large")

with col_video:
    if st.session_state.video_corrente and os.path.exists(st.session_state.video_corrente):
        with open(st.session_state.video_corrente, "rb") as f:
            st.video(f.read())
        renderizza_timer_video()

        if st.button("Change Video", use_container_width=True):
            st.session_state.video_corrente = None
            st.session_state.subs = pysrt.SubRipFile()
            st.session_state.durata_video = pysrt.SubRipTime(0)
            st.rerun()
    else:
        st.markdown("")
        uploaded = st.file_uploader("Choose a  file video", type=["mp4","mov","avi","mkv"],
                                    label_visibility="collapsed")
        if uploaded:
            with open(VIDEO_UPLOAD, "wb") as f:
                f.write(uploaded.getbuffer())
            st.session_state.nome_ultimo_file = uploaded.name
            st.session_state.video_corrente = VIDEO_UPLOAD
            st.session_state.subs = pysrt.SubRipFile()
            st.session_state.durata_video = ottieni_durata_video(VIDEO_UPLOAD)
            st.rerun()

with col_editor:
    settings = {
        'font': font, 'size': size, 'color': color,
        'bold': bold, 'italic': italic, 'outline': outline,
        'glow': glow, 'zoom': zoom, 'karaoke': karaoke,
        'colore_k': color_k, 'upper': uppercase, 'mode': display_mode,
        'speed': speed_factor
    }
    render_editor_interface(whisper_prompt, settings, esegui_operazione)
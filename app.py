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

st.set_page_config(layout="wide", page_title="Subtitles Editor", page_icon="🎬")

if 'temp_dir_obj' not in st.session_state:
    # Questa cartella vive nel session_state e si autodistrugge alla fine
    st.session_state.temp_dir_obj = tempfile.TemporaryDirectory()

TEMP_DIR = st.session_state.temp_dir_obj.name

srt_file = os.path.join(TEMP_DIR, "sottotitoli_generati.srt")
temp_upload_path = os.path.join(TEMP_DIR, "temp_video_upload.mp4")
temp_ass_path = os.path.join(TEMP_DIR, "temp_export.ass")

applica_css_globale()

@st.dialog("Processing", width="small")
def esegui_operazione_bloccante(azione, **kwargs):
    # Abbiamo rimosso tutto il blocco st.markdown per non avere messaggi testuali

    if azione == "transcription":
        with st.spinner("Transcribing"):  # Lo spinner rimane per dare feedback visivo di attività
            nuovi_subs = genera_sottotitoli_da_video(
                st.session_state.video_corrente,
                custom_prompt=kwargs.get("prompt", "")
            )
            st.session_state.subs = nuovi_subs
            applica_vincoli_timeline_continua()
            st.session_state.subs.save(srt_file, encoding='utf-8')
        st.rerun()

    elif azione == "export":
        with st.spinner("Exporting video"):
            stile_base = kwargs.get("stile_base")
            karaoke_attivo = kwargs.get("karaoke_attivo")
            colore_karaoke = kwargs.get("colore_karaoke")
            maiuscolo_pulito = kwargs.get("maiuscolo_pulito")
            parola_singola = kwargs.get("parola_singola")

            nome_originale = st.session_state.get("nome_ultimo_file", "video_finale.mp4")
            # Puntiamo l'output finale nella cartella temporanea
            output_file = os.path.join(TEMP_DIR, f"sub_{nome_originale}")

            contenuto_ass = genera_contenuto_ass(
                st.session_state.subs,
                "Testo Colorato (Karaoke)" if karaoke_attivo else "Nessuno",
                colore_karaoke,
                stile_base,
                maiuscolo=maiuscolo_pulito,
                parola_singola=parola_singola
            )

            # Usiamo temp_ass_path invece di "temp_export.ass" codificato a mano
            with open(temp_ass_path, "w", encoding="utf-8") as f:
                f.write(contenuto_ass)

            applica_sottotitoli(temp_upload_path, temp_ass_path, output_file, "")
            st.session_state.video_corrente = output_file

        st.rerun()


# --- SIDEBAR: UX OPTIMIZED ---
with st.sidebar:
    uploaded_file = st.file_uploader("Video", type=["mp4", "mov", "avi", "mkv"], label_visibility="collapsed")

    video_da_processare = None
    if uploaded_file is not None:
        if st.session_state.get("nome_ultimo_file") != uploaded_file.name:
            with open(temp_upload_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.nome_ultimo_file = uploaded_file.name
        video_da_processare = temp_upload_path

    if "ultimo_video_caricato" not in st.session_state:
        st.session_state.ultimo_video_caricato = None
    if video_da_processare != st.session_state.ultimo_video_caricato:
        st.session_state.ultimo_video_caricato = video_da_processare
        st.session_state.video_corrente = video_da_processare
        st.session_state.subs = pysrt.SubRipFile()
        st.session_state.durata_video = ottieni_durata_video(
            video_da_processare) if video_da_processare else pysrt.SubRipTime(0)

    if "video_corrente" not in st.session_state:
        st.session_state.video_corrente = None
    if "subs" not in st.session_state:
        st.session_state.subs = pysrt.SubRipFile()
    if "durata_video" not in st.session_state:
        st.session_state.durata_video = pysrt.SubRipTime(0)

    whisper_prompt = st.text_area("Context Prompt",
                                  value="Intelligenza Artificiale, Yann LeCun, LLM, Large Language Models, paper, deep learning, lavoro.",
                                  height=110)

    # 2. SELEZIONI TESTUALI (Dropdowns)
    modalita_visualizzazione = st.selectbox("Display Mode", ["Full Phrase", "Single Word"])

    # Lista di 10 font ottimizzati per UX e compatibilità FFmpeg (Win/Mac)
    lista_font = [
        "Arial",
        "Verdana",
        "Impact",
        "Georgia",
        "Trebuchet MS",
        "Courier New",
        "Comic Sans MS",
        "Bradley Hand",
        "Lucida Handwriting",
        "Brush Script MT"
    ]
    font_scelto = st.selectbox("Font Family", lista_font)

    # 3. GRUPPO SLIDER (Dimensioni e Intensità)
    # Raggruppati per controllo granulare
    size_scelta = st.slider("Text Size", 10, 100, 15)
    bordo_spessore = st.slider("Outline Thickness", 0.0, 10.0, 4.0, 0.5)
    glow_intensita = st.slider("Glow Intensity", 0.0, 10.0, 4.0, 0.5)
    zoom_factor = st.slider("Focus Zoom Scale", 100, 200, 110, 5)

    # 4. GRUPPO TOGGLE (Stati Binari)
    # Organizzati in una griglia per compattezza
    t1, t2 = st.columns(2)
    with t1:
        bold_scelto = st.toggle("Bold", True)
        italic_scelto = st.toggle("Italic", False)
    with t2:
        maiuscolo_pulito = st.toggle("Uppercase", True)
        karaoke_attivo = st.toggle("Karaoke", value=True)

    # 5. GRUPPO COLORI (Estetica Cromatica)
    c1, c2 = st.columns(2)
    with c1:
        colore_scelto = st.color_picker("Main Color", "#FFFFFF")
    with c2:
        colore_karaoke = st.color_picker(
            "Highlight",
            "#FFBF00",
            disabled=not karaoke_attivo
        )

    # 6. ANTEPRIMA DINAMICA
    # Generiamo i CSS in base ai toggle attivi
    fw = "bold" if bold_scelto else "normal"
    fs = "italic" if italic_scelto else "normal"
    tt = "uppercase" if maiuscolo_pulito else "none"

    renderizza_anteprima_stile(font_scelto, size_scelta, fw, fs, tt, colore_scelto)

# --- LAYOUT PRINCIPALE ---
# Contenitore globale per allineare tutto ordinatamente
with st.container():
    col_video, col_editor = st.columns([2, 5], gap="large")

    with col_video:
        st.markdown("<div style='margin-top: 3.5rem;'></div>", unsafe_allow_html=True)
        if st.session_state.video_corrente and os.path.exists(st.session_state.video_corrente):
            with open(st.session_state.video_corrente, "rb") as f:
                st.video(f.read())

            # Pulsante timer con stile Streamlit nativo e codice ridotto all'osso
            renderizza_timer_video()

    with col_editor:
        # Raccogliamo i settaggi in un unico dizionario per pulizia
        settings = {
            'font': font_scelto, 'size': size_scelta, 'color': colore_scelto,
            'bold': bold_scelto, 'italic': italic_scelto, 'outline': bordo_spessore,
            'glow': glow_intensita, 'zoom': zoom_factor, 'karaoke': karaoke_attivo,
            'colore_k': colore_karaoke, 'upper': maiuscolo_pulito,
            'mode': modalita_visualizzazione
        }

        render_editor_interface(whisper_prompt, settings, esegui_operazione_bloccante)

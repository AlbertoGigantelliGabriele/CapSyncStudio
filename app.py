import streamlit as st
import pysrt
import copy
import os
import tempfile
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from src.core.ai_transcription import generate_subtitles_from_video
from src.core.timeline_manager import apply_continuous_timeline
from src.utils.helpers import generate_ass_content
from src.core.video_processing import get_video_duration, apply_subtitles, concatenate_videos
from src.ui.components import apply_global_css, render_video_timer, render_style_preview
from src.ui.editor import render_editor_interface

st.set_page_config(layout="wide", page_title="CapSyncStudio", page_icon="🎬")

# Temporary directory
if 'temp_dir_obj' not in st.session_state:
    st.session_state.temp_dir_obj = tempfile.TemporaryDirectory()
TMP = st.session_state.temp_dir_obj.name

# Fixed paths
ASS_FILE = os.path.join(TMP, "temp_export.ass")

apply_global_css()


@st.dialog("Processing", width="small", dismissible=False)
def execute_operation(action, **kwargs):
    if action == "transcription":
        if st.session_state.get("original_subs") is not None:
            st.session_state.subs = copy.deepcopy(st.session_state.original_subs)
            apply_continuous_timeline()
            st.rerun()

        prog_bar = st.progress(0.0)

        def update_transcription_progress(pct):
            prog_bar.progress(pct)

        nuovi_subs = generate_subtitles_from_video(
            st.session_state.current_video,
            custom_prompt=kwargs.get("prompt", ""),
            max_chars=kwargs.get("max_chars", 28),
            progress_callback=update_transcription_progress
        )

        st.session_state.subs = nuovi_subs
        st.session_state.original_subs = copy.deepcopy(nuovi_subs)
        apply_continuous_timeline()
        st.rerun()

    elif action == "export":
        progress_bar = st.progress(value=0)
        def update_progress(pct):
            progress_bar.progress(pct)

        k = kwargs
        style = k["base_style"]
        original_name = st.session_state.get("last_filename", "final_video.mp4")
        output = os.path.join(TMP, f"sub_{original_name}")

        ass_content = generate_ass_content(
            st.session_state.subs,
            "Colored Text" if k["karaoke_active"] else "None",
            k["karaoke_color"],
            style,
            uppercase=k["clean_uppercase"],
            single_word=k["single_word"]
        )
        with open(ASS_FILE, "w", encoding="utf-8") as f:
            f.write(ass_content)

        apply_subtitles(
            st.session_state.current_video,
            ASS_FILE,
            output,
            speed=kwargs.get("speed", 1.0),
            callback_progress=update_progress
        )
        progress_bar.empty()

        # After the spinner: save the exported video and close the dialog
        st.session_state.final_video = output
        st.rerun()  # chiude il dialog e mostra il video nella colonna


# ---------- SIDEBAR ----------
with st.sidebar:
    display_mode = st.selectbox("Display Mode", ["Full Phrase", "Single Word"])
    speed_factor = st.slider(
        "Export Speed",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.05,
        format="%.2fx"
    )
    max_chars_limit = st.slider("Max Subtitle Length", min_value=10, max_value=80, value=28, step=1)
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
    render_style_preview(font, size, fw, fs, tt, color)

    whisper_prompt = st.text_area("Context Prompt",
                                  value="Intelligenza Artificiale, Yann LeCun, Demis Hassabis, LLM, Large Language Models, paper, deep learning, lavoro, DeepSeek, Claude, Gemini, ChatGPT, GLM, Kimi, Qwen, Gemma",
                                  height=110)


# ---------- SESSION INITIALIZATION ----------
defaults = {
    "current_video": None,
    "subs": pysrt.SubRipFile(),
    "original_subs": None,
    "video_duration": pysrt.SubRipTime(0),
    "last_filename": None,
    "final_video": None,
    "upload_queue": [],
    "upload_counter": 0
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------- MAIN LAYOUT ----------
col_video, col_editor = st.columns([2, 5], gap="large")

with col_video:
    # Decide which video to show: export first, then original
    video_to_show = st.session_state.get("final_video")
    if not video_to_show or not os.path.exists(video_to_show):
        video_to_show = st.session_state.current_video

    if video_to_show and os.path.exists(video_to_show):
        st.video(video_to_show)
        render_video_timer()

        # If showing exported video
        if st.session_state.get("final_video") and video_to_show == st.session_state.final_video:

            with open(st.session_state.final_video, "rb") as f:
                st.download_button(
                    label="Download",
                    data=f,
                    file_name=os.path.basename(st.session_state.final_video),
                    mime="video/mp4",
                    use_container_width=True
                )

        else:
            # Original (or concatenated) video – change button
            if st.button("Change Video", use_container_width=True):
                st.session_state.current_video = None
                st.session_state.subs = pysrt.SubRipFile()
                st.session_state.original_subs = None
                st.session_state.video_duration = pysrt.SubRipTime(0)
                st.session_state.final_video = None
                st.session_state.upload_queue = []
                st.session_state.upload_counter = 0
                st.rerun()
    else:
        # No active video: show native multiple upload interface
        st.markdown("")
        uploaded_files = st.file_uploader(
            "Select video file(s)",
            type=["mp4", "mov", "avi", "mkv"],
            accept_multiple_files=True
        )

        if uploaded_files:
            if st.button("Merge/Proceed", use_container_width=True):
                # Processa i file in una sola operazione
                saved_paths = []
                for uf in uploaded_files:
                    temp_path = os.path.join(TMP, uf.name)
                    with open(temp_path, "wb") as f:
                        f.write(uf.getbuffer())
                    saved_paths.append(temp_path)

                if len(saved_paths) == 1:
                    concat_output = saved_paths[0]
                else:
                    concat_output = os.path.join(TMP, "concatenated_video.mp4")
                    with st.spinner("Merging videos..."):
                        try:
                            # Richiama la funzione di unione
                            concatenate_videos(saved_paths, concat_output)
                        except RuntimeError as e:
                            st.error(f"Concatenation failed: {e}")
                            st.stop()

                st.session_state.last_filename = uploaded_files[0].name
                st.session_state.current_video = concat_output
                st.session_state.subs = pysrt.SubRipFile()
                st.session_state.original_subs = None
                st.session_state.video_duration = get_video_duration(concat_output)
                # Un solo rerun quando tutto è pronto
                st.rerun()

with col_editor:
    settings = {
        'font': font, 'size': size, 'color': color,
        'bold': bold, 'italic': italic, 'outline': outline,
        'glow': glow, 'zoom': zoom, 'karaoke': karaoke,
        'color_k': color_k, 'upper': uppercase, 'mode': display_mode,
        'speed': speed_factor,
        'max_chars': max_chars_limit
    }
    render_editor_interface(whisper_prompt, settings, execute_operation)

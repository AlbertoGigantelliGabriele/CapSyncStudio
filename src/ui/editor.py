import streamlit as st
import pandas as pd
import pysrt
from src.ui.callbacks import *


def process_editor_changes():
    """Sincronizza le modifiche con il backend SENZA toccare il DataFrame visivo."""
    state = st.session_state.get("sub_editor_state")
    if not state or "editor_df" not in st.session_state:
        return

    df = st.session_state.editor_df

    for row_idx_str, edits in state.get("edited_rows", {}).items():
        row_idx = int(row_idx_str)
        i, j = int(df.at[row_idx, "i"]), int(df.at[row_idx, "j"])

        for col, val in edits.items():
            # 1. Modifiche Testuali e Temporali
            # ATTENZIONE: NON modifichiamo df.at[row_idx, col] = val.
            # In questo modo Streamlit non si accorge che i dati sono cambiati
            # e NON resetta lo scroll. La UI mostra comunque la modifica
            # grazie allo stato interno "edited_rows" di st.data_editor.
            if col == "Word":
                update_word_text(i, j, val)
            elif col == "Start":
                update_word_start(i, j, val)
            elif col == "End":
                update_word_end(i, j, val)

            elif col in ["🔗", "➕", "🗑️"] and val:
                if col == "🔗":
                    merge_words(i, j)
                elif col == "➕":
                    insert_word(i, j)
                elif col == "🗑️":
                    delete_word(i, j)

                rows = []
                for i_idx, sub in enumerate(st.session_state.subs):
                    block_marker = "🔹" if i_idx % 2 == 0 else "🔸"
                    for j_idx, (word_text, w_start, w_end) in enumerate(sub.word_timings):
                        rows.append({
                            "i": i_idx, "j": j_idx,
                            "Blk": block_marker,
                            "Start": pysrt.SubRipTime.from_ordinal(w_start).__str__(),
                            "End": pysrt.SubRipTime.from_ordinal(w_end).__str__(),
                            "Word": word_text,
                            "🔗": False, "➕": False, "🗑️": False
                        })

                # IN-PLACE UPDATE: Svuotiamo e riempiamo il DataFrame senza ricreare l'oggetto
                df.drop(df.index, inplace=True)
                for idx_row, row_data in enumerate(rows):
                    df.loc[idx_row] = row_data

                # Resetta lo stato delle modifiche del widget per spegnere le checkbox
                if "sub_editor_state" in st.session_state:
                    del st.session_state["sub_editor_state"]

                # Non serve alcun st.rerun, il fragment si ri-eseguirà da solo
                # e la chiave del widget resta la stessa, conservando lo scroll.


@st.fragment
def render_subtitle_list():
    if getattr(st.session_state, 'subs', None) is None or len(st.session_state.subs) == 0:
        return

    # Creiamo il DataFrame visivo SOLO all'avvio o dopo modifiche strutturali
    if "editor_df" not in st.session_state or st.session_state.get("rebuild_df", True):
        rows = []
        for i, sub in enumerate(st.session_state.subs):
            block_marker = "🔹" if i % 2 == 0 else "🔸"

            for j, (word_text, w_start, w_end) in enumerate(sub.word_timings):
                rows.append({
                    "i": i, "j": j,
                    "Blk": block_marker,  # solo emoji, niente numero
                    "Start": pysrt.SubRipTime.from_ordinal(w_start).__str__(),
                    "End": pysrt.SubRipTime.from_ordinal(w_end).__str__(),
                    "Word": word_text,
                    "🔗": False, "➕": False, "🗑️": False
                })
        st.session_state.editor_df = pd.DataFrame(rows)
        st.session_state.rebuild_df = False

    st.data_editor(
        st.session_state.editor_df,
        column_config={
            "i": None, "j": None,
            "Blk": st.column_config.TextColumn("ID", width="small", disabled=True),
            "Start": st.column_config.TextColumn("Start", width="small"),
            "End": st.column_config.TextColumn("End", width="small"),
            "Word": st.column_config.TextColumn("Parola", width="medium"),
            "🔗": st.column_config.CheckboxColumn("🔗", width="small"),
            "➕": st.column_config.CheckboxColumn("➕", width="small"),
            "🗑️": st.column_config.CheckboxColumn("🗑️", width="small"),
        },
        hide_index=True,
        use_container_width=True,
        height=550,
        key="sub_editor_state",
        on_change=process_editor_changes
    )


def render_editor_interface(whisper_prompt, settings, execute_operation):
    st.markdown("")
    render_subtitle_list()

    st.write("")
    col1, col2 = st.columns(2)
    ready = st.session_state.current_video is not None

    with col1:
        if st.button("🖋️ Generate Transcription", use_container_width=True, disabled=not ready):
            st.session_state.rebuild_df = True
            execute_operation("transcription", prompt=whisper_prompt, max_chars=settings['max_chars'])

    with col2:
        if st.button("💾 Create Video", use_container_width=True, disabled=not ready):
            if not st.session_state.subs:
                st.warning("No subtitles available")
            else:
                from src.utils.helpers import hex_to_ass_color
                style = {
                    'font': settings['font'], 'size': settings['size'],
                    'color': hex_to_ass_color(settings['color']),
                    'color_hex': settings['color'],
                    'bold': "-1" if settings['bold'] else "0",
                    'italic': "-1" if settings['italic'] else "0",
                    'outline': settings['outline'], 'glow': settings['glow'],
                    'zoom': settings['zoom']
                }
                execute_operation("export",
                                  base_style=style,
                                  karaoke_active=settings['karaoke'],
                                  karaoke_color=settings['color_k'],
                                  clean_uppercase=settings['upper'],
                                  single_word=(settings['mode'] == "Single Word"),
                                  speed=settings['speed'])
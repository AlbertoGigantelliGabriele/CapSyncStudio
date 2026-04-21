import streamlit as st
import pysrt
from src.ui.callbacks import (
    aggiorna_inizio, aggiorna_fine, aggiorna_testo,
    elimina_blocco, sposta_su, sposta_giu, aggiungi_blocco_intermedio
)
from src.utils.helpers import hex_to_ass_color

def render_editor_interface(whisper_prompt, settings_dict, esegui_operazione_bloccante):
    """
    Gestisce i tab dell'editor e i pulsanti di azione (Trascrizione, Aggiunta, Export).
    settings_dict contiene tutte le scelte fatte nella sidebar (font, colori, ecc.)
    """
    tab_blocchi, tab_parola = st.tabs(["Multiple words", "Single word"])

    with tab_blocchi:
        with st.container(height=550, border=False):
            for i, sub in enumerate(st.session_state.subs):
                # Sincronizzazione dati con session_state
                st.session_state[f"start_{i}"] = str(sub.start)
                st.session_state[f"end_{i}"] = str(sub.end)
                st.session_state[f"text_{i}"] = sub.text

                col_times, col_text, col_actions = st.columns([3, 5, 2])

                with col_times:
                    is_first = (i == 0)
                    is_last = (i == len(st.session_state.subs) - 1)
                    st.text_input("Start", key=f"start_{i}", on_change=aggiorna_inizio, args=(i,),
                                  disabled=is_first, label_visibility="collapsed")
                    st.text_input("End", key=f"end_{i}", on_change=aggiorna_fine, args=(i,),
                                  disabled=is_last, label_visibility="collapsed")

                with col_text:
                    st.text_area("Text", key=f"text_{i}", height=85, label_visibility="collapsed",
                                 on_change=aggiorna_testo, args=(i,))

                with col_actions:
                    r1_c1, r1_c2 = st.columns(2)
                    r2_c1, r2_c2 = st.columns(2)

                    with r1_c1:
                        if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                            elimina_blocco(i)
                            st.rerun()
                    with r1_c2:
                        if st.button("↑", key=f"up_{i}", use_container_width=True) and i > 0:
                            sposta_su(i)
                            st.rerun()
                    with r2_c1:
                        if st.button("➕", key=f"add_{i}", use_container_width=True):
                            aggiungi_blocco_intermedio(i)
                            st.rerun()
                    with r2_c2:
                        if st.button("↓", key=f"down_{i}", use_container_width=True) and i < len(st.session_state.subs) - 1:
                            sposta_giu(i)
                            st.rerun()

                st.markdown("<hr style='margin: 0; border: 1px solid rgba(255, 255, 255, 0.1);'>", unsafe_allow_html=True)

    with tab_parola:
        with st.container(height=550, border=False):
            word_index = 0
            for block_idx, sub in enumerate(st.session_state.subs):
                # Utilizzo dei word_timings generati da ai_transcription.py
                if hasattr(sub, 'word_timings') and sub.word_timings:
                    for w_idx, (word, w_start_ms, w_end_ms) in enumerate(sub.word_timings):
                        start_str = str(pysrt.SubRipTime(milliseconds=w_start_ms))
                        end_str = str(pysrt.SubRipTime(milliseconds=w_end_ms))
                        col_w_times, col_w_text = st.columns([3, 7])
                        with col_w_times:
                            st.text_input("Start W", value=start_str, key=f"w_start_{word_index}", disabled=True, label_visibility="collapsed")
                            st.text_input("End W", value=end_str, key=f"w_end_{word_index}", disabled=True, label_visibility="collapsed")
                        with col_w_text:
                            st.text_input("Word", value=word, key=f"w_text_{word_index}", label_visibility="collapsed")
                        word_index += 1
                else:
                    st.info(f"No word timings available for block {block_idx + 1}. Please regenerate transcription.")

    # --- PULSANTI DI AZIONE FINALI ---
    st.write("")
    col_gen, col_add_main, col_export = st.columns(3)
    video_pronto = st.session_state.video_corrente is not None

    with col_gen:
        if st.button("🖋️ Generate Transcription", use_container_width=True, disabled=not video_pronto):
            esegui_operazione_bloccante("transcription", prompt=whisper_prompt)

    with col_add_main:
        durata_max = st.session_state.durata_video
        start_coda = st.session_state.subs[-1].end if st.session_state.subs else pysrt.SubRipTime(0)
        limite_raggiunto = (durata_max.ordinal > 0) and (start_coda.ordinal >= durata_max.ordinal)

        if st.button("➕ Add Block", use_container_width=True, disabled=(not video_pronto or limite_raggiunto)):
            end_coda = start_coda + pysrt.SubRipTime(seconds=1)
            if durata_max.ordinal > 0 and end_coda.ordinal > durata_max.ordinal:
                end_coda = durata_max
            st.session_state.subs.append(pysrt.SubRipItem(index=len(st.session_state.subs) + 1, start=start_coda, end=end_coda, text=""))
            st.rerun()

    with col_export:
        if st.button("💾 Create Video", use_container_width=True, disabled=not video_pronto):
            if not st.session_state.subs:
                st.warning("No subtitles available")
            else:
                # Prepariamo lo stile base usando i dati della sidebar
                stile_base = {
                    'font': settings_dict['font'],
                    'size': settings_dict['size'],
                    'color': hex_to_ass_color(settings_dict['color']),
                    'color_hex': settings_dict['color'],
                    'bold': "-1" if settings_dict['bold'] else "0",
                    'italic': "-1" if settings_dict['italic'] else "0",
                    'outline': settings_dict['outline'],
                    'glow': settings_dict['glow'],
                    'zoom': settings_dict['zoom']
                }
                esegui_operazione_bloccante(
                    "export",
                    stile_base=stile_base,
                    karaoke_attivo=settings_dict['karaoke'],
                    colore_karaoke=settings_dict['colore_k'],
                    maiuscolo_pulito=settings_dict['upper'],
                    parola_singola=(settings_dict['mode'] == "Single Word")
                )

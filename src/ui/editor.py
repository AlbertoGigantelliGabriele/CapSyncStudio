import streamlit as st
import pysrt
from src.ui.callbacks import *
from src.utils.helpers import hex_to_ass_color

def render_editor_interface(whisper_prompt, settings, esegui_operazione):
    tab_blocchi, tab_parola = st.tabs(["Multiple words", "Single word"])

    # ---------- TAB BLOCCHI ----------
    with tab_blocchi:
        with st.container(height=550, border=False):
            for i, sub in enumerate(st.session_state.subs):
                # Sincronizza lo stato per i campi di input
                st.session_state[f"start_{i}"] = str(sub.start)
                st.session_state[f"end_{i}"]   = str(sub.end)
                st.session_state[f"text_{i}"]  = sub.text

                c_times, c_text, c_act = st.columns([3,5,2])
                n_subs = len(st.session_state.subs)

                with c_times:
                    st.text_input("Start", key=f"start_{i}", on_change=aggiorna_inizio, args=(i,),
                                  disabled=(i==0), label_visibility="collapsed")
                    st.text_input("End",   key=f"end_{i}",   on_change=aggiorna_fine, args=(i,),
                                  disabled=(i==n_subs-1), label_visibility="collapsed")

                with c_text:
                    st.text_area("Text", key=f"text_{i}", height=85, label_visibility="collapsed",
                                 on_change=aggiorna_testo, args=(i,))

                with c_act:
                    r1c1, r1c2 = st.columns(2)
                    r2c1, r2c2 = st.columns(2)
                    with r1c1:
                        if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                            elimina_blocco(i); st.rerun()
                    with r1c2:
                        if st.button("↑", key=f"up_{i}", use_container_width=True) and i>0:
                            sposta_su(i); st.rerun()
                    with r2c1:
                        if st.button("➕", key=f"add_{i}", use_container_width=True):
                            aggiungi_blocco_intermedio(i); st.rerun()
                    with r2c2:
                        if st.button("↓", key=f"down_{i}", use_container_width=True) and i<n_subs-1:
                            sposta_giu(i); st.rerun()

                st.markdown("<hr style='margin:0;border:1px solid rgba(128,128,128,0.2);'>",
                            unsafe_allow_html=True)

    # ---------- TAB PAROLA ----------
    with tab_parola:
        with st.container(height=550, border=False):
            widx = 0
            for bidx, sub in enumerate(st.session_state.subs):
                if hasattr(sub, 'word_timings') and sub.word_timings:
                    for word, w_start, w_end in sub.word_timings:
                        s = str(pysrt.SubRipTime(milliseconds=w_start))
                        e = str(pysrt.SubRipTime(milliseconds=w_end))
                        c1, c2 = st.columns([3,7])
                        with c1:
                            st.text_input("Start W", value=s, key=f"w_start_{widx}", disabled=True,
                                          label_visibility="collapsed")
                            st.text_input("End W",   value=e, key=f"w_end_{widx}",   disabled=True,
                                          label_visibility="collapsed")
                        with c2:
                            st.text_input("Word", value=word, key=f"w_text_{widx}", label_visibility="collapsed")
                        widx += 1
                else:
                    st.info(f"No word timings for block {bidx+1}. Regenerate transcription.")

    # ---------- PULSANTI FINALI ----------
    st.write("")
    c1, c2, c3 = st.columns(3)
    ready = st.session_state.video_corrente is not None

    with c1:
        if st.button("🖋️ Generate Transcription", use_container_width=True, disabled=not ready):
            esegui_operazione("transcription", prompt=whisper_prompt)

    with c2:
        dur = st.session_state.durata_video
        last = st.session_state.subs[-1].end if st.session_state.subs else pysrt.SubRipTime(0)
        limit = (dur.ordinal>0) and (last.ordinal >= dur.ordinal)
        if st.button("➕ Add Block", use_container_width=True, disabled=(not ready or limit)):
            new_end = last + pysrt.SubRipTime(seconds=1)
            if 0 < dur.ordinal < new_end.ordinal:
                new_end = dur
            st.session_state.subs.append(
                pysrt.SubRipItem(index=len(st.session_state.subs)+1, start=last, end=new_end, text=""))
            st.rerun()

    with c3:
        if st.button("💾 Create Video", use_container_width=True, disabled=not ready):
            if not st.session_state.subs:
                st.warning("No subtitles available")
            else:
                stile = {
                    'font': settings['font'],
                    'size': settings['size'],
                    'color': hex_to_ass_color(settings['color']),
                    'color_hex': settings['color'],
                    'bold': "-1" if settings['bold'] else "0",
                    'italic': "-1" if settings['italic'] else "0",
                    'outline': settings['outline'],
                    'glow': settings['glow'],
                    'zoom': settings['zoom']
                }
                esegui_operazione("export",
                    stile_base=stile,
                    karaoke_attivo=settings['karaoke'],
                    colore_karaoke=settings['colore_k'],
                    maiuscolo_pulito=settings['upper'],
                    parola_singola=(settings['mode']=="Single Word"),
                    speed=settings['speed'])
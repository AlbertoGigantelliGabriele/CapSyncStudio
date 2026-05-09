import streamlit as st
import pysrt
from src.ui.callbacks import *
from src.utils.helpers import hex_to_ass_color

def render_editor_interface(whisper_prompt, settings, execute_operation):

    st.markdown("");
    with st.container(height=550, border=False):
        n_subs = len(st.session_state.subs)
        for i, sub in enumerate(st.session_state.subs):
            # Sync state for input fields
            st.session_state[f"start_{i}"] = str(sub.start)
            st.session_state[f"end_{i}"]   = str(sub.end)
            st.session_state[f"text_{i}"]  = sub.text

            c_times, c_text, c_act = st.columns([2,9,1])

            with c_times:
                st.text_input("Start", key=f"start_{i}", on_change=update_start, args=(i,),
                              disabled=(i==0), label_visibility="collapsed")
                st.text_input("End",   key=f"end_{i}",   on_change=update_end, args=(i,),
                              disabled=(i==n_subs-1), label_visibility="collapsed")

            with c_text:
                st.text_area("Text", key=f"text_{i}", height=85, label_visibility="collapsed",
                             on_change=update_text, args=(i,))

            with c_act:
                if st.button("🗑️", key=f"del_{i}", use_container_width=True):
                        delete_block(i); st.rerun()
                if st.button("➕", key=f"add_{i}", use_container_width=True):
                        insert_intermediate_block(i); st.rerun()

            st.markdown("<hr style='margin:0;border:1px solid rgba(128,128,128,0.2);'>",
                        unsafe_allow_html=True)

    # ---------- FINAL BUTTONS ----------
    st.write("")
    c1, c2, c3 = st.columns(3)
    ready = st.session_state.current_video  is not None

    with c1:
        if st.button("🖋️ Generate Transcription", use_container_width=True, disabled=not ready):
            execute_operation("transcription", prompt=whisper_prompt)

    with c2:
        dur = st.session_state.video_duration
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
                style = {
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

                execute_operation("export",
                    base_style=style,
                    karaoke_active=settings['karaoke'],
                    karaoke_color=settings['color_k'],
                    clean_uppercase=settings['upper'],
                    single_word=(settings['mode']=="Single Word"),
                    speed=settings['speed'])
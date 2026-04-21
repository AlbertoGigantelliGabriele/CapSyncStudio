import pysrt
import streamlit as st

def applica_vincoli_timeline_continua():
    """Rende la timeline continua, fissa il primo inizio a 0 e l'ultima fine alla durata del video."""
    if getattr(st.session_state, 'subs', None) is None or len(st.session_state.subs) == 0:
        return

    # 1. Fissa il primo inizio a zero
    st.session_state.subs[0].start = pysrt.SubRipTime(0)

    # 2. Fissa l'ultima fine alla durata esatta del video
    if st.session_state.durata_video.ordinal > 0:
         st.session_state.subs[-1].end = st.session_state.durata_video

    # 3. Chiudi i gap intermedi (la fine di un blocco diventa l'inizio del successivo)
    for i in range(len(st.session_state.subs) - 1):
         st.session_state.subs[i].end = st.session_state.subs[i + 1].start


def riordina_indici():
    for idx, sub in enumerate(st.session_state.subs):
        sub.index = idx + 1


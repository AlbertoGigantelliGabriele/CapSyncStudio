import streamlit as st
import pysrt
from src.utils.helpers import parse_srt_time
from src.core.timeline_manager import riordina_indici, applica_vincoli_timeline_continua

def aggiorna_inizio(i):
    if i <= 0 or i >= len(st.session_state.subs): return
    nuovo_tempo = parse_srt_time(st.session_state.get(f"start_{i}"))
    if nuovo_tempo:
        st.session_state.subs[i].start = nuovo_tempo
        st.session_state.subs[i - 1].end = nuovo_tempo

def aggiorna_fine(i):
    if i < 0 or i >= len(st.session_state.subs) - 1: return
    nuovo_tempo = parse_srt_time(st.session_state.get(f"end_{i}"))
    if nuovo_tempo:
        st.session_state.subs[i].end = nuovo_tempo
        st.session_state.subs[i + 1].start = nuovo_tempo

def aggiorna_testo(i):
    if i < 0 or i >= len(st.session_state.subs): return
    st.session_state.subs[i].text = st.session_state.get(f"text_{i}", "")

def elimina_blocco(i):
    st.session_state.subs.pop(i)
    riordina_indici()
    applica_vincoli_timeline_continua()

def sposta_su(i):
    if i > 0:
        testo_temp = st.session_state.subs[i].text
        st.session_state.subs[i].text = st.session_state.subs[i - 1].text
        st.session_state.subs[i - 1].text = testo_temp

def sposta_giu(i):
    if i < len(st.session_state.subs) - 1:
        testo_temp = st.session_state.subs[i].text
        st.session_state.subs[i].text = st.session_state.subs[i + 1].text
        st.session_state.subs[i + 1].text = testo_temp

def aggiungi_blocco_intermedio(i):
    sub = st.session_state.subs[i]
    mid_ordinal = (sub.start.ordinal + sub.end.ordinal) // 2
    mid_time = pysrt.SubRipTime.from_ordinal(mid_ordinal)
    sub.end = mid_time
    nuovo_sub = pysrt.SubRipItem(index=0, start=mid_time, end=sub.end, text="")
    st.session_state.subs.insert(i + 1, nuovo_sub)
    riordina_indici()
    applica_vincoli_timeline_continua()
import streamlit as st
import pysrt
from src.utils.helpers import parse_srt_time
from src.core.timeline_manager import reorder_indices, apply_continuous_timeline

def update_start(i):
    if i <= 0 or i >= len(st.session_state.subs): return
    new_time = parse_srt_time(st.session_state.get(f"start_{i}"))
    if new_time:
        st.session_state.subs[i].start = new_time
        st.session_state.subs[i - 1].end = new_time

def update_end(i):
    if i < 0 or i >= len(st.session_state.subs) - 1: return
    new_time = parse_srt_time(st.session_state.get(f"end_{i}"))
    if new_time:
        st.session_state.subs[i].end = new_time
        st.session_state.subs[i + 1].start = new_time

def update_text(i):
    if i < 0 or i >= len(st.session_state.subs): return
    sub = st.session_state.subs[i]
    new_text = st.session_state.get(f"text_{i}", "")
    if sub.text != new_text:
        if hasattr(sub, 'word_timings'):
            delattr(sub, 'word_timings')
    sub.text = new_text

def delete_block(i):
    st.session_state.subs.pop(i)
    reorder_indices()
    apply_continuous_timeline()

def insert_intermediate_block(i):
    sub = st.session_state.subs[i]
    mid_ordinal = (sub.start.ordinal + sub.end.ordinal) // 2
    mid_time = pysrt.SubRipTime.from_ordinal(mid_ordinal)
    old_end = sub.end                # preserve the original end
    sub.end = mid_time               # shorten the current block
    new_sub = pysrt.SubRipItem(index=0, start=mid_time, end=old_end, text="")
    st.session_state.subs.insert(i + 1, new_sub)
    reorder_indices()
    apply_continuous_timeline()
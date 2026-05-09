import pysrt
import streamlit as st

def apply_continuous_timeline():
    if getattr(st.session_state, 'subs', None) is None or len(st.session_state.subs) == 0:
        return

    st.session_state.subs[0].start = pysrt.SubRipTime(0)

    if st.session_state.video_duration.ordinal > 0:
         st.session_state.subs[-1].end = st.session_state.video_duration

    for i in range(len(st.session_state.subs) - 1):
         st.session_state.subs[i].end = st.session_state.subs[i + 1].start


def reorder_indices():
    for idx, sub in enumerate(st.session_state.subs):
        sub.index = idx + 1
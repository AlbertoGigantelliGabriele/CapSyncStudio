import pysrt
import streamlit as st

def apply_continuous_timeline():
    """Rende la timeline continua a livello di parola e aggiorna i testi dei blocchi."""
    if getattr(st.session_state, 'subs', None) is None or len(st.session_state.subs) == 0:
        return

    # Appiattisci tutte le parole in un'unica lista ordinata
    all_words = []   # (block_idx, word_idx, word_text, start_ms, end_ms)
    for i, sub in enumerate(st.session_state.subs):
        if hasattr(sub, 'word_timings') and sub.word_timings:
            for j, (w_text, ws, we) in enumerate(sub.word_timings):
                all_words.append((i, j, w_text, ws, we))

    # Collega le parole consecutive
    for idx in range(1, len(all_words)):
        prev_block, prev_word, prev_text, prev_start, prev_end = all_words[idx-1]
        cur_block, cur_word, cur_text, cur_start, cur_end = all_words[idx]

        # Imposta fine precedente = inizio corrente (se necessario)
        if prev_end != cur_start:
            st.session_state.subs[prev_block].word_timings[prev_word] = (
                prev_text, prev_start, cur_start
            )
            st.session_state.subs[cur_block].word_timings[cur_word] = (
                cur_text, cur_start, cur_end
            )

    # Rigenera i testi e i limiti dei blocchi
    for i, sub in enumerate(st.session_state.subs):
        if hasattr(sub, 'word_timings') and sub.word_timings:
            sub.start = pysrt.SubRipTime.from_ordinal(sub.word_timings[0][1])
            sub.end   = pysrt.SubRipTime.from_ordinal(sub.word_timings[-1][2])
            sub.text  = ' '.join(w[0] for w in sub.word_timings)


def reorder_indices():
    for idx, sub in enumerate(st.session_state.subs):
        sub.index = idx + 1
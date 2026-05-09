import streamlit as st
import pysrt
from src.utils.helpers import parse_srt_time
from src.core.timeline_manager import reorder_indices, apply_continuous_timeline


# ======================== MODIFICA TESTO ========================
def update_word_text(i, j, new_val):
    """Aggiorna il testo di una parola senza rompere i tempi."""
    sub = st.session_state.subs[i]
    words = sub.word_timings
    old_word, old_start, old_end = words[j]

    if new_val == old_word:
        return False  # Nessuna modifica reale

    words[j] = (new_val, old_start, old_end)
    sub.text = ' '.join(w[0] for w in words)
    return True


# ======================== MODIFICA TIMING ========================
def update_word_start(i, j, new_val_str):
    """Modifica lo start applicando le regole temporali."""
    new_time = parse_srt_time(new_val_str)
    if new_time is None:
        return False

    sub = st.session_state.subs[i]
    words = sub.word_timings
    word_text, old_start, old_end = words[j]
    new_start_ms = max(0, new_time.ordinal)  # REGOLA: Mai negativo

    # REGOLA: Lo start non può scavalcare l'end
    if new_start_ms >= old_end:
        new_start_ms = old_end - 10  # Lascia 10ms di margine

    words[j] = (word_text, new_start_ms, old_end)

    if j == 0:
        sub.start = pysrt.SubRipTime.from_ordinal(new_start_ms)

    apply_continuous_timeline()
    return True


def update_word_end(i, j, new_val_str):
    """Modifica la fine applicando le regole temporali."""
    new_time = parse_srt_time(new_val_str)
    if new_time is None:
        return False

    sub = st.session_state.subs[i]
    words = sub.word_timings
    word_text, old_start, old_end = words[j]
    new_end_ms = new_time.ordinal

    # REGOLA: L'end non può essere precedente allo start
    if new_end_ms <= old_start:
        new_end_ms = old_start + 10

    words[j] = (word_text, old_start, new_end_ms)

    if j == len(words) - 1:
        sub.end = pysrt.SubRipTime.from_ordinal(new_end_ms)

    apply_continuous_timeline()
    return True


# ======================== AZIONI STRUTTURALI ========================
def merge_words(i, j):
    """Fonde la parola j con la j+1 (o con la prima parola del blocco successivo)."""
    subs = st.session_state.subs
    sub = subs[i]
    words = sub.word_timings

    # CASO A: Fondere con la parola successiva nello stesso blocco
    if j < len(words) - 1:
        w1_text, w1_start, _ = words[j]
        w2_text, _, w2_end = words[j + 1]

        words[j] = (f"{w1_text} {w2_text}".strip(), w1_start, w2_end)
        words.pop(j + 1)
        sub.text = ' '.join(w[0] for w in words)
        sub.end = pysrt.SubRipTime.from_ordinal(words[-1][2])

    # CASO B: Fondere l'ultima parola del blocco con la prima del blocco seguente
    elif i < len(subs) - 1:
        next_sub = subs[i + 1]
        if hasattr(next_sub, 'word_timings') and next_sub.word_timings:
            w1_text, w1_start, _ = words[j]
            w2_text, _, w2_end = next_sub.word_timings[0]

            words[j] = (f"{w1_text} {w2_text}".strip(), w1_start, w2_end)
            next_sub.word_timings.pop(0)

            if not next_sub.word_timings:
                subs.pop(i + 1)  # Elimina blocco vuoto
            else:
                next_sub.text = ' '.join(w[0] for w in next_sub.word_timings)
                next_sub.start = pysrt.SubRipTime.from_ordinal(next_sub.word_timings[0][1])

            sub.text = ' '.join(w[0] for w in words)
            sub.end = pysrt.SubRipTime.from_ordinal(words[-1][2])

    reorder_indices()
    apply_continuous_timeline()


def insert_word(i, j):
    """Divide a metà il tempo della parola corrente e crea uno spazio vuoto."""
    sub = st.session_state.subs[i]
    words = sub.word_timings

    cur_text, cur_start, cur_end = words[j]
    mid_time = (cur_start + cur_end) // 2

    # Riduce la parola originale al primo 50%
    words[j] = (cur_text, cur_start, mid_time)
    # Inserisce la nuova parola (vuota) nel secondo 50%
    words.insert(j + 1, ("...", mid_time, cur_end))

    sub.text = ' '.join(w[0] for w in words)
    apply_continuous_timeline()


def delete_word(i, j):
    """Elimina la parola e aggiusta l'intero blocco."""
    sub = st.session_state.subs[i]
    words = sub.word_timings

    if len(words) == 1:
        st.session_state.subs.pop(i)  # Se era l'unica, elimino il blocco
        reorder_indices()
    else:
        words.pop(j)
        sub.start = pysrt.SubRipTime.from_ordinal(words[0][1])
        sub.end = pysrt.SubRipTime.from_ordinal(words[-1][2])
        sub.text = ' '.join(w[0] for w in words)

    apply_continuous_timeline()
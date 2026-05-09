import re
import torch
from faster_whisper import WhisperModel
import streamlit as st
import pysrt


@st.cache_resource(show_spinner=False)
def load_whisper_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute = "float16" if device == "cuda" else "int8"
    return WhisperModel("medium", device=device, compute_type=compute)


def generate_subtitles_from_video(video_path, custom_prompt="", max_chars=28, progress_callback=None):
    subs = pysrt.SubRipFile()

    def sec_to_srt_time(seconds):
        h, rem = divmod(int(seconds), 3600)
        m, s = divmod(rem, 60)
        ms = int((seconds - int(seconds)) * 1000)
        return pysrt.SubRipTime(h, m, s, ms)

    model = load_whisper_model()
    # Recuperiamo "info" per sapere la durata totale
    segments, info = model.transcribe(video_path, language="it", initial_prompt=custom_prompt,
                                      beam_size=5, word_timestamps=True)

    total_duration = info.duration
    clean_re = re.compile(r"[,.?!;:]")
    idx = 1
    buf, buf_len, buf_start = [], 0, None

    def flush_buffer(words, start_t, i):
        if not words:
            return None
        clean = [clean_re.sub('', w.word.strip()) for w in words]
        text = " ".join(clean)
        item = pysrt.SubRipItem(index=i, start=sec_to_srt_time(start_t),
                                end=sec_to_srt_time(words[-1].end), text=text)
        item.word_timings = [(clean[j], int(words[j].start * 1000), int(words[j].end * 1000))
                             for j in range(len(words))]
        return item

    for segment in segments:

        # --- LA MAGIA DELLA BARRA DI PROGRESSO ---
        if progress_callback:
            pct = min(segment.end / total_duration, 1.0)
            progress_callback(pct)
        # -----------------------------------------

        for word in segment.words:
            cleaned = clean_re.sub('', word.word.strip())
            if not cleaned:
                continue
            lw = len(cleaned)
            if not buf:
                buf_start = word.start

            if buf and (buf_len + lw + 1 > max_chars):
                new_item = flush_buffer(buf, buf_start, idx)
                if new_item:
                    subs.append(new_item)
                    idx += 1
                buf, buf_len, buf_start = [word], lw, word.start
            else:
                buf.append(word)
                buf_len += lw + (1 if len(buf) > 1 else 0)

    new_item = flush_buffer(buf, buf_start, idx)
    if new_item:
        subs.append(new_item)
    return subs
import re
import torch
from faster_whisper import WhisperModel
import pysrt


def genera_sottotitoli_da_video(video_path, custom_prompt="", mode="Standard"):
    subs = pysrt.SubRipFile()

    def sec_to_srt_time(seconds):
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds - int(seconds)) * 1000)
        return pysrt.SubRipTime(h, m, s, ms)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"

    model = WhisperModel("medium", device=device, compute_type=compute_type)
    segments, _ = model.transcribe(
        video_path,
        language="it",
        initial_prompt=custom_prompt,
        beam_size=5,
        word_timestamps=True
    )

    MAX_CHARS = 28
    indice = 1
    current_words = []
    current_length = 0
    start_time = None

    # 1. Precompiliamo la regex fuori dal loop per maggiore efficienza
    cleaner = re.compile(r"[,.?!;:']")

    # 2. Funzione helper interna per evitare di ripetere la logica di creazione blocco
    def flush_buffer(words_buffer, start_t, idx):
        if not words_buffer:
            return None

        end_t = words_buffer[-1].end

        # Puliamo le parole una volta sola e le riutilizziamo
        parole_pulite = [cleaner.sub('', w.word.strip()) for w in words_buffer]
        testo_blocco = " ".join(parole_pulite)

        item = pysrt.SubRipItem(
            index=idx,
            start=sec_to_srt_time(start_t),
            end=sec_to_srt_time(end_t),
            text=testo_blocco
        )

        # Associamo i timing usando le parole già pulite
        item.word_timings = [(parole_pulite[i], int(w.start * 1000), int(w.end * 1000))
                             for i, w in enumerate(words_buffer)]
        return item

    for segment in segments:
        for word in segment.words:
            testo_parola = cleaner.sub('', word.word.strip())
            lunghezza_parola = len(testo_parola)

            if not current_words:
                start_time = word.start

            if current_words and (current_length + lunghezza_parola + 1 > MAX_CHARS):
                # Raggiunto il limite: svuotiamo il buffer usando la funzione helper
                nuovo_item = flush_buffer(current_words, start_time, indice)
                if nuovo_item:
                    subs.append(nuovo_item)
                    indice += 1

                current_words = [word]
                current_length = lunghezza_parola
                start_time = word.start
            else:
                current_words.append(word)
                current_length += lunghezza_parola + (1 if len(current_words) > 1 else 0)

    # Svuotamento buffer a fine segmento (riutilizziamo la STESSA funzione!)
    nuovo_item = flush_buffer(current_words, start_time, indice)
    if nuovo_item:
        subs.append(nuovo_item)

    return subs
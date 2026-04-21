import os
import subprocess
import streamlit as st
import pysrt
import re


def applica_sottotitoli(video_input, srt_input, video_output, stile):
    # Capiamo qual è la cartella di lavoro temporanea
    work_dir = os.path.dirname(video_output)

    # Estraiamo SOLO i nomi dei file per evitare errori di path su FFmpeg
    video_input_name = os.path.basename(video_input)
    srt_input_name = os.path.basename(srt_input)
    video_output_name = os.path.basename(video_output)

    filter_script_name = "ffmpeg_filter.txt"
    temp_output_name = "temp_render_ffmpeg.mp4"

    # Il percorso assoluto del file script (che scriviamo da Python)
    filter_script_path = os.path.join(work_dir, filter_script_name)

    with open(filter_script_path, "w", encoding="utf-8") as f:
        # Passiamo solo il nome del file a FFmpeg, lo stile è già dentro il file ASS!
        f.write(f"subtitles={srt_input_name}")

    comando = [
        'ffmpeg', '-y',
        '-i', video_input_name,
        '-filter_script:v', filter_script_name,
        '-c:a', 'copy',
        '-preset', 'fast',  # I parametri di codifica vanno PRIMA dell'output
        temp_output_name  # Il file di output va SEMPRE per ultimo
    ]
    try:
        # cwd=work_dir forza FFmpeg a lavorare DENTRO la cartella temporanea
        subprocess.run(comando, check=True, capture_output=True, cwd=work_dir)

        # Rinominiamo il temp renderizzato nel nome finale richiesto
        os.replace(os.path.join(work_dir, temp_output_name), video_output)
    except subprocess.CalledProcessError as e:
        err_msg = e.stderr.decode('utf-8', errors='ignore')
        st.error(f"FFmpeg Engine Error:\n\n{err_msg}")
        raise e
    finally:
        # Pulizia del file script all'interno della cartella temporanea
        if os.path.exists(filter_script_path):
            os.remove(filter_script_path)


def ottieni_durata_video(video_path):
    if not os.path.exists(video_path):
        return pysrt.SubRipTime(0, 0, 0, 0)
    comando = ['ffmpeg', '-i', video_path]
    result = subprocess.run(comando, capture_output=True, text=True)
    match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d+)", result.stderr)
    if match:
        h, m, s, ms = match.groups()
        ms = int(ms.ljust(3, '0')[:3])
        return pysrt.SubRipTime(int(h), int(m), int(s), ms)
    return pysrt.SubRipTime(0, 0, 0, 0)
import os
import streamlit as st
import subprocess
import pysrt
import re
import json


def get_video_properties(video_path):
    """Legge i metadati del video per capire se è HDR e quanto è grande."""
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,color_space,color_transfer',
            '-of', 'json', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        info = json.loads(result.stdout)
        stream = info.get('streams', [{}])[0]

        width = stream.get('width', 0)
        height = stream.get('height', 0)
        color_space = stream.get('color_space', '')
        color_transfer = stream.get('color_transfer', '')

        # È HDR se il color space o transfer è BT.2020 o SMPTE2084
        is_hdr = 'bt2020' in color_space or 'smpte2084' in color_transfer or 'arib-std-b67' in color_transfer

        # Serve ridimensionare solo se il lato più lungo supera i 1920 pixel
        needs_scaling = max(width, height) > 1920

        return is_hdr, needs_scaling
    except Exception as e:
        # Se qualcosa va storto, assumiamo SDR e nessun ridimensionamento per sicurezza
        print(f"Errore lettura metadati: {e}")
        return False, False


def concatenate_videos(file_paths, output_path):
    list_file = output_path + ".txt"
    with open(list_file, "w", encoding="utf-8") as f:
        for p in file_paths:
            f.write(f"file '{p}'\n")

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', list_file,
        '-c', 'copy',
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode('utf-8', errors='ignore')
        # Fallback with filter concat (re-encode) omitted for brevity
        raise RuntimeError(f"FFmpeg concat error:\n{err}")
    finally:
        if os.path.exists(list_file):
            os.remove(list_file)

def apply_subtitles(video_input, ass_input, video_output, speed=1.0, callback_progress=None):
    work_dir = os.path.dirname(video_output)
    video_in = os.path.basename(video_input)
    ass_in = os.path.basename(ass_input)
    video_out = os.path.basename(video_output)

    # 1. Scopriamo con chi abbiamo a che fare
    is_hdr, needs_scaling = get_video_properties(video_input)

    # 2. Costruiamo la catena di filtri (-vf) come i pezzi di un puzzle
    vf_filters = []

    if needs_scaling:
        # Scala in modo intelligente solo se il video è gigante
        vf_filters.append("scale='if(gt(iw,ih),1920,-2)':'if(gt(iw,ih),-2,1920)'")

    if is_hdr:
        # Applica l'antidoto HDR solo se serve davvero
        vf_filters.append("format=yuv420p,colorspace=all=bt709:iall=bt2020:fast=1")

    # Aggiungiamo i sottotitoli (questo c'è sempre)
    vf_filters.append(f"subtitles={ass_in}")

    if speed != 1.0:
        # Modifica la velocità visiva
        setpts = 1.0 / speed
        vf_filters.append(f"setpts={setpts}*PTS")

    # Uniamo tutti i pezzi separati da virgola
    vf_string = ",".join(vf_filters)

    # 3. Assembliamo il comando finale
    cmd = [
        'ffmpeg', '-y',
        '-i', video_in,
        '-threads', '0',
        '-vf', vf_string,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '23'
    ]

    if speed != 1.0:
        # Se la velocità è diversa, dobbiamo elaborare anche l'audio
        cmd.extend(['-af', f"atempo={speed}", '-c:a', 'aac'])
    else:
        # Altrimenti copiamo l'audio originale senza perdere tempo e qualità
        cmd.extend(['-c:a', 'copy'])

    # Aggiungiamo il file di output alla fine
    cmd.append(video_out)

    try:
        process = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                   universal_newlines=True, cwd=work_dir)
        time_pattern = re.compile(r"time=(\d{2}):(\d{2}):(\d{2})\.\d{2}")
        for line in process.stderr:
            match = time_pattern.search(line)
            if match and callback_progress:
                h, m, s = map(int, match.groups())
                elapsed_sec = h * 3600 + m * 60 + s
                if speed != 1.0:
                    total_sec = (st.session_state.video_duration.ordinal / 1000) / speed
                else:
                    total_sec = st.session_state.video_duration.ordinal / 1000 if st.session_state.video_duration else 1
                pct = min(elapsed_sec / max(total_sec, 1), 1.0)
                callback_progress(pct)
        process.wait()
        if process.returncode != 0:
            raise subprocess.CalledProcessError(process.returncode, cmd)
    except Exception as e:
        raise RuntimeError(f"FFmpeg error: {e}")

def get_video_duration(video_path):
    if not os.path.exists(video_path):
        return pysrt.SubRipTime(0)
    command = ['ffmpeg', '-i', video_path]
    result = subprocess.run(command, capture_output=True, text=True)
    match = re.search(r"Duration: (\d{2}):(\d{2}):(\d{2})\.(\d+)", result.stderr)
    if match:
        h, m, s, ms = match.groups()
        ms = int(ms.ljust(3, '0')[:3])
        return pysrt.SubRipTime(int(h), int(m), int(s), ms)
    return pysrt.SubRipTime(0)
import os
import subprocess
import streamlit as st
import pysrt
import re


def applica_sottotitoli(video_input, ass_input, video_output, speed=1.0):
    work_dir = os.path.dirname(video_output)
    video_in = os.path.basename(video_input)
    ass_in = os.path.basename(ass_input)
    video_out = os.path.basename(video_output)

    if speed == 1.0:
        # Comando normale: solo sottotitoli
        cmd = [
            'ffmpeg', '-y',
            '-i', video_in,
            '-vf', f"subtitles={ass_in}",
            '-c:a', 'copy',
            '-preset', 'fast',
            video_out
        ]
    else:
        # Velocità personalizzata: sottotitoli + setpts video + atempo audio
        setpts = 1.0 / speed
        cmd = [
            'ffmpeg', '-y',
            '-i', video_in,
            '-vf', f"subtitles={ass_in},setpts={setpts}*PTS",
            '-af', f"atempo={speed}",
            '-c:a', 'aac',
            '-preset', 'fast',
            video_out
        ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, cwd=work_dir)
    except subprocess.CalledProcessError as e:
        err = e.stderr.decode('utf-8', errors='ignore')
        raise RuntimeError(f"FFmpeg error:\n{err}")

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
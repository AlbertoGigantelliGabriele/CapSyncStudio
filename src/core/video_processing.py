import os
import streamlit as st
import subprocess
import pysrt
import re

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

    if speed == 1.0:
        # Normal command: only subtitles
        cmd = [
            'ffmpeg', '-y',
            '-i', video_in,
            '-vf', f"subtitles={ass_in}",
            '-c:a', 'copy',
            '-preset', 'fast',
            video_out
        ]
    else:
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
import pysrt
import re

def parse_srt_time(time_str):
    match = re.search(r'(\d+):(\d+):(\d+)[,.](\d+)', str(time_str).strip())
    if match:
        h, m, s, ms = match.groups()
        ms = int(ms.ljust(3, '0')[:3])
        return pysrt.SubRipTime(int(h), int(m), int(s), ms)
    return None

def hex_to_ass_color(hex_color):
    hex_color = hex_color.lstrip('#')
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return f"&H00{b}{g}{r}&"

def format_ass_time(ms):
    total_cs = (ms + 5) // 10                      # total hundredths (truncation)
    h = total_cs // 360000
    m = (total_cs % 360000) // 6000
    s = (total_cs % 6000) // 100
    cs = total_cs % 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def generate_ass_content(subs, highlight_style, highlight_color, base_style, uppercase=False, single_word=False):
    col_highlight = hex_to_ass_color(highlight_color)
    col_base = hex_to_ass_color(base_style['color_hex'])

    zoom = base_style['zoom']
    tag_zoom = f"\\fscx{zoom}\\fscy{zoom}" if zoom != 100 else ""
    tag_reset = "\\fscx100\\fscy100" if tag_zoom else ""

    style_def = (
        f"Style: Default,{base_style['font']},{base_style['size']},{col_base},"
        f"&H000000FF,&H00000000,&H00000000,{base_style['bold']},{base_style['italic']},"
        f"0,0,100,100,0,0,1,{base_style['outline']},0,2,10,10,40,1"
    )
    header = f"""[Script Info]
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{style_def}
"""
    events = []

    for sub in subs:
        text = sub.text.upper() if uppercase else sub.text
        words = text.split()
        if not words:
            continue

        has_timing = hasattr(sub, 'word_timings') and len(sub.word_timings) == len(words)
        word_duration = (sub.end.ordinal - sub.start.ordinal) / len(words)

        for i, w_target in enumerate(words):
            if has_timing:
                t_start, t_end = sub.word_timings[i][1], sub.word_timings[i][2]
            else:
                t_start = sub.start.ordinal + int(i * word_duration)

            if i < len(words) - 1:
                if has_timing:
                    t_end = sub.word_timings[i + 1][1]
                else:
                    t_end = sub.start.ordinal + round((i+1) * word_duration)
            else:
                t_end = sub.end.ordinal

            s_str = format_ass_time(int(t_start))
            e_str = format_ass_time(int(t_end))

            highlight = (highlight_style  == "Colored Text")

            if single_word:
                tags = tag_zoom + (f"\\c{col_highlight}" if highlight else "")
                line_text = f"{{{tags}}}{w_target}" if tags else w_target
            else:
                parts = []
                for j, w in enumerate(words):
                    if j == i and highlight:
                        # Opening: zoom + highlight color
                        opening_tag = f"{{{tag_zoom}\\c{col_highlight}}}"
                        # Closing: reset zoom + base color
                        reset_tags = tag_reset + f"\\c{col_base}"
                        close_tag = f"{{{reset_tags}}}"
                        parts.append(f"{opening_tag}{w}{close_tag}")
                    else:
                        parts.append(w)
                line_text = ' '.join(parts)

            events.append(f"Dialogue: 0,{s_str},{e_str},Default,,0,0,0,,{{\\blur{base_style['glow']}}}{line_text}\n")

    events_header = "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    return header + events_header + "".join(events) + "\n"

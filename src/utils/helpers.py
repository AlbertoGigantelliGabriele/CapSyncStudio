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
    """Converte #RRGGBB in &HBBGGRR& per i tag ASS."""
    hex_color = hex_color.lstrip('#')
    r, g, b = hex_color[0:2], hex_color[2:4], hex_color[4:6]
    return f"&H{b}{g}{r}&"


def genera_contenuto_ass(subs, stile_evidenziazione, colore_highlight, stile_base, maiuscolo=False, parola_singola=False):
    """Genera il file ASS con supporto alla parola singola, Karaoke, Ombra e Zoom."""

    # Colori ASS
    col_highlight = hex_to_ass_color(colore_highlight)
    col_base = hex_to_ass_color(stile_base['color_hex']).rstrip('&')

    # Tag zoom
    zoom = stile_base['zoom']
    tag_zoom = f"\\fscx{zoom}\\fscy{zoom}" if zoom != 100 else ""
    tag_reset = "\\fscx100\\fscy100" if tag_zoom else ""

    # Header
    stile_def = (
        f"Style: Default,{stile_base['font']},{stile_base['size']},{col_base},"
        f"&H000000FF,&H00000000,&H00000000,{stile_base['bold']},{stile_base['italic']},"
        f"0,0,100,100,0,0,1,{stile_base['outline']},0,2,10,10,40,1"
    )
    header = f"""[Script Info]
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{stile_def}
"""
    events = []

    for sub in subs:
        testo = sub.text.upper() if maiuscolo else sub.text
        parole = testo.split()
        if not parole:
            continue

        timing_reali = hasattr(sub, 'word_timings') and len(sub.word_timings) == len(parole)
        durata_parola = (sub.end.ordinal - sub.start.ordinal) / len(parole)

        for i, w_target in enumerate(parole):
            if timing_reali:
                t_start, t_end = sub.word_timings[i][1], sub.word_timings[i][2]
            else:
                t_start = sub.start.ordinal + int(i * durata_parola)
                t_end   = sub.start.ordinal + int((i+1) * durata_parola)

            s_str = str(pysrt.SubRipTime.from_ordinal(int(t_start))).replace(',', '.')[:-1]
            e_str = str(pysrt.SubRipTime.from_ordinal(int(t_end))).replace(',', '.')[:-1]

            # Evidenziazione karaoke
            evidenzia = (stile_evidenziazione == "Testo Colorato (Karaoke)")
            if parola_singola:
                colore_tag = f"\\c{col_highlight}" if evidenzia else ""
                testo_riga = f"{{{tag_zoom}{colore_tag}}}{w_target}"
            else:
                parti = []
                for j, w in enumerate(parole):
                    if j == i and evidenzia:
                        parti.append(f"{{{tag_zoom}\\c{col_highlight}}}{w}{{{tag_reset}\\c{col_base}}}")
                    else:
                        parti.append(w)
                testo_riga = ' '.join(parti)

            events.append(f"Dialogue: 0,{s_str},{e_str},Default,,0,0,0,,{{\\blur{stile_base['glow']}}}{testo_riga}\n")

    events_header = "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    return header + events_header + "".join(events)

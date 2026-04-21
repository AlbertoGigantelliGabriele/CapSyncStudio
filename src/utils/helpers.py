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


def genera_contenuto_ass(subs_originali, stile_evidenziazione, colore_highlight, stile_base, maiuscolo=False, parola_singola=False):
    """Genera il file ASS finale con supporto alla parola singola, Karaoke dinamico, Ombra e Zoom."""

    ass_color_highlight = hex_to_ass_color(colore_highlight)
    ass_color_testo_base = hex_to_ass_color(stile_base['color_hex'])

    color_base = ass_color_testo_base.rstrip('&')

    # Header aggiornato con Outline dinamico
    header = f"""[Script Info]
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{stile_base['font']},{stile_base['size']},{color_base},&H000000FF,&H00000000,&H00000000,{stile_base['bold']},{stile_base['italic']},0,0,100,100,0,0,1,{stile_base['outline']},0,2,10,10,40,1
"""
    # events = "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    event_lines = []

    # Definiamo i tag di Zoom dinamici PRIMA di entrare nel ciclo, usando il dizionario stile_base
    usa_zoom = stile_base['zoom'] != 100
    tag_zoom = f"\\fscx{stile_base['zoom']}\\fscy{stile_base['zoom']}" if usa_zoom else ""
    tag_reset = "\\fscx100\\fscy100" if usa_zoom else ""

    for sub in subs_originali:
        testo = sub.text
        if maiuscolo: testo = testo.upper()
        parole = testo.split()
        if not parole: continue

        usa_timing_reali = hasattr(sub, 'word_timings') and len(sub.word_timings) == len(parole)
        durata_per_parola = (sub.end.ordinal - sub.start.ordinal) / len(parole)

        for i, w_target in enumerate(parole):
            if usa_timing_reali:
                t_start, t_end = sub.word_timings[i][1], sub.word_timings[i][2]
            else:
                t_start = sub.start.ordinal + int(i * durata_per_parola)
                t_end = sub.start.ordinal + int((i + 1) * durata_per_parola)

            s_str = str(pysrt.SubRipTime.from_ordinal(t_start)).replace(',', '.')[:-1]
            e_str = str(pysrt.SubRipTime.from_ordinal(t_end)).replace(',', '.')[:-1]

            # BIVIO DI STILE: Parola Singola vs Frase Intera
            if parola_singola:
                tag_colore = f"\\c{ass_color_highlight}" if stile_evidenziazione == "Testo Colorato (Karaoke)" else ""
                # Applichiamo i tag generati dinamicamente
                riga_finale = f"{{{tag_zoom}{tag_colore}}}{w_target}"
            else:
                riga_formattata = []
                for j, w in enumerate(parole):
                    if i == j:
                        if stile_evidenziazione == "Testo Colorato (Karaoke)":
                            # Applichiamo i tag generati dinamicamente
                            riga_formattata.append(
                                f"{{{tag_zoom}\\c{ass_color_highlight}}}{w}{{{tag_reset}\\c{ass_color_testo_base}}}")
                        else:
                            riga_formattata.append(w)
                    else:
                        riga_formattata.append(w)
                riga_finale = ' '.join(riga_formattata)

            # Iniezione del Blur dinamico sulla riga finale stampata a video
            # events += f"Dialogue: 0,{s_str},{e_str},Default,,0,0,0,,{{\\blur{stile_base['glow']}}}{riga_finale}\n"
            event_lines.append(
                f"Dialogue: 0,{s_str},{e_str},Default,,0,0,0,,{{\\blur{stile_base['glow']}}}{riga_finale}\n")

    events_header = "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    return header + events_header + "".join(event_lines)

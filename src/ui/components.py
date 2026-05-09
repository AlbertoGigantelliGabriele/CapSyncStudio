import streamlit as st

def apply_global_css():
    st.markdown("""
        <style>
        video {
            max-height: 70vh !important;
            width: auto !important;
            margin: 0 auto;
            display: block;
        }
        .block-container {
            padding-top: 2rem !important;
            padding-bottom: 1rem !important;
        }
        </style>
    """, unsafe_allow_html=True)

def render_video_timer():
    st.html("""
        <style>
            #tbtn {
                width: 100%; min-height: 38px; margin-top: 8px; cursor: pointer;
                background: transparent; border: 1px solid rgba(128,128,128,0.5);
                border-radius: 0.5rem; color: var(--text-color); font-family: inherit;
                display: flex; align-items: center; justify-content: center; gap: 8px; transition: 0.2s;
            }
            #tbtn:hover { border-color: #ff4b4b; color: #ff4b4b; }
        </style>
        <button id="tbtn"><span id="tdsp">00:00:00,000</span> <span id="tico">📋</span></button>
        <script>
            if(window.iv) clearInterval(window.iv);
            window.iv = setInterval(() => {
                let v=document.querySelector('video'), b=document.getElementById('tbtn'), d=document.getElementById('tdsp'), i=document.getElementById('tico');
                if(v && d) d.innerText = new Date(v.currentTime*1000).toISOString().slice(11,23).replace('.',',');
                if(b && !b.on) {
                    b.onclick = () => {
                        let t=document.createElement('textarea'); t.value=d.innerText; document.body.appendChild(t); t.select(); document.execCommand('copy'); t.remove();
                        b.style.color=b.style.borderColor='#28a745'; i.innerText='✅';
                        setTimeout(()=>{ b.style.color=b.style.borderColor=''; i.innerText='📋'; }, 800);
                    }; b.on=1;
                }
            }, 50);
        </script>
    """, unsafe_allow_javascript=True)

def render_style_preview(chosen_font, chosen_size, fw, fs, tt, chosen_color):
    st.markdown(f"""
        <div style="
            margin-top: 15px; padding: 15px;
            background-color: rgba(0, 0, 0, 0.25);
            border: 1px solid rgba(128,128,128,0.3);
            border-radius: 8px; text-align: center;
            font-family: '{chosen_font}';
            font-size: {chosen_size}px; font-weight: {fw}; font-style: {fs};
            text-transform: {tt}; color: {chosen_color};
        ">
            Subtitle Preview
        </div>
    """, unsafe_allow_html=True)

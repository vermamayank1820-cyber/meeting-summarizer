"""
Meeting Summarizer — Production UI v2
Clean light-mode Streamlit interface with streaming chat.
"""
import time
from pathlib import Path

import requests
import streamlit as st

API_BASE      = "http://localhost:8000"
POLL_INTERVAL = 5   # seconds between status polls

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Meeting Summarizer",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,wght@0,300;0,400;0,500;0,600;0,700;1,400&display=swap');

/* ── Base reset ───────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
    background-color: #F8F9FA !important;
    color: #0F172A !important;
}
* { box-sizing: border-box; }

/* ── Hide Streamlit chrome ────────────────────────────────────────────── */
#MainMenu, footer, header, [data-testid="stDecoration"] { visibility: hidden; }
.stDeployButton { display: none !important; }
section[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── Scrollbar ────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }

/* ═══ TOPBAR ══════════════════════════════════════════════════════════════ */
.topbar {
    background: #fff;
    border-bottom: 1px solid #E2E8F0;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 36px;
    position: sticky;
    top: 0;
    z-index: 999;
    box-shadow: 0 1px 4px rgba(0,0,0,.04);
}
.topbar-left  { display: flex; align-items: center; gap: 12px; }
.topbar-icon  {
    width: 34px; height: 34px;
    background: #0F172A;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 16px; line-height: 1;
}
.topbar-name  { font-size: .9375rem; font-weight: 700; color: #0F172A; letter-spacing: -.02em; }
.topbar-sub   { font-size: .72rem; color: #94A3B8; margin-top: 1px; }
.topbar-chip  {
    font-size: .7rem; font-weight: 600; letter-spacing: .01em;
    background: #F1F5F9; color: #64748B;
    border: 1px solid #E2E8F0;
    padding: 4px 10px; border-radius: 20px;
}
.topbar-chip.green { background: #F0FDF4; color: #16A34A; border-color: #BBF7D0; }
.topbar-chip.red   { background: #FEF2F2; color: #DC2626; border-color: #FECACA; }

/* ═══ LAYOUT ══════════════════════════════════════════════════════════════ */
.page { max-width: 1260px; margin: 0 auto; padding: 28px 36px 72px; }

/* ═══ STAT TILES ══════════════════════════════════════════════════════════ */
.stat-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 28px; }
.stat-tile {
    background: #fff;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 18px 22px;
}
.stat-val  { font-size: 1.625rem; font-weight: 700; color: #0F172A; letter-spacing: -.03em; line-height: 1; }
.stat-lbl  { font-size: .7rem; font-weight: 600; color: #94A3B8; text-transform: uppercase; letter-spacing: .06em; margin-top: 7px; }

/* ═══ TABS ════════════════════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    gap: 0; background: transparent !important;
    border-bottom: 1.5px solid #E2E8F0 !important;
    padding: 0; margin-bottom: 24px;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    color: #64748B !important;
    font-size: .875rem !important; font-weight: 500 !important;
    padding: 11px 18px !important; margin: 0 !important; border-radius: 0 !important;
    transition: all .15s;
}
.stTabs [data-baseweb="tab"]:hover { color: #0F172A !important; }
.stTabs [aria-selected="true"] {
    color: #0F172A !important;
    border-bottom: 2px solid #0F172A !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ═══ CARDS ═══════════════════════════════════════════════════════════════ */
.card {
    background: #fff;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 10px;
    transition: box-shadow .18s, border-color .18s;
}
.card:hover { box-shadow: 0 4px 14px rgba(0,0,0,.06); border-color: #CBD5E1; }
.card-title { font-size: .9375rem; font-weight: 600; color: #0F172A; letter-spacing: -.01em; }
.card-meta  {
    display: flex; flex-wrap: wrap; gap: 14px;
    font-size: .78rem; color: #94A3B8; margin-top: 5px;
}
.card-excerpt {
    font-size: .8375rem; color: #475569; line-height: 1.65;
    margin-top: 10px; padding-top: 10px; border-top: 1px solid #F1F5F9;
}

/* ═══ BADGES ══════════════════════════════════════════════════════════════ */
.badge {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 3px 9px; border-radius: 20px;
    font-size: .7rem; font-weight: 600; white-space: nowrap;
}
.badge-ok   { background: #F0FDF4; color: #15803D; }
.badge-proc { background: #FFFBEB; color: #B45309; }
.badge-fail { background: #FEF2F2; color: #B91C1C; }

/* ═══ UPLOAD ZONE ═════════════════════════════════════════════════════════ */
div[data-testid="stFileUploader"] > div {
    background: #FAFAFA !important;
    border: 2px dashed #CBD5E1 !important;
    border-radius: 12px !important;
    transition: all .2s !important;
    padding: 24px !important;
}
div[data-testid="stFileUploader"] > div:hover {
    border-color: #94A3B8 !important;
    background: #F1F5F9 !important;
}
div[data-testid="stFileUploaderDropzoneInstructions"] > div > small { display: none; }

/* ═══ BUTTONS ═════════════════════════════════════════════════════════════ */
.stButton > button {
    background: #0F172A !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: .875rem !important;
    font-weight: 500 !important;
    padding: 10px 20px !important;
    letter-spacing: -.01em !important;
    transition: all .15s !important;
    box-shadow: 0 1px 3px rgba(0,0,0,.1) !important;
}
.stButton > button:hover {
    background: #1E293B !important;
    box-shadow: 0 4px 12px rgba(0,0,0,.18) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: none !important; }
.btn-ghost > button {
    background: #fff !important; color: #374151 !important;
    border: 1px solid #D1D5DB !important; box-shadow: none !important;
}
.btn-ghost > button:hover {
    background: #F9FAFB !important; box-shadow: none !important; transform: none !important;
}

/* ═══ RADIO (fix label visibility) ════════════════════════════════════════ */
div[data-testid="stRadio"] label {
    background: #fff !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 8px 14px !important;
    cursor: pointer !important;
    transition: all .15s !important;
    font-size: .875rem !important;
    color: #374151 !important;
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #F0FDF4 !important;
    border-color: #86EFAC !important;
    color: #15803D !important;
    font-weight: 600 !important;
}
div[data-testid="stRadio"] > div { gap: 8px !important; }

/* ═══ PROGRESS BAR ════════════════════════════════════════════════════════ */
.stProgress > div > div { background: #E2E8F0 !important; border-radius: 4px !important; height: 5px !important; }
.stProgress > div > div > div { background: linear-gradient(90deg,#0F172A,#334155) !important; border-radius: 4px !important; }

/* ═══ SELECT BOX ══════════════════════════════════════════════════════════ */
.stSelectbox > div > div { border-radius: 8px !important; border-color: #D1D5DB !important; font-size: .875rem !important; }

/* ═══ TEXT AREA ═══════════════════════════════════════════════════════════ */
.stTextArea textarea {
    font-family: 'Inter', monospace !important; font-size: .8rem !important;
    color: #374151 !important; background: #FAFAFA !important;
    border: 1px solid #E2E8F0 !important; border-radius: 8px !important;
    line-height: 1.75 !important;
}

/* ═══ DATA TABLE ══════════════════════════════════════════════════════════ */
div[data-testid="stDataFrame"] {
    border-radius: 10px !important; overflow: hidden !important; border: 1px solid #E2E8F0 !important;
}
div[data-testid="stDataFrame"] th {
    background: #F8FAFC !important; font-weight: 600 !important; color: #64748B !important;
    font-size: .72rem !important; text-transform: uppercase !important; letter-spacing: .05em !important;
}

/* ═══ SUMMARY BLOCKS ══════════════════════════════════════════════════════ */
.sum-card {
    background: #fff; border: 1px solid #E2E8F0; border-radius: 12px;
    padding: 18px 20px; margin-bottom: 14px;
}
.sum-card-title {
    font-size: .69rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .07em; color: #94A3B8; margin-bottom: 12px;
}
.sum-overview { font-size: .9375rem; color: #1E293B; line-height: 1.75; }
.bullet-row {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 7px 0; border-bottom: 1px solid #F8FAFC;
    font-size: .875rem; color: #334155; line-height: 1.55;
}
.bullet-row:last-child { border-bottom: none; }
.dot { width: 6px; height: 6px; border-radius: 50%; background: #CBD5E1; margin-top: 7px; flex-shrink: 0; }
.dot-g { background: #86EFAC; }
.dot-r { background: #FCA5A5; }
.dot-b { background: #93C5FD; }
.dot-y { background: #FDE68A; }

/* ═══ CHAT ════════════════════════════════════════════════════════════════ */
[data-testid="stChatMessage"] {
    background: #fff !important; border: 1px solid #E2E8F0 !important;
    border-radius: 12px !important; padding: 14px 18px !important;
    margin-bottom: 10px !important; font-size: .875rem !important;
}
[data-testid="stChatMessage"][data-testid*="user"] { background: #F8FAFC !important; }
.stChatInputContainer > div {
    border: 1.5px solid #D1D5DB !important; border-radius: 12px !important;
    background: #fff !important;
}
.stChatInputContainer textarea { font-size: .875rem !important; }

/* ═══ PULSE ANIMATION ═════════════════════════════════════════════════════ */
.pulse-dot {
    display: inline-block; width: 8px; height: 8px;
    background: #F59E0B; border-radius: 50%;
    animation: pulse 1.4s infinite;
}
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:.35; transform:scale(.8); }
}

/* ═══ ETA BOX ═════════════════════════════════════════════════════════════ */
.eta-box {
    display: flex; align-items: center; gap: 10px;
    background: #FFFBEB; border: 1px solid #FDE68A;
    border-radius: 8px; padding: 10px 14px;
    font-size: .8125rem; color: #92400E; font-weight: 500; margin-top: 10px;
}

/* ═══ SECTION LABELS ══════════════════════════════════════════════════════ */
.section-lbl {
    font-size: .69rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: .08em; color: #94A3B8; margin-bottom: 14px;
}

/* ═══ SENTIMENT ═══════════════════════════════════════════════════════════ */
.sent-positive { background:#F0FDF4; color:#15803D; padding:2px 9px; border-radius:20px; font-size:.72rem; font-weight:600; }
.sent-neutral  { background:#FFFBEB; color:#B45309; padding:2px 9px; border-radius:20px; font-size:.72rem; font-weight:600; }
.sent-negative { background:#FEF2F2; color:#B91C1C; padding:2px 9px; border-radius:20px; font-size:.72rem; font-weight:600; }
</style>
""", unsafe_allow_html=True)


# ─── API helpers ─────────────────────────────────────────────────────────────
def api_get(endpoint: str):
    try:
        r = requests.get(f"{API_BASE}{endpoint}", timeout=12)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def api_post_form(endpoint: str, data: dict) -> dict | None:
    try:
        r = requests.post(f"{API_BASE}{endpoint}", data=data, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


def api_upload(file_bytes, filename: str, style: str) -> dict | None:
    try:
        r = requests.post(
            f"{API_BASE}/upload",
            files={"file": (filename, file_bytes)},
            data={"summary_style": style},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Upload failed: {e}")
        return None


def stream_chat(meeting_id: str, question: str):
    """Generator: yields text chunks from the streaming chat endpoint."""
    try:
        with requests.post(
            f"{API_BASE}/meetings/{meeting_id}/chat",
            data={"question": question},
            stream=True, timeout=90,
        ) as r:
            if r.status_code != 200:
                yield f"Error {r.status_code}: {r.text}"
                return
            for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    yield chunk
    except Exception as e:
        yield f"\n⚠️ Connection error: {e}"


def is_api_up() -> bool:
    try:
        return requests.get(f"{API_BASE}/health", timeout=2).status_code == 200
    except Exception:
        return False


def size_to_eta(size_bytes: int) -> str:
    mb = size_bytes / 1024 / 1024
    if mb < 10:   return "~1–2 min"
    if mb < 25:   return "~2–4 min"
    if mb < 100:  return "~4–7 min"
    return "~7–12 min"


# ─── Top bar ─────────────────────────────────────────────────────────────────
api_up   = is_api_up()
api_chip = "green" if api_up else "red"
api_txt  = "API :8000" if api_up else "API offline"

st.markdown(f"""
<div class="topbar">
  <div class="topbar-left">
    <div class="topbar-icon">🎙️</div>
    <div>
      <div class="topbar-name">Meeting Summarizer</div>
      <div class="topbar-sub">AI-powered transcription &amp; analysis</div>
    </div>
  </div>
  <div style="display:flex;gap:8px;align-items:center">
    <div class="topbar-chip {api_chip}">● {api_txt}</div>
    <div class="topbar-chip">GPT-4o · Whisper</div>
  </div>
</div>
<div class="page">
""", unsafe_allow_html=True)

if not api_up:
    st.error("⚠️ API server is not running. Start it with: `python -m uvicorn api.main:app --port 8000 --reload`")
    st.stop()

# ─── Stats row ────────────────────────────────────────────────────────────────
data_all  = api_get("/meetings?limit=500") or {}
all_mtgs  = data_all.get("meetings", [])
done      = [m for m in all_mtgs if m.get("status") == "completed"]
tot_secs  = sum(float(m.get("duration_secs") or 0) for m in done)
hrs, rem  = divmod(int(tot_secs), 3600)
mins      = rem // 60

c1, c2, c3, c4 = st.columns(4)
for col, val, lbl in [
    (c1, len(all_mtgs), "Total Meetings"),
    (c2, len(done),     "Processed"),
    (c3, f"{hrs}h {mins}m" if hrs else f"{mins}m" if mins else "—", "Audio Processed"),
    (c4, "GPT-4o",     "LLM Engine"),
]:
    with col:
        st.markdown(
            f'<div class="stat-tile"><div class="stat-val">{val}</div>'
            f'<div class="stat-lbl">{lbl}</div></div>', unsafe_allow_html=True
        )

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ─── Main tabs ────────────────────────────────────────────────────────────────
t_upload, t_meetings, t_view = st.tabs(["⬆ Upload Recording", "📋 All Meetings", "📄 Summary & Chat"])


# ══════════════════════════════════════════════════════════════════════
# TAB 1 — UPLOAD
# ══════════════════════════════════════════════════════════════════════
with t_upload:
    st.markdown('<div class="section-lbl">New Recording</div>', unsafe_allow_html=True)

    col_up, col_opts = st.columns([2.2, 1], gap="large")

    with col_up:
        uploaded = st.file_uploader(
            "Drop your meeting recording here, or click to browse",
            type=["mp4","mp3","wav","m4a","webm","ogg","mkv","mov"],
            label_visibility="collapsed",
        )
        st.markdown("""
        <div style="margin-top:8px;font-size:.76rem;color:#94A3B8;">
          Supported: <b>MP4 MP3 WAV M4A WebM OGG MKV MOV</b>
          &nbsp;·&nbsp; Files &gt;25 MB are auto-chunked — no size limit
        </div>
        """, unsafe_allow_html=True)

    with col_opts:
        st.markdown('<div style="font-size:.78rem;font-weight:600;color:#64748B;text-transform:uppercase;letter-spacing:.06em;margin-bottom:8px">Summary Style</div>', unsafe_allow_html=True)
        style = st.radio(
            "Summary Style",
            options=["executive", "detailed"],
            format_func=lambda x: ("⚡  Executive — concise & actionable"
                                   if x == "executive" else
                                   "📋  Detailed — every decision & owner"),
            label_visibility="collapsed",
        )
        st.markdown(f"""
        <div style="font-size:.76rem;color:#94A3B8;margin-top:8px;line-height:1.6">
          {'<b>Executive</b>: McKinsey-style brief, key insights only.' if style=="executive"
           else '<b>Detailed</b>: Full breakdown — all risks, owners, timeline.'}
        </div>
        """, unsafe_allow_html=True)

    if uploaded:
        size_bytes = uploaded.size
        eta        = size_to_eta(size_bytes)
        size_str   = f"{size_bytes/1024/1024:.1f} MB"

        st.markdown(f"""
        <div class="card" style="display:flex;align-items:center;gap:14px;padding:14px 18px;margin-top:14px">
          <div style="background:#F1F5F9;border-radius:8px;padding:10px 12px;font-size:1.5rem">🎬</div>
          <div style="flex:1">
            <div style="font-size:.9rem;font-weight:600;color:#0F172A">{uploaded.name}</div>
            <div style="font-size:.76rem;color:#94A3B8;margin-top:2px">{size_str} · Ready to process</div>
          </div>
          <span class="badge badge-proc">Selected</span>
        </div>
        <div class="eta-box">
          ⏱ Estimated processing time: <strong>{eta}</strong>
          &nbsp;—&nbsp; Audio is extracted &amp; transcribed in parallel chunks
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Process Recording →"):
            with st.spinner("Uploading…"):
                result = api_upload(uploaded.getvalue(), uploaded.name, style)

            if result:
                mid = result["meeting_id"]
                eta = result.get("estimated_time", "a few minutes")
                st.session_state["last_job_id"] = mid

                st.markdown(f"""
                <div class="card" style="border-color:#BBF7D0;background:#F0FDF4;margin-top:8px">
                  <div style="font-size:.875rem;font-weight:600;color:#15803D">✅ Upload successful</div>
                  <div style="font-size:.78rem;color:#6B7280;margin-top:3px">
                    Job ID: <code style="background:#E2E8F0;padding:1px 6px;border-radius:4px">{mid}</code>
                    &nbsp;·&nbsp; Est. {eta}
                  </div>
                </div>
                """, unsafe_allow_html=True)

                prog_bar   = st.progress(0.0)
                status_ph  = st.empty()

                for i in range(360):
                    time.sleep(POLL_INTERVAL)
                    resp   = api_get(f"/status/{mid}")
                    status = (resp or {}).get("status", "unknown")

                    if status == "completed":
                        prog_bar.progress(1.0)
                        status_ph.markdown("""
                        <div class="card" style="border-color:#BBF7D0;background:#F0FDF4">
                          <div style="font-size:.9rem;font-weight:600;color:#15803D">🎉 Summary is ready!</div>
                          <div style="font-size:.8rem;color:#6B7280;margin-top:3px">
                            Switch to <b>Summary &amp; Chat</b> to view results and ask questions.
                          </div>
                        </div>
                        """, unsafe_allow_html=True)
                        st.balloons()
                        break
                    elif status.startswith("failed"):
                        prog_bar.progress(0.0)
                        stage = status.replace("failed: ","").replace("failed_","")
                        status_ph.error(f"❌ Pipeline failed at **{stage}**. Check the API logs for details.")
                        break
                    else:
                        # Smooth fake progress: 5% → 90%
                        p = min(0.9, 0.05 + i * 0.012)
                        prog_bar.progress(p)
                        pct   = int(p * 100)
                        stage_msg = {
                            "queued":     "⏳ Queued — waiting to start",
                            "processing": "⚙️ Transcribing → Cleaning → Summarizing",
                        }.get(status, f"⚙️ {status}")
                        status_ph.markdown(
                            f'<div class="eta-box">'
                            f'<span class="pulse-dot"></span>'
                            f' {stage_msg} ({pct}%)'
                            f'</div>',
                            unsafe_allow_html=True,
                        )


# ══════════════════════════════════════════════════════════════════════
# TAB 2 — MEETINGS LIST
# ══════════════════════════════════════════════════════════════════════
with t_meetings:
    hcol, rcol = st.columns([6, 1])
    with hcol:
        st.markdown('<div class="section-lbl">All Processed Meetings</div>', unsafe_allow_html=True)
    with rcol:
        st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
        if st.button("↻ Refresh"):
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    meetings = (api_get("/meetings?limit=100") or {}).get("meetings", [])

    if not meetings:
        st.markdown("""
        <div style="text-align:center;padding:60px 0;color:#94A3B8">
          <div style="font-size:2.5rem;margin-bottom:12px">📭</div>
          <div style="font-weight:600;color:#475569;font-size:1rem">No meetings yet</div>
          <div style="font-size:.875rem;margin-top:4px">Upload a recording to get started</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        for m in meetings:
            status    = m.get("status","")
            badge     = (f'<span class="badge badge-ok">✓ Complete</span>'  if status=="completed"
                         else f'<span class="badge badge-proc">⚙ Processing</span>' if "process" in status or status=="queued"
                         else f'<span class="badge badge-fail">✗ Failed</span>')
            dur       = float(m.get("duration_secs") or 0)
            dur_str   = f"{int(dur//60)}m {int(dur%60)}s" if dur else "—"
            created   = (m.get("created_at","")[:16]).replace("T"," at ")
            sty       = (m.get("summary_style") or "executive").title()
            sent      = m.get("sentiment","neutral")
            sent_e    = {"positive":"🟢","neutral":"🟡","negative":"🔴"}.get(sent,"⚪")
            excerpt   = (m.get("overview") or "")[:160]
            if len(m.get("overview","")) > 160: excerpt += "…"

            st.markdown(f"""
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:flex-start">
                <div>
                  <div class="card-title">🎙 {m.get('filename','Unknown')}</div>
                  <div class="card-meta">
                    <span>📅 {created}</span><span>⏱ {dur_str}</span>
                    <span>📄 {sty}</span><span>{sent_e} {sent.title()}</span>
                    <span style="font-family:monospace;font-size:.72rem;color:#CBD5E1">{m.get('id','')}</span>
                  </div>
                </div>
                {badge}
              </div>
              {"<div class='card-excerpt'>" + excerpt + "</div>" if excerpt else ""}
            </div>
            """, unsafe_allow_html=True)

            vcol, _ = st.columns([1, 7])
            with vcol:
                if st.button("View →", key=f"v_{m['id']}"):
                    st.session_state["selected_meeting"] = m["id"]
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════
# TAB 3 — VIEW SUMMARY + CHAT
# ══════════════════════════════════════════════════════════════════════
with t_view:
    mid = st.session_state.get("selected_meeting") or st.session_state.get("last_job_id")

    if not mid:
        st.markdown("""
        <div style="text-align:center;padding:64px 0;color:#94A3B8">
          <div style="font-size:2.5rem;margin-bottom:12px">📄</div>
          <div style="font-weight:600;color:#475569;font-size:1rem">No meeting selected</div>
          <div style="font-size:.875rem;margin-top:4px">Click "View →" from the Meetings tab</div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    record = api_get(f"/meetings/{mid}")
    if not record:
        st.error(f"Meeting `{mid}` not found or still processing.")
        st.stop()

    summary  = record.get("summary", {})
    filename = record.get("filename","Unknown")
    created  = (record.get("created_at","")[:16]).replace("T"," at ")
    dur      = float(record.get("duration_secs") or 0)
    dur_str  = f"{int(dur//60)}m {int(dur%60)}s" if dur else "—"
    sty_lbl  = (record.get("summary_style") or "executive").title()
    sent     = summary.get("sentiment","neutral")

    # Meeting header
    st.markdown(f"""
    <div style="margin-bottom:20px">
      <div style="font-size:1.2rem;font-weight:700;color:#0F172A;letter-spacing:-.02em">
        🎙️ {filename}
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:14px;align-items:center;margin-top:7px">
        <span style="font-size:.78rem;color:#94A3B8">📅 {created}</span>
        <span style="font-size:.78rem;color:#94A3B8">⏱ {dur_str}</span>
        <span style="font-size:.78rem;color:#94A3B8">📄 {sty_lbl} Summary</span>
        <span class="sent-{sent}">{sent.title()} sentiment</span>
        <span style="font-size:.7rem;color:#D1D5DB;font-family:monospace">ID: {mid}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    s_summary, s_transcript, s_chat = st.tabs(["Summary", "Transcript", "💬 Chat"])

    # ── SUMMARY ─────────────────────────────────────────────────────────
    with s_summary:
        if not summary:
            st.warning("Summary not available yet — the meeting may still be processing.")
            st.stop()

        # Overview
        st.markdown(f"""
        <div class="sum-card">
          <div class="sum-card-title">📋 Meeting Overview</div>
          <div class="sum-overview">{summary.get('meeting_overview','N/A')}</div>
        </div>
        """, unsafe_allow_html=True)

        # 2-column: key points + decisions
        cl, cr = st.columns(2, gap="medium")

        def bullet_rows(items, dot_cls):
            html = ""
            for item in items:
                text = (f"<strong>{item.get('topic','')}</strong>: {item.get('details','')}"
                        if isinstance(item, dict) and 'topic' in item
                        else item.get('decision', str(item)) if isinstance(item, dict)
                        else str(item))
                html += f'<div class="bullet-row"><div class="dot {dot_cls}"></div><div>{text}</div></div>'
            return html or '<div style="font-size:.85rem;color:#94A3B8">None recorded</div>'

        with cl:
            st.markdown(f"""
            <div class="sum-card">
              <div class="sum-card-title">💬 Key Discussion Points</div>
              {bullet_rows(summary.get('key_discussion_points',[]), 'dot')}
            </div>
            """, unsafe_allow_html=True)

        with cr:
            dec_html = bullet_rows(summary.get('decisions_taken',[]), 'dot-g')
            st.markdown(f"""
            <div class="sum-card">
              <div class="sum-card-title">✅ Decisions Taken</div>
              {dec_html}
            </div>
            """, unsafe_allow_html=True)

        # Risks + Next Steps
        cl2, cr2 = st.columns(2, gap="medium")
        with cl2:
            risks = summary.get('risks_and_blockers',[])
            r_html = ""
            for r in risks:
                txt = r.get('item', str(r)) if isinstance(r, dict) else str(r)
                r_html += f'<div class="bullet-row"><div class="dot dot-r"></div><div>{txt}</div></div>'
            st.markdown(f"""
            <div class="sum-card">
              <div class="sum-card-title">⚠️ Risks &amp; Blockers</div>
              {r_html or '<div style="color:#15803D;font-size:.85rem">✓ No risks identified</div>'}
            </div>
            """, unsafe_allow_html=True)

        with cr2:
            ns_html = ""
            for ns in summary.get('next_steps',[]):
                txt = f"{ns.get('step','')} <em style='color:#94A3B8'>· {ns.get('responsible','TBD')}</em>" if isinstance(ns, dict) else str(ns)
                ns_html += f'<div class="bullet-row"><div class="dot dot-b"></div><div>{txt}</div></div>'
            st.markdown(f"""
            <div class="sum-card">
              <div class="sum-card-title">🔜 Next Steps</div>
              {ns_html or '<div style="font-size:.85rem;color:#94A3B8">None recorded</div>'}
            </div>
            """, unsafe_allow_html=True)

        # Action items table
        action_items = summary.get("action_items", [])
        if action_items:
            st.markdown('<div class="section-lbl" style="margin-top:6px">📋 Action Items</div>', unsafe_allow_html=True)
            import pandas as pd
            rows = [
                {
                    "Task":     ai.get("task","") if isinstance(ai,dict) else str(ai),
                    "Owner":    ai.get("owner","Unassigned") if isinstance(ai,dict) else "—",
                    "Deadline": ai.get("deadline","TBD") if isinstance(ai,dict) else "—",
                    "Priority": ai.get("priority","—") if isinstance(ai,dict) else "—",
                }
                for ai in action_items
            ]
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # ── TRANSCRIPT ──────────────────────────────────────────────────────
    with s_transcript:
        clean = record.get("clean_transcript","")
        raw   = record.get("raw_transcript","")

        if not clean and not raw:
            st.warning("Transcript not available.")
        else:
            mode_col, _ = st.columns([2, 5])
            with mode_col:
                mode = st.radio("View", ["Cleaned","Raw"], horizontal=True, label_visibility="collapsed")
            content = clean if mode == "Cleaned" else raw
            wc = len(content.split())
            st.markdown(f'<div style="font-size:.76rem;color:#94A3B8;margin-bottom:6px">{wc:,} words · {len(content):,} characters</div>', unsafe_allow_html=True)
            st.text_area("t", value=content, height=480, label_visibility="collapsed")
            st.download_button(f"⬇️ Download {mode.lower()} transcript",
                               data=content.encode(), mime="text/plain",
                               file_name=f"{Path(filename).stem}_{mode.lower()}_transcript.txt")

    # ── CHAT ────────────────────────────────────────────────────────────
    with s_chat:
        st.markdown("""
        <div class="sum-card" style="margin-bottom:16px">
          <div class="sum-card-title">💬 Ask anything about this meeting</div>
          <div style="font-size:.875rem;color:#475569;line-height:1.65">
            Ask questions like <em>"Who owns the API task?"</em>, <em>"What were the key risks?"</em>,
            <em>"Summarise the discussion about X"</em>, or <em>"Draft a follow-up email"</em>.
            Answers are generated from the meeting transcript.
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Session chat history
        history_key = f"chat_{mid}"
        if history_key not in st.session_state:
            st.session_state[history_key] = []

        # Render history
        for msg in st.session_state[history_key]:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Quick question chips
        CHIPS = [
            "What were the main decisions taken?",
            "List all action items with owners",
            "What risks were raised?",
            "Write a follow-up email",
        ]
        chip_cols = st.columns(len(CHIPS))
        for idx, chip in enumerate(CHIPS):
            with chip_cols[idx]:
                st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                if st.button(chip, key=f"chip_{mid}_{idx}"):
                    st.session_state[f"pending_q_{mid}"] = chip
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Chat input
        prompt = st.chat_input("Ask a question about this meeting…")
        # Also accept chip selection
        if not prompt and f"pending_q_{mid}" in st.session_state:
            prompt = st.session_state.pop(f"pending_q_{mid}")

        if prompt:
            # Show user message
            st.session_state[history_key].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Stream assistant response
            with st.chat_message("assistant"):
                response_text = st.write_stream(stream_chat(mid, prompt))

            st.session_state[history_key].append({"role": "assistant", "content": response_text})

        if st.session_state[history_key]:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            bcol, _ = st.columns([1, 6])
            with bcol:
                st.markdown('<div class="btn-ghost">', unsafe_allow_html=True)
                if st.button("🗑 Clear chat", key=f"clr_{mid}"):
                    st.session_state[history_key] = []
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# close .page div
st.markdown("</div>", unsafe_allow_html=True)

import streamlit as st
import requests
import base64
import tempfile
import os
import io
import wave
from datetime import datetime

try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_OK = True
except Exception as e:   # instead of ImportError
    AUDIO_OK = False

# TTS deps
try:
    from gtts import gTTS
    TTS_OK = True
except ImportError:
    TTS_OK = False

# PDF
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BACKEND_URL = "http://127.0.0.1:8000"

# ------------------ Page Config ------------------
st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ------------------ Custom CSS ------------------
st.markdown(
    """
<style>
/* General */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}

/* Header */
.app-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    padding: 16px 24px;
    color: white;
    box-shadow: 0 6px 18px rgba(102,126,234,0.35);
    margin-bottom: 16px;
}

/* Question */
.question-box {
    background: linear-gradient(135deg, #4c6fff 50%, #9f7aea 100%);
    padding: 20px;
    border-radius: 14px;
    color: #fff;
    font-size: 1.1rem;
    line-height: 1.6;
    box-shadow: 0 4px 14px rgba(76,111,255,0.3);
    margin-bottom: 10px;
}

/* Score cards */
.score-card {
    background: #ffffff;
    padding: 14px 16px;
    border-radius: 10px;
    box-shadow: 0 2px 10px rgba(15,23,42,0.1);
}

/* Strengths & improvements */
.strength-item {
    background: #8DB600;
    padding: 8px 10px;
    border-radius: 6px;
    margin-bottom: 6px;
    border-left: 3px solid #22c55e;
}
.improve-item {
    background: #F88379;
    padding: 8px 10px;
    border-radius: 6px;
    margin-bottom: 6px;
    border-left: 3px solid #f97316;
}

/* Final score */
.final-score-box {
    background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
    padding: 26px;
    border-radius: 18px;
    color: white;
    text-align: center;
    box-shadow: 0 8px 24px rgba(34,197,94,0.4);
    margin-bottom: 18px;
}
.final-score-number {
    font-size: 3.5rem;
    font-weight: 800;
    margin-bottom: 4px;
}

/* Progress badge */
.progress-badge {
    background: #800080;
    border-radius: 999px;
    padding: 6px 12px;
    display: inline-block;
    font-size: 0.85rem;
    margin-bottom: 6px;
}

/* Sidebar question status */
.sidebar-q {
    background: #DDA0DD;
    padding: 6px 9px;
    border-radius: 8px;
    margin-bottom: 4px;
    font-size: 0.9rem;
}
.sidebar-q.current {
    background: #0054b4;
    border-left: 3px solid #0ea5e9;
    font-weight: 600;
}
.sidebar-q.done {
    background: #4b0082;
    border-left: 3px solid #22c55e;
}

/* Recording indicator */
.recording-indicator {
    background: #ef4444;
    color: white;
    padding: 8px 12px;
    border-radius: 999px;
    display: inline-block;
    font-size: 0.85rem;
    animation: pulse 1.4s infinite;
}
@keyframes pulse {
    0% { transform: scale(1); opacity: 1; }
    50% { transform: scale(1.04); opacity: 0.75; }
    100% { transform: scale(1); opacity: 1; }
}
</style>
""",
    unsafe_allow_html=True,
)

# ------------------ Helper Functions ------------------
def safe_get(path: str):
    try:
        r = requests.get(f"{BACKEND_URL}{path}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"GET {path} failed: {e}")
        return None


def safe_post(path: str, data=None, json_data=None):
    try:
        if json_data is not None:
            r = requests.post(f"{BACKEND_URL}{path}", json=json_data, timeout=60)
        else:
            r = requests.post(f"{BACKEND_URL}{path}", data=data, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"POST {path} failed: {e}")
        return None


def tts_generate(text: str):
    """Generate TTS bytes for given text using gTTS."""
    if not TTS_OK or not text or not text.strip():
        return None
    try:
        tts = gTTS(text=text, lang="en")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
            tmp_path = f.name
        tts.save(tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        os.remove(tmp_path)
        return audio_bytes
    except Exception as e:
        st.warning(f"TTS error: {e}")
        return None


def autoplay_audio(audio_bytes: bytes):
    """Embed & auto-play audio."""
    if not audio_bytes:
        return
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    audio_html = f"""
    <audio autoplay="true">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
    </audio>
    """
    st.markdown(audio_html, unsafe_allow_html=True)


def start_recording():
    """Start continuous recording to temp WAV file."""
    if not AUDIO_OK:
        st.error("Audio recording not available. Install: pip install sounddevice soundfile numpy")
        return

    if st.session_state.is_recording:
        st.warning("Already recording.")
        return

    try:
        samplerate = 44100
        channels = 1
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_path = tmp.name
        tmp.close()

        sf_obj = sf.SoundFile(
            tmp_path,
            mode="w",
            samplerate=samplerate,
            channels=channels,
            subtype="PCM_16",
        )

        def callback(indata, frames, time, status):
            if status:
                print("Recording status:", status)
            sf_obj.write(indata.copy())

        stream = sd.InputStream(
            samplerate=samplerate,
            channels=channels,
            callback=callback,
        )
        stream.start()

        st.session_state.is_recording = True
        st.session_state.record_stream = stream
        st.session_state.soundfile_obj = sf_obj
        st.session_state.audio_tempfile = tmp_path

    except Exception as e:
        st.error(f"Could not start recording: {e}")
        # Cleanup if partially created
        if "soundfile_obj" in st.session_state and st.session_state.soundfile_obj:
            try:
                st.session_state.soundfile_obj.close()
            except:
                pass
        if "audio_tempfile" in st.session_state and st.session_state.audio_tempfile:
            try:
                os.remove(st.session_state.audio_tempfile)
            except:
                pass
        st.session_state.is_recording = False
        st.session_state.record_stream = None
        st.session_state.soundfile_obj = None
        st.session_state.audio_tempfile = None


def stop_recording_and_transcribe():
    """Stop recording and transcribe using your Faster-Whisper backend."""
    if not st.session_state.get("is_recording", False):
        st.warning("No active recording.")
        return

    try:
        # Stop recording
        if st.session_state.record_stream:
            st.session_state.record_stream.stop()
            st.session_state.record_stream.close()
        if st.session_state.soundfile_obj:
            st.session_state.soundfile_obj.close()

        audio_path = st.session_state.audio_tempfile

        # Reset state
        st.session_state.is_recording = False
        st.session_state.record_stream = None
        st.session_state.soundfile_obj = None
        st.session_state.audio_tempfile = None

        if not audio_path or not os.path.exists(audio_path):
            st.error("Audio file not found.")
            return

        # Read the recorded audio
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()   # ← THIS WAS MISSING

        # Delete temp file
        try:
            os.remove(audio_path)
        except:
            pass

        # Send to your backend
        audio_b64 = base64.b64encode(audio_bytes).decode()
        payload = {"audio_data": audio_b64}

        with st.spinner("Transcribing your answer..."):
            response = requests.post(f"{BACKEND_URL}/speech-to-text", json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()

        # Optional debug
        st.write("Transcription result:", result)

        if result.get("success"):
            transcript = result.get("text", "").strip()
            if transcript:
                # Append to the answer (this works with value= in text_area)
                st.session_state.answer = (st.session_state.answer + " " + transcript).strip()
                st.success("Transcript added to your answer!")
                st.rerun()
            else:
                st.warning("Transcription was empty.")
        else:
            st.error(result.get("error", "Transcription failed"))

    except Exception as e:
        st.error(f"Error during transcription: {e}")
        st.session_state.is_recording = False
        
def create_pdf(final_result, questions, responses, category):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    y = h - 50

    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, y, "AI Interview Report")
    y -= 30
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Category: {category.title()}")
    y -= 16
    c.drawString(50, y, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    y -= 26

    score = final_result.get("overall_score", 0.0)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Final Score: {score}/10")
    y -= 24

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Summary Feedback:")
    y -= 18
    c.setFont("Helvetica", 10)
    feedback = final_result.get("detailed_feedback", "")
    for line in feedback.split(". "):
        if y < 80:
            c.showPage()
            y = h - 50
        c.drawString(50, y, line[:90])
        y -= 14

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Questions & Answers:")
    y -= 20
    c.setFont("Helvetica", 10)

    for i, q in enumerate(questions):
        if y < 100:
            c.showPage()
            y = h - 50
        c.drawString(50, y, f"Q{i+1}: {q[:85]}")
        y -= 14
        ans = responses[i] if i < len(responses) else "(no answer)"
        c.drawString(60, y, f"A: {ans[:85]}")
        y -= 18

    c.save()
    buf.seek(0)
    return buf


def score_color(score: float) -> str:
    if score >= 8:
        return "#22c55e"
    if score >= 6:
        return "#0ea5e9"
    if score >= 4:
        return "#f97316"
    return "#ef4444"


# ------------------ Session State ------------------
def init_state():
    defaults = {
        "interview_id": None,
        "category": None,
        "question": None,
        "q_index": 0,
        "total_q": 0,
        "questions": [],
        "responses": [],
        "scores": [],
        "answer": "",
        "final_result": None,
        "last_tts_question": None,
        # recording
        "is_recording": False,
        "record_stream": None,
        "soundfile_obj": None,
        "audio_tempfile": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    init_state()


init_state()

# ------------------ Sidebar ------------------
with st.sidebar:
    st.markdown("## 🎯 AI Interview Coach")
    st.markdown("---")
    health = safe_get("/health")
    if health:
        st.success("Backend: Online")
        st.caption(f"Speech: {'ON' if health.get('speech_enabled') else 'OFF'}")
    else:
        st.error("Backend: Offline")
        st.code("python main.py", language="bash")
        st.stop()

    st.markdown("---")
    categories = safe_get("/categories") or []
    cat_map = {c["id"]: c["name"] for c in categories}

    if not st.session_state.interview_id:
        sel_cat = st.selectbox(
            "Category",
            list(cat_map.keys()) if cat_map else ["technical", "behavioral", "management", "sales"],
            format_func=lambda x: cat_map.get(x, x.title()),
        )
        if st.button("🚀 Start Interview", type="primary", use_container_width=True):
            resp = safe_post(
                "/start-interview",
                data={"category": sel_cat, "user_id": "user"},
            )
            if resp:
                st.session_state.interview_id = resp["interview_id"]
                st.session_state.category = resp["category"]
                st.session_state.question = resp["question"]
                st.session_state.q_index = resp["question_index"]
                st.session_state.total_q = resp["total_questions"]
                st.session_state.responses = []
                st.session_state.scores = []
                st.session_state.answer = ""
                st.session_state.final_result = None
                st.session_state.last_tts_question = None

                dbg = safe_get(f"/debug-interview/{resp['interview_id']}")
                if dbg and dbg.get("questions"):
                    st.session_state.questions = dbg["questions"]
                else:
                    st.session_state.questions = [resp["question"]]

                st.rerun()
    else:
        st.markdown(f"**Category:** {st.session_state.category.title()}")
        st.markdown("---")

        st.markdown("### Progress")
        for i in range(st.session_state.total_q):
            qnum = i + 1
            if i < len(st.session_state.responses):
                sc = st.session_state.scores[i].get("overall_score", 0) if i < len(st.session_state.scores) else 0
                st.markdown(
                    f"<div class='sidebar-q done'>✅ Q{qnum} – {sc:.1f}/10</div>",
                    unsafe_allow_html=True,
                )
            elif i == st.session_state.q_index:
                st.markdown(
                    f"<div class='sidebar-q current'>➡️ Q{qnum} (current)</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f"<div class='sidebar-q'>⏳ Q{qnum}</div>",
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        if st.button("🔄 Reset Interview", use_container_width=True):
            reset_all()
            st.rerun()

# ------------------ Header ------------------
st.markdown(
    f"""
<div class="app-header">
  <h2 style="margin:0;">AI Interview Coach</h2>
  <p style="margin:4px 0 0 0; font-size:0.95rem; opacity:0.9;">
    Practice structured interviews with instant, AI-powered feedback.
  </p>
</div>
""",
    unsafe_allow_html=True,
)

# ------------------ Final Result Page (separate) ------------------
if st.session_state.final_result:
    final = st.session_state.final_result
    score = final.get("overall_score", 0.0)
    color = score_color(score)

    st.markdown(
        f"""
<div class="final-score-box">
  <div>🎉 Interview Complete!</div>
  <div class="final-score-number">{score:.1f}/10</div>
  <div style="font-size:1.05rem;">Overall Performance</div>
</div>
""",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📊 Score Breakdown")
        breakdown = final.get("category_breakdown", {})
        if breakdown:
            for k, v in breakdown.items():
                st.markdown(
                    f"**{k.title()}:** <span style='color:{score_color(v)}; font-weight:600;'>{v}/10</span>",
                    unsafe_allow_html=True,
                )
                st.progress(min(max(v / 10.0, 0.0), 1.0))
        else:
            st.write("No breakdown available.")

        st.markdown("---")
        st.subheader("💪 Strengths")
        strengths = final.get("strength_analysis", [])
        if strengths:
            for s in strengths:
                st.markdown(f"<div class='strength-item'>✅ {s}</div>", unsafe_allow_html=True)
        else:
            st.caption("No specific strengths identified.")

    with col2:
        st.subheader("📝 Summary Feedback")
        st.write(final.get("detailed_feedback", ""))

        st.markdown("---")
        st.subheader("📈 Areas to Improve")
        improvements = final.get("areas_for_improvement", [])
        if improvements:
            for imp in improvements:
                st.markdown(f"<div class='improve-item'>💡 {imp}</div>", unsafe_allow_html=True)
        else:
            st.caption("No specific improvement areas identified.")

    st.markdown("---")
    c_pdf, c_new = st.columns(2)
    with c_pdf:
        pdf_bytes = create_pdf(
            final,
            st.session_state.questions,
            st.session_state.responses,
            st.session_state.category or "interview",
        )
        st.download_button(
            "📄 Download PDF Report",
            data=pdf_bytes,
            file_name=f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )
    with c_new:
        if st.button("🔄 Start New Interview", use_container_width=True):
            reset_all()
            st.rerun()

    st.stop()  # Do NOT show questions below result page

# ------------------ If no interview yet ------------------
if not st.session_state.interview_id:
    st.info("Choose a category in the sidebar and click **Start Interview** to begin.")
    st.stop()

# ------------------ Active Interview Page ------------------
# Progress
progress_ratio = st.session_state.q_index / max(st.session_state.total_q, 1)
st.markdown(
    f"<div class='progress-badge'>Question {st.session_state.q_index + 1} of {st.session_state.total_q}</div>",
    unsafe_allow_html=True,
)
st.progress(progress_ratio)

st.markdown("---")

# Question box
st.markdown(
    f"<div class='question-box'>{st.session_state.question}</div>",
    unsafe_allow_html=True,
)

# Auto TTS: read aloud ONCE per new question
if TTS_OK and st.session_state.question != st.session_state.last_tts_question:
    audio = tts_generate(st.session_state.question)
    if audio:
        autoplay_audio(audio)
    st.session_state.last_tts_question = st.session_state.question



if "answer" not in st.session_state:
    st.session_state.answer = ""

st.text_area(
    "Type here (or use voice recording below):",
    value=st.session_state.answer,    # ← this is what shows the text
    on_change=lambda: None,           # optional
    height=170,
    placeholder="Your answer will appear here..."
)


# Now you can safely use the value like this:
word_count = len(st.session_state.answer.split()) if st.session_state.answer.strip() else 0
col_wc1, col_wc2 = st.columns([1, 3])
with col_wc1:
    st.write(f"📝 **{word_count} words**")
with col_wc2:
    if word_count < 20:
        st.warning("Try to add more detail (aim for at least 50 words).")
    elif word_count < 50:
        st.info("Good start — you can add more specifics.")
    else:
        st.success("Nice length — now focus on clarity & relevance.")

st.markdown("---")

# Voice Recording (Start / Stop + Transcribe)
st.subheader("🎤 Voice Recording")

if AUDIO_OK:
    col_r1, col_r2, col_r3 = st.columns([1, 1, 2])

    with col_r1:
        # Do not allow recording while user is typing
        disable_start = st.session_state.is_recording or bool(st.session_state.answer.strip())
        if st.button("🎙️ Start Recording", disabled=disable_start, use_container_width=True):
            if st.session_state.answer.strip():
                st.warning("Finish or clear your typed answer before recording.")
            else:
                start_recording()
                st.rerun()

    with col_r2:
        if st.button("⏹️ Stop & Transcribe", disabled=not st.session_state.is_recording, use_container_width=True):
            stop_recording_and_transcribe()
            st.rerun()

    with col_r3:
        if st.session_state.is_recording:
            st.markdown("<span class='recording-indicator'>🔴 Recording in progress...</span>", unsafe_allow_html=True)
        else:
            st.caption("Use recording to dictate your answer, then edit the text above if needed.")
else:
    st.warning("Voice recording not available. Install: `pip install sounddevice soundfile numpy`,🎤 Voice recording is only available when running locally.")

st.markdown("---")

# Submit / Skip
col_submit, col_skip = st.columns([2, 1])

with col_submit:
    if st.button("✅ Submit Answer", type="primary", use_container_width=True):
        text = st.session_state.answer.strip()
        if len(text) < 5:
            st.warning("Please provide a more complete answer before submitting.")
        else:
            data = {
                "interview_id": st.session_state.interview_id,
                "response_text": text,
            }
            with st.spinner("Analyzing your answer..."):
                res = safe_post("/submit-response", data=data)
            if res:
                st.session_state.responses.append(text)
                if res.get("current_response_analysis"):
                    st.session_state.scores.append(res["current_response_analysis"])

                if res.get("interview_complete"):
                    st.session_state.final_result = {
                        "overall_score": res.get("final_score"),
                        "detailed_feedback": res.get("detailed_feedback", ""),
                        "areas_for_improvement": res.get("areas_for_improvement", []),
                        "strength_analysis": res.get("strength_analysis", []),
                        "category_breakdown": res.get("category_breakdown", {}),
                    }
                else:
                    # Move to next question & clear UI
                    st.session_state.q_index = res["question_index"]
                    st.session_state.question = res["next_question"]
                    st.session_state.answer = ""          # clear textbox
                    st.session_state.last_tts_question = None
                    # reset recording state
                    st.session_state.is_recording = False
                    st.session_state.record_stream = None
                    st.session_state.soundfile_obj = None
                    st.session_state.audio_tempfile = None

                st.rerun()

with col_skip:
    if st.button("⏭️ Skip Question", use_container_width=True):
        data = {
            "interview_id": st.session_state.interview_id,
            "response_text": "(Skipped)",
        }
        res = safe_post("/submit-response", data=data)
        if res:
            st.session_state.responses.append("(Skipped)")
            if res.get("current_response_analysis"):
                st.session_state.scores.append(res["current_response_analysis"])

            if res.get("interview_complete"):
                st.session_state.final_result = {
                    "overall_score": res.get("final_score"),
                    "detailed_feedback": res.get("detailed_feedback", ""),
                    "areas_for_improvement": res.get("areas_for_improvement", []),
                    "strength_analysis": res.get("strength_analysis", []),
                    "category_breakdown": res.get("category_breakdown", {}),
                }
            else:
                st.session_state.q_index = res["question_index"]
                st.session_state.question = res["next_question"]
                st.session_state.answer = ""      # clear
                st.session_state.last_tts_question = None
                # reset recording state
                st.session_state.is_recording = False
                st.session_state.record_stream = None
                st.session_state.soundfile_obj = None
                st.session_state.audio_tempfile = None

            st.rerun()

# Last answer feedback
if st.session_state.scores:
    st.markdown("---")
    st.subheader("📊 Last Answer Feedback")
    last = st.session_state.scores[-1]

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("Overall", f"{last.get('overall_score', 0):.1f}/10")
    col_s2.metric("Relevance", f"{last.get('relevance_score', 0):.1f}/10")
    col_s3.metric("Completeness", f"{last.get('completeness_score', 0):.1f}/10")
    col_s4.metric("Clarity", f"{last.get('clarity_score', 0):.1f}/10")

    # Show your agent's detailed feedback (useful for garbage answers)
    if "feedback" in last:
        st.info(last["feedback"])

    c_ls, c_li = st.columns(2)
    with c_ls:
        st.markdown("**💪 Strengths**")
        for s in last.get("strengths", []):
            st.markdown(f"<div class='strength-item'>✅ {s}</div>", unsafe_allow_html=True)
    with c_li:
        st.markdown("**📈 Areas to Improve**")
        for imp in last.get("improvement_areas", []):
            st.markdown(f"<div class='improve-item'>💡 {imp}</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("AI Interview Coach · FastAPI + Streamlit · STT via faster-whisper, TTS via gTTS")

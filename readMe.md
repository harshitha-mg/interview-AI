# AI Interview Coach

An AI-powered interview practice agent that conducts structured interviews, analyzes your answers, and provides detailed scoring and feedback across multiple categories (Technical, Behavioral, Management, Sales & Marketing).

---

## Overview

This project is a full-stack AI interview practice system:

- **Frontend**: A modern web UI (Streamlit) where users:
  - Choose an interview category
  - Answer 8 questions per session (typed or via speech)
  - See real-time progress and detailed feedback

- **Backend**: A FastAPI service that:
  - Generates questions per category
  - Analyzes each response using NLP (semantic similarity, readability, specificity, sentiment)
  - Computes per-question and final interview scores
  - Returns detailed strengths and improvement suggestions

The scoring logic is intentionally **supportive and lenient** for reasonable answers while still penalizing obviously poor or non-answers (e.g., “I don’t know”).

---

## Features

### Core Features

- **Multiple Interview Categories**
  - Technical
  - Behavioral
  - Management
  - Sales & Marketing

- **8-Question Sessions**
  - Each interview consists of 8 questions
  - Questions are randomly sampled from a larger question bank per category (≈20+)
  - Keeps practice sessions varied and fresh

- **Voice & Text Input**
  - Type your answer in a rich textarea
  - Or use browser speech recognition to transcribe your voice directly into text

- **Per-Question AI Analysis**
  For each answer, the backend computes:
  - **Relevance**: Are you using concepts and terms that match the category?
  - **Completeness**: Are you providing specific details and examples?
  - **Clarity**: Is your explanation easy to read and understand?
  - **Accuracy (Technical Accuracy)**: How semantically similar is your answer to the question prompt?
  - **Overall Score (0–10)** combining all the above

- **Interview-Level Feedback**
  - Overall score (0–10)
  - Category breakdown:
    - Relevance
    - Completeness
    - Clarity
    - Technical Accuracy
  - Aggregated strengths
  - Aggregated areas for improvement
  - Natural-language summary feedback

- **Supportive Scoring**
  - Reasonable answers (20–60 words, somewhat relevant) usually land in the **6–8+** range
  - Excellent answers with strong relevance and detail can reach **8.5–10**
  - Very short or non-answers remain in the **1–4** range

---

## Limitations

- **Heuristic Scoring (No LLM in the loop)**
  - Scoring is based on:
    - SentenceTransformer embeddings
    - Keyword presence
    - Simple readability metrics
    - Basic sentiment analysis (NLTK VADER)
  - It does not “understand” content as deeply as a large language model would.

- **Speech Recognition Quality Depends on Browser**
  - The current setup uses the browser’s Web Speech API (Chrome/Edge) for transcription.
  - Accuracy depends heavily on:
    - Microphone quality
    - Noise environment
    - Browser support
  - If backend Whisper or another STT solution is integrated, quality can improve but requires more resources.

- **In-Memory Sessions**
  - `active_interviews` are stored in memory.
  - If the backend restarts, in-progress sessions are lost.
  - Only completed interviews are persisted (if database/local JSON is enabled).

- **Single-User Oriented**
  - The default user_id is `"default_user"`.
  - Multi-user scenarios require wiring proper auth/user IDs on the frontend.

- **No Security / Auth**
  - All endpoints are open (CORS `allow_origins=["*"]`).
  - Intended for local development and demo use.

---

## Tech Stack & APIs Used

### Backend

- **Language**
  - Python 3.x

- **Framework**
  - [FastAPI](https://fastapi.tiangolo.com/) for HTTP API

- **Core AI / NLP**
  - [SentenceTransformers](https://www.sbert.net/)
    - Model: `all-MiniLM-L6-v2`
    - Used for semantic similarity (question vs. answer)
  - [NLTK](https://www.nltk.org/)
    - VADER sentiment analyzer for tone analysis
  - Custom heuristics in `interview_agent_free.py`:
    - Keyword-based relevance
    - Readability (sentence/word length)
    - Specificity (presence of example markers, unique words)
    - Response quality classification (non-answer, very_short, short, adequate, good, excellent)

- **Speech Processing (Optional Backend STT)**
  - `speech_recognition` + audio conversion
  - Or Whisper/faster-whisper if configured (depends on your `speech_processor.py` implementation)

- **Persistence**
  - `FirebaseManager` (if configured), or
  - Local JSON file (`interview_data.json`) as a simple storage layer

**Frontend (Streamlit UI)**
- Built entirely with **Streamlit** (`streamlit_app.py`)
- Modern, card-based layout with:
  - **Category selection screen**
    - Sidebar selectbox for interview category
    - “Start Interview” button
  - **Interview Q&A screen**
    - Question displayed in a styled “card”
    - Progress badge and `st.progress` bar
    - `st.text_area` for user answers
    - Optional voice recording controls (local dev)
    - Per-question feedback section showing:
      - Overall score
      - Relevance, completeness, clarity, etc.
      - Strengths and areas for improvement
  - **Results screen (separate page)**
    - Only shown after all questions are answered
    - Final overall score with color-coded display
    - Breakdown cards for relevance/completeness/clarity/technical
    - Bullet lists for strengths and improvement areas
    - “Download PDF Report” button
    - “Start New Interview” button

**Frontend → Backend Communication (Python requests, not JS)**
- Uses Python `requests` inside Streamlit (no JavaScript `fetch`):
  - `GET /health`  
    - To show “Backend: Online / Offline” in the sidebar
  - `GET /categories`  
    - To populate the category dropdown
  - `POST /start-interview` (form data: `category`, `user_id`)  
    - To create a new interview session and fetch the first question
  - `POST /submit-response` (form data: `interview_id`, `response_text`)  
    - To analyze the current answer and either:
      - Return next question + per-answer analysis, or
      - Return final scores + feedback when interview is complete
  - `POST /speech-to-text` (JSON: `audio_data` as base64 WAV)  
    - To send recorded audio to the FastAPI backend
    - Backend uses `SpeechProcessor` (Faster-Whisper) to transcribe speech to text

---

## Setup & Run Instructions

1. Clone / Create Project

```bash
# Inside your workspace
mkdir interview-agent
cd interview-agent

# Place your files:
# - main.py
# - interview_agent_free.py
# - database.py
# - speech_processor.py
# - streamlit_app.py
# - requirements.txt

2. Create and Activate Virtual Environment

# Create venv
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

3. Install Dependencies

pip install -r requirements.txt

4. Download NLTK Data (First Run)
    
    If not handled in code:
    # In interview_agent_free.py
        nltk.download('vader_lexicon', quiet=True)
        nltk.download('punkt', quiet=True)

These lines are already present; on first run, they will download required data.        

5. Run the Backend

    python main.py

    You should see:
        Uvicorn running on http://0.0.0.0:8000

6. Serve the Frontend
    In another terminal (still in the project directory):
        
        streamlit run streamlit_app.py 

    Now open in browser:
       (http://localhost:8501)

7. Using the App

    Open (http://localhost:8501)
    Choose a category (e.g., “Technical Interview”)
    Answer each of the 8 questions:
    Type your answer, or
    Click “Start Recording” to use voice → text
    Click “Submit Answer” for each question
    After Q8, you’ll be taken to the Results screen with:
    Overall score
    Category breakdown
    Strengths
    Areas for improvement
        
Potential Improvements

1. Smarter Scoring & Feedback
    Replace heuristics with a small, locally served LLM (e.g., via an API or local inference) to:
    Better understand content and nuance
    Provide more realistic interview-style feedback
    Learn a user’s level over time and adapt scoring:
    Junior vs Senior expectations
    Track performance trends by category

2. Better Speech Recognition
    Integrate a dedicated STT engine (e.g., Whisper, Vosk, or a cloud STT):
    More robust transcription
    Noise handling
    Punctuation and formatting
    Add microphone input level indicators and “replay audio” option.

3. Persistence & User Accounts
    Add authentication and per-user dashboards:
    See past interview sessions
    Track improvement over time
    Export reports (PDF/CSV)
    Migrate from local JSON to a robust DB:
    PostgreSQL / MySQL / Firestore / Supabase

4. Richer Frontend Experience
    Add:
    Timer per question (for timeboxing)
    Difficulty selector (easy/medium/hard)
    Question review screen before final submission
    Mobile-optimized layout with:
    Larger tap targets
    Better handling of the on-screen keyboard

5. Configurable Scoring Profiles
    Allow customization of scoring strictness:
    “Practice Mode” – more lenient, encouraging
    “Realistic Mode” – stricter, closer to real interviews
    Toggle weights:
    Emphasize clarity vs technical accuracy vs completeness
    
6. Multi-Language Support
    Extend:
    Question sets in other languages
    Multilingual SentenceTransformer models
    Multilingual STT/TTS (speech-to-text / text-to-speech)

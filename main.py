# main.py
from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from datetime import datetime
import base64
import os
import uvicorn
from interview_agent_free import FreeInterviewAgent   # <- YOUR agent
from speech_processor import SpeechProcessor          # <- YOUR speech processor

app = FastAPI(title="AI Interview Agent API", version="1.0.0")

# CORS so Streamlit can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; lock down in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
interview_agent = FreeInterviewAgent()
speech_processor = SpeechProcessor()

# In‑memory interview sessions
active_interviews: Dict[str, Dict] = {}


@app.get("/")
async def root():
    return {"message": "AI Interview Agent API", "status": "running"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "speech_enabled": speech_processor.model is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/categories")
async def get_categories():
    """Return available categories (IDs must match your question_templates keys)."""
    return [
        {"id": "technical", "name": "Technical Interview"},
        {"id": "behavioral", "name": "Behavioral Interview"},
        {"id": "management", "name": "Management Interview"},
        {"id": "sales", "name": "Sales & Marketing"},
    ]


@app.post("/start-interview")
async def start_interview(
    category: str = Form(...),
    user_id: str = Form("default_user"),
):
    """Start a new 8-question interview."""
    try:
        # Validate category against your agent
        valid_categories = list(interview_agent.question_templates.keys())
        if category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category '{category}'. Must be one of {valid_categories}",
            )

        interview_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        questions = interview_agent.generate_questions(category, 8)

        if not questions:
            raise HTTPException(status_code=500, detail="Could not generate questions")

        session = {
            "interview_id": interview_id,
            "user_id": user_id,
            "category": category,
            "questions": questions,
            "current_question": 0,
            "responses": [],
            "scores": [],
            "status": "active",
            "start_time": datetime.now().isoformat(),
            "final_result": None,
        }

        active_interviews[interview_id] = session

        return {
            "interview_id": interview_id,
            "question": questions[0],
            "question_index": 0,
            "total_questions": len(questions),
            "category": category,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /start-interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit-response")
async def submit_response(
    interview_id: str = Form(...),
    response_text: str = Form(...)
):
    """Use YOUR FreeInterviewAgent.analyze_response, and YOUR final_score logic."""
    try:
        if interview_id not in active_interviews:
            raise HTTPException(status_code=404, detail="Interview not found")

        session = active_interviews[interview_id]

        if session["status"] == "completed":
            raise HTTPException(status_code=400, detail="Interview already completed")

        current_idx = session["current_question"]
        total = len(session["questions"])

        if current_idx >= total:
            raise HTTPException(status_code=400, detail="All questions answered")

        current_question = session["questions"][current_idx]

        # Store response
        session["responses"].append(response_text)

        # ANALYZE with your agent
        analysis = interview_agent.analyze_response(
            current_question, response_text, session["category"]
        )
        session["scores"].append(analysis)

        # Move to next
        session["current_question"] += 1
        next_idx = session["current_question"]

        print(f"Q{current_idx + 1}/{total} answered. Score: {analysis.get('overall_score')}")

        # If finished
        if next_idx >= total:
            session["status"] = "completed"
            final_result = interview_agent.calculate_final_score(session["scores"])
            session["final_result"] = final_result

            return {
                "interview_complete": True,
                "final_score": final_result.get("overall_score", 0),
                "detailed_feedback": final_result.get("detailed_feedback", ""),
                "areas_for_improvement": final_result.get("areas_for_improvement", []),
                "strength_analysis": final_result.get("strength_analysis", []),
                "category_breakdown": final_result.get("category_breakdown", {}),
                "current_response_analysis": analysis,
            }

        # Otherwise return next question
        return {
            "interview_complete": False,
            "next_question": session["questions"][next_idx],
            "question_index": next_idx,
            "total_questions": total,
            "current_response_analysis": analysis,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in /submit-response: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/speech-to-text")
async def speech_to_text(request: dict):
    """
    Convert user speech (sent as base64 audio) to text
    using your Faster-Whisper SpeechProcessor.
    """
    try:
        audio_b64 = request.get("audio_data")
        if not audio_b64:
            return {
                "success": False,
                "text": "",
                "error": "No audio data provided"
            }

        # Ensure model is loaded
        if speech_processor.model is None:
            return {
                "success": False,
                "text": "",
                "error": "Speech model not loaded on server"
            }

        # Decode base64 -> raw audio bytes (WAV, as recorded in Streamlit)
        try:
            audio_bytes = base64.b64decode(audio_b64)
        except Exception as e:
            return {
                "success": False,
                "text": "",
                "error": f"Invalid audio format: {e}"
            }

        # Use YOUR Faster-Whisper processor
        transcribed_text = await speech_processor.speech_to_text(audio_bytes)

        if transcribed_text and len(transcribed_text.strip()) > 0:
            return {
                "success": True,
                "text": transcribed_text.strip(),
                "error": None
            }
        else:
            return {
                "success": False,
                "text": "",
                "error": "Could not transcribe audio. Please speak clearly and try again."
            }

    except Exception as e:
        print(f"/speech-to-text error: {e}")
        return {
            "success": False,
            "text": "",
            "error": str(e)
        }

@app.get("/debug-interview/{interview_id}")
async def debug_interview(interview_id: str):
    """Debug endpoint used by Streamlit to fetch all questions."""
    if interview_id not in active_interviews:
        return {"error": "Interview not found"}
    s = active_interviews[interview_id]
    return {
        "interview_id": interview_id,
        "category": s["category"],
        "current_question": s["current_question"],
        "questions": s["questions"],
        "responses": s["responses"],
        "scores": s["scores"],
        "status": s["status"],
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting API on port {port}")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
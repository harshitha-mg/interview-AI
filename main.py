from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from datetime import datetime
import base64
import os
import uvicorn
from interview_agent_free import FreeInterviewAgent

app = FastAPI(title="AI Interview Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lightweight agent only
interview_agent = FreeInterviewAgent()

# Disable speech on Render free tier
speech_processor = None
print("⚠️ SpeechProcessor disabled on Render free tier (512 MB limit)")

active_interviews: Dict[str, Dict] = {}

@app.get("/")
async def root():
    return {"message": "AI Interview Agent API", "status": "running"}

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "speech_enabled": False,
        "timestamp": datetime.now().isoformat(),
    }

@app.get("/categories")
async def get_categories():
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
    valid_categories = list(interview_agent.question_templates.keys())
    if category not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Invalid category")

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

@app.post("/submit-response")
async def submit_response(
    interview_id: str = Form(...),
    response_text: str = Form(...)
):
    if interview_id not in active_interviews:
        raise HTTPException(status_code=404, detail="Interview not found")

    session = active_interviews[interview_id]
    current_idx = session["current_question"]
    total = len(session["questions"])

    current_question = session["questions"][current_idx]
    session["responses"].append(response_text)

    analysis = interview_agent.analyze_response(
        current_question, response_text, session["category"]
    )
    session["scores"].append(analysis)
    session["current_question"] += 1

    if session["current_question"] >= total:
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

    return {
        "interview_complete": False,
        "next_question": session["questions"][session["current_question"]],
        "question_index": session["current_question"],
        "total_questions": total,
        "current_response_analysis": analysis,
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

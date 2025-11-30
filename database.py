# database.py (Same as before, but we'll add a free alternative)
import json
import os
from typing import Dict, Any
from datetime import datetime

class FirebaseManager:
    def __init__(self):
        # For free version, we can use local JSON file storage
        self.data_file = "interview_data.json"
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize local JSON storage"""
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w') as f:
                json.dump({"interview_sessions": []}, f)
    
    async def save_interview_session(self, session_data: Dict[str, Any]):
        """Save interview session to local JSON file"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            # Add new session
            data["interview_sessions"].append(session_data)
            
            # Save back to file
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            print(f"Interview session {session_data['interview_id']} saved locally")
            
        except Exception as e:
            print(f"Error saving to local storage: {e}")
    
    async def get_user_interviews(self, user_id: str) -> list:
        """Get all interviews for a user from local storage"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            
            user_interviews = [
                session for session in data.get("interview_sessions", [])
                if session.get("user_id") == user_id
            ]
            
            return user_interviews
            
        except Exception as e:
            print(f"Error reading from local storage: {e}")
            return []
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from dotenv import load_dotenv
import os
import csv
from datetime import datetime

load_dotenv()
gemini_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_key)

app = FastAPI(title="AI Chat Agent Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# NEW: The Manager's dictionary to keep track of all active tables
active_sessions = {}

class ChatRequest(BaseModel):
    message: str
    session_id: str # NEW: The Waiter must provide a Table Number

# Update the Logbook to include the Session ID column
log_file = "chat_logs.csv"
if not os.path.exists(log_file):
    with open(log_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Session ID", "Sender", "Message"])

@app.post("/chat")
def process_chat(request: ChatRequest):
    user_message = request.message
    session_id = request.session_id
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Write to Logbook
    with open(log_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, session_id, "User", user_message])
    
    # NEW: Check if this table needs a brand new chair pulled up
    if session_id not in active_sessions:
        active_sessions[session_id] = client.chats.create(
            model='gemini-2.5-flash',
            config={"system_instruction": "You are a helpful AI assistant."}
        )
    
    try:
        # Send the message to this specific table's memory session
        response = active_sessions[session_id].send_message(user_message)
        ai_reply = response.text
        
    except Exception as e:
        ai_reply = f"The Chef had an error: {str(e)}"
    
    # Write to Logbook
    with open(log_file, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, session_id, "AI", ai_reply])
    
    return {"reply": ai_reply}
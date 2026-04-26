"""
Dark Tower Chatbot - FastAPI Server
Exposes the chatbot as a REST API for local development and Hugging Face Spaces deployment.
"""

import os
import uuid
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, List, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import chatbot components
from chatbot import DarkTowerChatbot

# ---------------------------------------------------------------------------
# Session store — purely in-memory, no persistence, no database
# ---------------------------------------------------------------------------

# Maximum number of individual messages (user + assistant) kept per session.
# 12 = 6 full exchange pairs, giving the LLM a comfortable sliding window.
MAX_HISTORY_MESSAGES = 12

# Sessions are pruned after this many minutes of inactivity.
SESSION_TTL_MINUTES = 30


@dataclass
class SessionData:
    """Holds the conversation history for a single browser session."""
    # List of {role: "user"|"assistant", content: str} dicts in chronological order
    history: List[Dict[str, str]] = field(default_factory=list)
    last_active: datetime = field(default_factory=datetime.utcnow)

    def add_exchange(self, user_text: str, assistant_text: str) -> None:
        """Append one Q&A pair and trim to the sliding window."""
        self.history.append({"role": "user",      "content": user_text})
        self.history.append({"role": "assistant",  "content": assistant_text})
        # Keep only the most recent MAX_HISTORY_MESSAGES messages
        if len(self.history) > MAX_HISTORY_MESSAGES:
            self.history = self.history[-MAX_HISTORY_MESSAGES:]
        self.last_active = datetime.utcnow()

    def get_history_for_llm(self) -> List[Dict[str, str]]:
        """
        Return history to pass to Groq — everything except the LAST user entry
        (the current question is built separately with RAG context injected).
        """
        # Drop the last user message; the caller will inject RAG context for it
        if self.history and self.history[-1]["role"] == "user":
            return self.history[:-1]
        return self.history


# Global session store: session_id (str) → SessionData
_sessions: Dict[str, SessionData] = {}


def get_or_create_session(session_id: Optional[str]) -> tuple[str, SessionData]:
    """Look up an existing session or create a fresh one. Returns (sid, data)."""
    if session_id and session_id in _sessions:
        session = _sessions[session_id]
        session.last_active = datetime.utcnow()
        return session_id, session

    # Unknown or missing session — start clean
    new_id = str(uuid.uuid4())
    new_session = SessionData()
    _sessions[new_id] = new_session
    return new_id, new_session


async def _cleanup_expired_sessions() -> None:
    """Background task: remove sessions idle for longer than SESSION_TTL_MINUTES."""
    while True:
        await asyncio.sleep(300)  # run every 5 minutes
        cutoff = datetime.utcnow() - timedelta(minutes=SESSION_TTL_MINUTES)
        expired = [sid for sid, s in _sessions.items() if s.last_active < cutoff]
        for sid in expired:
            del _sessions[sid]
        if expired:
            print(f"[*] Pruned {len(expired)} expired session(s). Active: {len(_sessions)}")


# ---------------------------------------------------------------------------
# App lifecycle
# ---------------------------------------------------------------------------

# Global chatbot instance
chatbot: Optional[DarkTowerChatbot] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize chatbot and background cleanup on startup."""
    global chatbot
    print("[*] Starting Dark Tower Oracle API...")
    chatbot = DarkTowerChatbot()

    # Launch the session-cleanup daemon
    cleanup_task = asyncio.create_task(_cleanup_expired_sessions())

    yield

    # Graceful shutdown
    cleanup_task.cancel()
    print("[*] Shutting down...")


app = FastAPI(
    title="Dark Tower Oracle API",
    description="An API for querying knowledge about Stephen King's Dark Tower series",
    version="1.1.0",
    lifespan=lifespan,
)

# CORS middleware - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    question: str
    spoiler_mode: bool = False
    book_limit: Optional[str] = None
    show_sources: bool = True
    # Optional: client sends back the session_id it received on the first turn.
    # If omitted or unknown, the server creates a new session automatically.
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    spoiler_mode: bool
    book_limit: Optional[str]
    # Always returned so the client can store and reuse it for the next message.
    session_id: str


class SettingsRequest(BaseModel):
    spoiler_mode: Optional[bool] = None
    book_limit: Optional[str] = None


class SettingsResponse(BaseModel):
    spoiler_mode: bool
    book_limit: Optional[str]
    message: str


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "message": "Long days and pleasant nights, traveler!",
        "description": "Dark Tower Oracle API - Ask questions about Roland's journey",
        "endpoints": {
            "/chat":     "POST - Ask a question (pass session_id to maintain context)",
            "/settings": "GET/POST - View or update spoiler settings",
            "/books":    "GET - List all books in reading order",
            "/health":   "GET - Health check",
        },
    }


@app.get("/health")
async def health_check():
    """Health check."""
    return {
        "status": "healthy",
        "message": "The Tower stands.",
        "active_sessions": len(_sessions),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Ask a question about the Dark Tower series.

    - **question**: Your question about the series
    - **session_id**: Opaque token returned by the previous response; omit on the first message
    - **spoiler_mode**: Set to true to allow spoilers (default: false)
    - **book_limit**: Limit responses to a specific book (e.g., \"Wizard and Glass\")
    - **show_sources**: Include source references (default: true)

    The server keeps the last 6 exchange pairs (12 messages) per session in memory.
    Sessions expire after 30 minutes of inactivity and are never written to disk.
    """
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # Resolve or create a session
    session_id, session = get_or_create_session(request.session_id)

    # Apply per-request chatbot settings
    chatbot.spoiler_mode = request.spoiler_mode
    if request.book_limit:
        result = chatbot.set_book_limit(f"read until {request.book_limit}")
        if "could not discern" in result.lower():
            raise HTTPException(status_code=400, detail=f"Invalid book: {request.book_limit}")
    else:
        chatbot.book_limit = None

    # --- Conversational shortcut (greetings, thanks, help, etc.) ---
    # These don't use RAG, but we still record them in history so the
    # LLM has a natural conversation flow.
    convo_response = chatbot.handle_conversation(question)
    if convo_response:
        session.add_exchange(question, convo_response)
        return ChatResponse(
            answer=convo_response,
            sources=[],
            spoiler_mode=chatbot.spoiler_mode,
            book_limit=chatbot.book_limit,
            session_id=session_id,
        )

    # --- RAG answer with conversation history ---
    # Pass all previous turns; ask() will inject RAG context into the current question.
    prior_history = session.get_history_for_llm()

    answer = chatbot.ask(
        question,
        show_sources=False,
        conversation_history=prior_history if prior_history else None,
    )

    # Persist this exchange to the session (raw user text, clean LLM answer)
    session.add_exchange(question, answer)

    # Gather sources separately (they're shown in the UI, not stored in history)
    results = chatbot.search(question, top_k=5)
    sources = list(set(r["source"] for r in results)) if request.show_sources else []

    return ChatResponse(
        answer=answer,
        sources=sources,
        spoiler_mode=chatbot.spoiler_mode,
        book_limit=chatbot.book_limit,
        session_id=session_id,
    )


@app.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current spoiler and book limit settings."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    return SettingsResponse(
        spoiler_mode=chatbot.spoiler_mode,
        book_limit=chatbot.book_limit,
        message="Current settings retrieved",
    )


@app.post("/settings", response_model=SettingsResponse)
async def update_settings(request: SettingsRequest):
    """Update spoiler and book limit settings."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")

    messages = []

    if request.spoiler_mode is not None:
        chatbot.spoiler_mode = request.spoiler_mode
        messages.append(
            "Spoilers enabled - all shall be revealed"
            if request.spoiler_mode
            else "Spoiler protection enabled"
        )

    if request.book_limit is not None:
        if request.book_limit.lower() in ["none", "all", ""]:
            chatbot.book_limit = None
            messages.append("Book limit removed")
        else:
            result = chatbot.set_book_limit(f"read until {request.book_limit}")
            if "could not discern" in result.lower():
                raise HTTPException(status_code=400, detail=f"Invalid book: {request.book_limit}")
            messages.append(f"Book limit set to: {chatbot.book_limit}")

    return SettingsResponse(
        spoiler_mode=chatbot.spoiler_mode,
        book_limit=chatbot.book_limit,
        message="; ".join(messages) if messages else "No changes made",
    )


@app.get("/books")
async def list_books():
    """List all Dark Tower books in reading order."""
    from chatbot import BOOK_ORDER

    books = [
        {"number": i + 1, "title": name, "aliases": aliases}
        for i, (name, aliases) in enumerate(BOOK_ORDER)
    ]
    return {"message": "The path to the Tower, in order:", "books": books}


# Run with: uvicorn server:app --reload (from backend/)
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)

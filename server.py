"""
Dark Tower Chatbot - FastAPI Server
Exposes the chatbot as a REST API for local development and Render deployment.
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager

# Import chatbot components
from chatbot import DarkTowerChatbot

# Global chatbot instance
chatbot: Optional[DarkTowerChatbot] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize chatbot on startup."""
    global chatbot
    print("🗼 Starting Dark Tower Oracle API...")
    chatbot = DarkTowerChatbot()
    yield
    print("👋 Shutting down...")


app = FastAPI(
    title="Dark Tower Oracle API",
    description="An API for querying knowledge about Stephen King's Dark Tower series",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    question: str
    spoiler_mode: bool = False
    book_limit: Optional[str] = None
    show_sources: bool = True


class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    spoiler_mode: bool
    book_limit: Optional[str]


class SettingsRequest(BaseModel):
    spoiler_mode: Optional[bool] = None
    book_limit: Optional[str] = None


class SettingsResponse(BaseModel):
    spoiler_mode: bool
    book_limit: Optional[str]
    message: str


# API Endpoints
@app.get("/")
async def root():
    """Welcome endpoint."""
    return {
        "message": "Long days and pleasant nights, traveler!",
        "description": "Dark Tower Oracle API - Ask questions about Roland's journey",
        "endpoints": {
            "/chat": "POST - Ask a question",
            "/settings": "GET/POST - View or update spoiler settings",
            "/books": "GET - List all books in reading order",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check():
    """Health check for Render."""
    return {"status": "healthy", "message": "The Tower stands."}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Ask a question about the Dark Tower series.
    
    - **question**: Your question about the series
    - **spoiler_mode**: Set to true to allow spoilers (default: false)
    - **book_limit**: Limit responses to a specific book (e.g., "Wizard and Glass")
    - **show_sources**: Include source references (default: true)
    """
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Apply settings for this request
    chatbot.spoiler_mode = request.spoiler_mode
    
    # Handle book limit
    if request.book_limit:
        result = chatbot.set_book_limit(f"read until {request.book_limit}")
        if "could not discern" in result.lower():
            raise HTTPException(status_code=400, detail=f"Invalid book: {request.book_limit}")
    else:
        chatbot.book_limit = None
    
    # Check for conversational response first
    convo_response = chatbot.handle_conversation(request.question)
    if convo_response:
        return ChatResponse(
            answer=convo_response,
            sources=[],
            spoiler_mode=chatbot.spoiler_mode,
            book_limit=chatbot.book_limit
        )
    
    # Get answer from chatbot
    response = chatbot.ask(request.question, show_sources=False)
    
    # Get sources separately
    results = chatbot.search(request.question, top_k=5)
    sources = list(set(r['source'] for r in results)) if request.show_sources else []
    
    return ChatResponse(
        answer=response,
        sources=sources,
        spoiler_mode=chatbot.spoiler_mode,
        book_limit=chatbot.book_limit
    )


@app.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current spoiler and book limit settings."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    return SettingsResponse(
        spoiler_mode=chatbot.spoiler_mode,
        book_limit=chatbot.book_limit,
        message="Current settings retrieved"
    )


@app.post("/settings", response_model=SettingsResponse)
async def update_settings(request: SettingsRequest):
    """Update spoiler and book limit settings."""
    if not chatbot:
        raise HTTPException(status_code=503, detail="Chatbot not initialized")
    
    messages = []
    
    if request.spoiler_mode is not None:
        chatbot.spoiler_mode = request.spoiler_mode
        if request.spoiler_mode:
            messages.append("Spoilers enabled - all shall be revealed")
        else:
            messages.append("Spoiler protection enabled")
    
    if request.book_limit is not None:
        if request.book_limit.lower() in ['none', 'all', '']:
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
        message="; ".join(messages) if messages else "No changes made"
    )


@app.get("/books")
async def list_books():
    """List all Dark Tower books in reading order."""
    from chatbot import BOOK_ORDER
    
    books = [
        {"number": i + 1, "title": name, "aliases": aliases}
        for i, (name, aliases) in enumerate(BOOK_ORDER)
    ]
    
    return {
        "message": "The path to the Tower, in order:",
        "books": books
    }


# Run with: uvicorn server:app --reload
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)

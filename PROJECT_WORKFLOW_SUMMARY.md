# Project Workflow Summary

## Overview
The **Dark Tower Chatbot** project is a full‑stack application consisting of:
- **Backend** – FastAPI server exposing a REST API that powers the chatbot logic.
- **Frontend** – React single‑page app that provides a UI for users to interact with the bot.
- **Data assets** – FAISS index and metadata for Retrieval‑Augmented Generation (RAG).
- **Environment** – `.env` holds the `GROQ_API_KEY` used to call the Groq LLM.

---

## Backend Workflow
### Entry point
- **`backend/server.py`** creates a FastAPI app (`app`).  The command `uvicorn server:app` runs this file.
- Routes defined:
  - `GET /` – basic welcome/info.
  - `GET /health` – health check (active session count).
  - `POST /chat` – main chat endpoint.
  - `GET /settings` / `POST /settings` – read/write spoiler & book‑limit settings.
  - `GET /books` – returns the canonical Dark Tower reading order.

### Session handling
- In‑memory dict `_sessions: Dict[str, SessionData]` stores per‑user conversation history.
- `SessionData` keeps a list of `{role, content}` messages (max 12 entries) and a `last_active` timestamp.
- `get_or_create_session` returns an existing session or creates a new UUID.
- Background coroutine `_cleanup_expired_sessions` prunes sessions after 30 min of inactivity.

### Chatbot core (`backend/chatbot.py`)
1. **Initialization**
   - Loads a **SentenceTransformer** (`all‑MiniLM‑L6‑v2`).
   - Reads the FAISS index (`embeddings/index.faiss`) and accompanying metadata (`embeddings/metadata.json`).
   - Instantiates a **Groq** client with the API key from `.env`.
   - Sets default spoiler mode **off** and no book limit.
2. **Request processing (`POST /chat`)
   - Parses `ChatRequest` (question, optional `session_id`, `spoiler_mode`, `book_limit`, `show_sources`).
   - Updates the global chatbot instance with the provided settings.
   - Handles casual conversation shortcuts (greetings, help, status, spoiler toggles, book limit commands) via `handle_conversation`.
   - If not a shortcut, retrieves the session, builds conversation history, and calls `DarkTowerChatbot.ask`.
3. **RAG pipeline (`DarkTowerChatbot.ask`)
   - Detects *reading‑order* queries; if matched, returns the static `CANONICAL_BOOK_ORDER_TEXT` without invoking FAISS.
   - Otherwise, calls `search` to get top‑k relevant chunks from FAISS.
   - **`search`** embeds the query, retrieves candidates, classifies intent/category, applies score boosts, and returns the best results.
   - `build_context` formats the selected chunks with source labels.
   - System prompt is assembled from:
     - `BASE_SYSTEM_PROMPT`
     - `SPOILER_FREE_PROMPT` (if `spoiler_mode` is **off**)
     - `BOOK_LIMITED_PROMPT` (if a book limit is set)
   - Sends the combined messages (`system` + optional history + current user message) to Groq.
   - Returns the LLM answer, optionally appending a list of unique sources.
4. **Settings endpoints**
   - `GET /settings` returns current `spoiler_mode` and `book_limit`.
   - `POST /settings` updates those flags, validating book names via `set_book_limit`.

### Supporting modules
- **`backend/scraper/`** – utilities for scraping source pages (used when building the FAISS index, not at runtime).
- **`backend/processor/`** – `chunk_text.py` contains logic for splitting raw texts into searchable chunks (also used during index creation).

---

## Frontend Workflow
- **Entry point** – `frontend/src/App.jsx` sets up a React Router with three pages:
  - `/` → `Home`
  - `/chat` → `Chat`
  - `/about` → `About`
- The **Chat** page (implementation not shown) calls the backend API:
  - `POST /chat` with the user’s question and the stored `session_id`.
  - Receives `ChatResponse` containing `answer`, optional `sources`, and the new `session_id`.
- UI toggles (e.g., spoiler mode, book limit) are sent via the **Settings** endpoint.
- Development server runs via `npm start` and proxies requests to `http://localhost:8000` (the FastAPI server).

---

## Data Flow Summary
1. **User types a question** in the React UI.
2. **Frontend** sends a `POST /chat` request (including any session ID).
3. **FastAPI** receives the request, obtains/creates a session, and updates spoiler/book settings.
4. If the message matches a *conversation shortcut* (greetings, help, status, spoiler toggle, book limit), the backend returns a predefined response.
5. Otherwise, the backend:
   - Calls `DarkTowerChatbot.search` → FAISS → metadata → relevance boost.
   - Builds a context string from the top chunks.
   - Constructs a system prompt based on spoiler/book settings.
   - Sends the prompt + context + user question to Groq.
   - Receives the LLM answer, appends source citations (if requested).
6. The **answer and updated `session_id`** are returned to the frontend.
7. Frontend displays the answer (and source list) and stores the `session_id` for the next turn.
8. Background session‑cleanup task runs every 5 minutes, discarding idle sessions.

---

## Key Configuration Files
- **`.env`** – defines `GROQ_API_KEY` (required for LLM access).
- **`backend/requirements.txt`** – Python dependencies (FastAPI, faiss‑cpu, sentence‑transformers, python‑dotenv, groq, etc.).
- **`frontend/package.json`** – React dependencies and start script.
- **`backend/embeddings/index.faiss` & `metadata.json`** – pre‑computed vector index and chunk metadata for RAG.

---

## Quick Reference Links
- [backend/server.py](file:///e:/Data%20Science%20projects/Dark%20Tower%20Chatbot/backend/server.py)
- [backend/chatbot.py](file:///e:/Data%20Science%20projects/Dark%20Tower%20Chatbot/backend/chatbot.py)
- [frontend/src/App.jsx](file:///e:/Data%20Science%20projects/Dark%20Tower%20Chatbot/frontend/src/App.jsx)

---

*This markdown file captures the complete project workflow and should serve as a foundation for any further development or debugging.*

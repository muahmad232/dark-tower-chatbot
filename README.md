<p align="center">
  <img src="frontend/src/assests/icon/dark-tower-icon.png" alt="KaGuide Logo" width="120" height="120">
</p>

<h1 align="center">🗼 KaGuide - Dark Tower Chatbot</h1>

<p align="center">
  <strong>An intelligent RAG-powered chatbot for Stephen King's Dark Tower series</strong>
</p>

<p align="center">
  <a href="https://ka-guide.vercel.app">
    <img src="https://img.shields.io/badge/🌐_Live_Demo-ka--guide.vercel.app-blue?style=for-the-badge" alt="Live Demo">
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/Groq-LLM-orange?style=flat-square" alt="Groq">
  <img src="https://img.shields.io/badge/🤗_Hugging_Face-Spaces-yellow?style=flat-square" alt="Hugging Face">
  <img src="https://img.shields.io/badge/Vercel-Deployed-black?style=flat-square&logo=vercel&logoColor=white" alt="Vercel">
</p>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **RAG-Powered Search** | Semantic search through Dark Tower wiki content using FAISS vector index |
| 🤖 **LLM Responses** | Natural language answers powered by Groq's Llama 3.1 |
| 🧠 **Session Memory** | Remembers the last 6 exchanges per conversation — follow-up questions work naturally |
| 🛡️ **Spoiler Protection** | Set your reading progress to avoid spoilers from later books |
| 📚 **Book-Aware Context** | Responses limited to books you've read |
| 📖 **Accurate Book Order** | Canonical reading order is hardcoded and bypasses FAISS — always correct |
| 🎨 **Themed UI** | Immersive Dark Tower aesthetic with Ka sigil animation and markdown rendering |
| ⚡ **Fast & Free** | Deployed on Hugging Face Spaces (16GB RAM) and Vercel |

---

## 🎮 Live Demo

**👉 [https://ka-guide.vercel.app](https://ka-guide.vercel.app)**

<p align="center">
  <img src="https://img.shields.io/badge/Status-Live-brightgreen?style=for-the-badge" alt="Status">
</p>

---

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────────────────────────┐
│                 │         │          Backend (HF Spaces)          │
│   React App     │  HTTP   │  ┌──────────┐    ┌────────────────┐  │
│   (Vercel)      │ ──────► │  │ FastAPI  │───►│   Groq LLM     │  │
│                 │         │  └────┬─────┘    │ llama-3.1-8b   │  │
│  • Chat UI      │         │       │          └────────────────┘  │
│  • Settings     │         │       ▼                              │
│  • Session      │         │  ┌──────────┐    ┌────────────────┐  │
│    Memory       │         │  │  FAISS   │◄───│   Sentence     │  │
│                 │         │  │  Index   │    │  Transformer   │  │
└─────────────────┘         │  └──────────┘    └────────────────┘  │
    sessionStorage           │                                      │
    (tab-scoped session_id)  │  In-memory session store (RAM only)  │
                             └──────────────────────────────────────┘
```

### Conversation Flow

```
User message + session_id
        │
        ├─► Order question?  YES ──► Canonical list (bypass FAISS) ──► Groq ──► Answer
        │
        └─► NO ──► FAISS semantic search ──► top-5 chunks ──► Rerank ──► Groq (+ history) ──► Answer
                                                                               │
                                                                        Session history
                                                                        (last 6 pairs)
```

---

## 🛠️ Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) | Core language |
| ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) | REST API framework |
| ![Groq](https://img.shields.io/badge/Groq-FF6600?style=flat-square) | LLM inference (Llama 3.1 8B) |
| ![HuggingFace](https://img.shields.io/badge/🤗_Hugging_Face-FFD21E?style=flat-square) | Model hosting & deployment |
| **FAISS** | Vector similarity search |
| **Sentence Transformers** | Text embeddings (all-MiniLM-L6-v2) |

### Frontend
| Technology | Purpose |
|------------|---------|
| ![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black) | UI framework |
| ![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white) | Hosting & deployment |
| **React Router** | Client-side routing |
| **CSS3** | Custom Dark Tower theming |
| **sessionStorage** | Tab-scoped session memory (auto-cleared on tab close) |

---

## 📁 Project Structure

```
dark-tower-chatbot/
├── backend/                      # FastAPI backend (Hugging Face Spaces)
│   ├── chatbot.py                # Core chatbot: RAG, session memory, spoiler logic
│   ├── server.py                 # FastAPI REST API + in-memory session store
│   ├── Dockerfile                # Container configuration
│   ├── requirements.txt          # Python dependencies
│   ├── data/
│   │   ├── raw_pages.json        # Scraped wiki data
│   │   └── chunks.json           # Processed text chunks
│   ├── embeddings/
│   │   ├── index.faiss           # Vector search index
│   │   ├── metadata.json         # Chunk metadata
│   │   └── build_index.py        # Index builder
│   ├── scraper/                  # Wiki scraping tools
│   └── processor/                # Text processing
│
├── frontend/                     # React app (Vercel)
│   ├── public/                   # Static assets
│   ├── src/
│   │   ├── components/           # Reusable UI components
│   │   │   ├── Header/           # Navigation header
│   │   │   ├── Footer/           # Page footer
│   │   │   ├── ChatMessage/      # Chat bubbles with markdown rendering
│   │   │   └── SettingsPanel/    # Spoiler settings
│   │   ├── pages/                # Route pages
│   │   │   ├── Home/             # Landing with Ka sigil
│   │   │   ├── Chat/             # Chat interface + session memory
│   │   │   └── About/            # About page
│   │   └── assests/              # Images & icons
│   ├── package.json
│   └── vercel.json               # Vercel config
│
└── README.md
```

---

## 🧠 Session Memory

KaGuide maintains a **temporary, in-memory conversation history** so you can ask natural follow-up questions:

> *"What is the Dark Tower?"* → *"How is Roland related to it?"* → *"And what about Jake?"*

### How it works

| Aspect | Detail |
|--------|--------|
| **Storage** | Python dict in RAM — no database, no disk writes |
| **Scope** | Per browser tab via `sessionStorage` — cleared automatically on tab close |
| **Window** | Last **6 exchange pairs** (12 messages) passed to the LLM |
| **Session ID** | UUID4 generated server-side on the first message, returned to the client |
| **Expiry** | Sessions idle for **30 minutes** are pruned by a background task |
| **Privacy** | Memory never persists beyond the current server process or browser tab |

The `session_id` is an opaque token. Each browser tab gets its own independent conversation history.

---

## 🚀 Deployment

### Backend - Hugging Face Spaces

The backend is deployed on **Hugging Face Spaces** with Docker SDK:

| Setting | Value |
|---------|-------|
| **Platform** | [Hugging Face Spaces](https://huggingface.co/spaces) |
| **SDK** | Docker |
| **Hardware** | CPU Basic (Free - 16GB RAM) |
| **URL** | `https://muahmad123-dark-tower-chatbot.hf.space` |

**Environment Variables (Secrets):**
- `GROQ_API_KEY` - Your Groq API key

### Frontend - Vercel

The frontend is deployed on **Vercel**:

| Setting | Value |
|---------|-------|
| **Platform** | [Vercel](https://vercel.com) |
| **Framework** | Create React App |
| **URL** | [https://ka-guide.vercel.app](https://ka-guide.vercel.app) |

**Environment Variables:**
- `REACT_APP_API_URL` - Backend API URL

---

## 💻 Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Groq API Key](https://console.groq.com/keys) (free)

### Backend Setup

```bash
# Clone the repository
git clone https://github.com/muahmad232/dark-tower-chatbot.git
cd dark-tower-chatbot

# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Set up environment variables
cp backend/.env.example backend/.env
# Edit .env and add your GROQ_API_KEY

# Run the server
cd backend
uvicorn server:app --reload --port 8000
```

### Frontend Setup

```bash
# In a new terminal
cd frontend

# Install dependencies
npm install

# Run development server
npm start
```

Visit: **http://localhost:3000**

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Welcome message & API info |
| `/health` | GET | Health check + active session count |
| `/chat` | POST | Ask a question (supports session memory) |
| `/settings` | GET | Get current settings |
| `/settings` | POST | Update spoiler/book settings |
| `/books` | GET | List all books in reading order |

### `/chat` Request & Response

```bash
curl -X POST "https://muahmad123-dark-tower-chatbot.hf.space/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who is Roland Deschain?",
    "spoiler_mode": false,
    "book_limit": "The Gunslinger",
    "show_sources": true,
    "session_id": null
  }'
```

**Request fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `question` | string | required | Your question |
| `spoiler_mode` | bool | `false` | Allow full spoilers |
| `book_limit` | string\|null | `null` | Restrict to books up to this title |
| `show_sources` | bool | `true` | Include wiki source references |
| `session_id` | string\|null | `null` | Session token from a previous response; omit on the first message |

**Response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `answer` | string | Markdown-formatted answer |
| `sources` | string[] | Wiki pages used as context |
| `spoiler_mode` | bool | Active spoiler setting |
| `book_limit` | string\|null | Active book limit |
| `session_id` | string | Store this and send it with the next message to maintain context |

---

## 📚 Dark Tower Book Order

| # | Title | Year |
|---|-------|------|
| 1 | The Gunslinger | 1982 |
| 2 | The Drawing of the Three | 1987 |
| 3 | The Waste Lands | 1991 |
| 4 | Wizard and Glass | 1997 |
| 4.5 | The Wind Through the Keyhole | 2012 |
| 5 | Wolves of the Calla | 2003 |
| 6 | Song of Susannah | 2004 |
| 7 | The Dark Tower | 2004 |

---

## 🛡️ Spoiler Protection

KaGuide includes built-in spoiler protection:

- **Spoiler Mode OFF** (default): Gives general overviews without revealing deaths, endings, or major plot twists
- **Book Limit**: Set your reading progress to only receive information from books you've completed
- **Safe Responses**: If you ask about events beyond your book limit, KaGuide will tell you to keep reading!

---

## 🎨 Markdown Rendering

The chat interface renders LLM responses as formatted text — no raw asterisks:

| Markdown | Rendered as |
|----------|-------------|
| `**Roland Deschain**` | **Roland Deschain** |
| `*ka-tet*` | *ka-tet* |
| `- item` / `• item` | Bullet list with gold markers |
| `1. item` | Numbered list |
| Blank line | Paragraph spacing |

---

## 🙏 Acknowledgments

- **Stephen King** - For creating the incredible Dark Tower universe
- [Dark Tower Wiki](https://darktower.fandom.com) - Source of knowledge
- [Groq](https://groq.com) - Fast LLM inference
- [Hugging Face](https://huggingface.co) - Free model hosting
- [Vercel](https://vercel.com) - Frontend hosting

---

## 📄 License

This project is for **educational purposes only**.

Dark Tower content and characters are the property of **Stephen King**. This is a fan project and is not affiliated with or endorsed by Stephen King or his publishers.

---

<p align="center">
  <i>"Go then, there are other worlds than these."</i>
  <br>
  — Jake Chambers
</p>

<p align="center">
  <strong>Long days and pleasant nights, traveler! 🗼</strong>
</p>

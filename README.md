# Dark Tower Chatbot - KaGuide

An intelligent RAG-powered chatbot for answering questions about Stephen King's Dark Tower series. Features a React frontend with immersive Dark Tower theming and spoiler protection.

## Features

- **Comprehensive Wiki Scraping**: Scrapes character, book, place, concept, and event pages from the Dark Tower Wiki
- **Semantic Chunking**: Paragraph-aware text chunking with metadata classification (definition, background, plot, death, summary, location)
- **Query-Aware Retrieval**: Intent detection that prioritizes relevant chunk types based on query patterns
- **Category Matching**: Boosts results from matching categories (character queries → character chunks, etc.)
- **LLM-Powered Responses**: Uses Groq API with Llama 3.1 for well-structured, contextual answers
- **Spoiler Protection**: Set your reading progress to avoid spoilers from later books
- **Dark Tower Themed UI**: Immersive React frontend with custom Ka sigil, icons, and atmospheric design

## Project Structure

```
├── backend/                  # FastAPI backend (deploy to Railway)
│   ├── chatbot.py            # Main chatbot with Groq LLM
│   ├── server.py             # FastAPI server
│   ├── requirements.txt      # Python dependencies
│   ├── Procfile              # Start command
│   ├── railway.json          # Railway configuration
│   ├── scraper/
│   │   ├── scrape_all.py     # Wiki scraper
│   │   └── scrape_page.py    # Single page scraper
│   ├── processor/
│   │   └── chunk_text.py     # Text chunking
│   ├── embeddings/
│   │   ├── build_index.py    # FAISS index builder
│   │   ├── index.faiss       # Vector index
│   │   └── metadata.json     # Chunk metadata
│   └── data/
│       ├── raw_pages.json    # Scraped wiki data
│       └── chunks.json       # Processed chunks
├── frontend/                 # React frontend
│   ├── public/               # Static assets
│   ├── src/
│   │   ├── components/       # Reusable UI components
│   │   │   ├── Header/       # Navigation header
│   │   │   ├── Footer/       # Page footer
│   │   │   ├── ChatMessage/  # Chat message display
│   │   │   └── SettingsPanel/ # Spoiler settings
│   │   ├── pages/            # Route pages
│   │   │   ├── Home/         # Landing page with Ka sigil
│   │   │   ├── Chat/         # Chat interface
│   │   │   └── About/        # About page
│   │   ├── assests/          # Images and icons
│   │   ├── App.jsx           # Router setup
│   │   └── App.css           # Global styles
│   └── package.json
└── README.md
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/muahmad232/dark-tower-chatbot.git
   cd dark-tower-chatbot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. Set up your API key:
   ```bash
   # Create .env file in backend folder
   echo "GROQ_API_KEY=your_api_key_here" > backend/.env
   ```
   Get your free API key at: https://console.groq.com/keys

5. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```

## Usage

### Run Both Backend and Frontend

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn server:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm start
```

Then visit: http://localhost:3000

### Run the CLI Chatbot (Alternative)

```bash
cd backend
python chatbot.py
```

Commands in chat:
- Type your question and press Enter
- `spoilers on/off` - Toggle spoiler protection
- `read until [book]` - Set your reading progress
- `sources off` - Hide source references
- `sources on` - Show source references  
- `help` - Show all commands
- `quit` or `exit` - End the conversation

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Welcome message |
| `/health` | GET | Health check |
| `/chat` | POST | Ask a question |
| `/settings` | GET/POST | View/update spoiler settings |
| `/books` | GET | List books in order |

### Rebuild the Knowledge Base

#### 1. Scrape Wiki Data

```bash
cd backend
python scraper/scrape_all.py --important-only --delay 0.3

# Scrape all discovered pages (takes longer)
python scraper/scrape_all.py --delay 0.5
```

#### 2. Process and Chunk Text

```bash
python processor/chunk_text.py
```

#### 3. Build FAISS Index

```bash
python embeddings/build_index.py
```

## Deployment

### Backend (Railway)

1. Go to [railway.app](https://railway.app) and create a new project
2. Select **Deploy from GitHub repo**
3. Connect your repository: `muahmad232/dark-tower-chatbot`
4. Configure the service:
   - **Root Directory**: `backend`
   - Railway will auto-detect Python and use `railway.json`
5. Add Environment Variables:
   - `GROQ_API_KEY` = your Groq API key
   - `ALLOWED_ORIGINS` = your frontend URL (after deploying frontend)
6. Deploy! You'll get a URL like `https://dark-tower-chatbot-production.up.railway.app`

### Frontend (Vercel)

1. Go to [vercel.com](https://vercel.com) and create a new project
2. Import your GitHub repository
3. Configure:
   - **Root Directory**: `frontend`
   - **Framework Preset**: Create React App
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
4. Add Environment Variable:
   - `REACT_APP_API_URL` = `https://your-backend.up.railway.app`
5. Deploy!

After frontend is deployed, go back to Railway and update:
- `ALLOWED_ORIGINS` = `https://your-frontend.vercel.app`

## Screenshots

**Home Page** - Features the spinning Ka sigil symbolizing "Ka is a wheel"

**Chat Interface** - Dark Tower themed chat with spoiler protection settings

**About Page** - Information about the series and how KaGuide works

## Categories

The system categorizes content into:
- **character**: Roland, Eddie, Jake, Susannah, etc.
- **book**: The Gunslinger, Drawing of the Three, etc.
- **place**: Mid-World, Gilead, Dark Tower, etc.
- **concept**: Ka, Ka-tet, High Speech, etc.
- **object**: Sandalwood Guns, Black Thirteen, etc.
- **event**: Battle of Jericho Hill, Fall of Gilead, etc.

## Technical Details

- **Backend**: Python, FastAPI, Groq API (`llama-3.1-8b-instant`)
- **Frontend**: React, React Router, CSS with custom theming
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Vector Index**: FAISS IndexFlatIP (inner product similarity)
- **Chunk Size**: 300 tokens with 75 token overlap
- **Tokenizer**: tiktoken `cl100k_base`

## License

This project is for educational purposes. Dark Tower content belongs to Stephen King.

---

*"Go then, there are other worlds than these."*

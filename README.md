# Dark Tower Chatbot

An intelligent RAG-powered chatbot for answering questions about Stephen King's Dark Tower series. Uses semantic search with FAISS vector indexing and Groq's Llama model for natural language responses.

## Features

- **Comprehensive Wiki Scraping**: Scrapes character, book, place, concept, and event pages from the Dark Tower Wiki
- **Semantic Chunking**: Paragraph-aware text chunking with metadata classification (definition, background, plot, death, summary, location)
- **Query-Aware Retrieval**: Intent detection that prioritizes relevant chunk types based on query patterns
- **Category Matching**: Boosts results from matching categories (character queries → character chunks, etc.)
- **LLM-Powered Responses**: Uses Groq API with Llama 3.1 for well-structured, contextual answers

## Project Structure

```
├── backend/
│   ├── chatbot.py         # Main chatbot with Groq LLM integration
│   ├── server.py          # FastAPI server for API access
│   ├── scraper/
│   │   ├── scrape_all.py  # Comprehensive wiki scraper
│   │   └── scrape_page.py # Single page scraper
│   ├── processor/
│   │   └── chunk_text.py  # Category-aware semantic chunking
│   ├── embeddings/
│   │   ├── build_index.py # FAISS index builder
│   │   ├── test_search.py # Search testing
│   │   ├── index.faiss    # Vector index
│   │   └── metadata.json  # Chunk metadata
│   └── data/
│       ├── raw_pages.json # Scraped wiki data
│       └── chunks.json    # Processed chunks
├── requirements.txt       # Python dependencies
├── Procfile              # Render deployment
├── render.yaml           # Render configuration
└── .env                  # API keys (not in git)
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

3. Install dependencies:
   ```bash
   pip install requests beautifulsoup4 lxml tiktoken sentence-transformers faiss-cpu groq python-dotenv
   ```

4. Set up your API key:
   ```bash
   # Create .env file
   echo "GROQ_API_KEY=your_api_key_here" > .env
   ```
   Get your free API key at: https://console.groq.com/keys

## Usage

### Run the API Server

```bash
# From project root
uvicorn backend.server:app --reload
```

Then visit: http://localhost:8000/docs for interactive API documentation.

### Run the CLI Chatbot

```bash
python -m backend.chatbot
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
# Scrape important pages only
python backend/scraper/scrape_all.py --important-only --delay 0.3

# Scrape all discovered pages (takes longer)
python backend/scraper/scrape_all.py --delay 0.5
```

#### 2. Process and Chunk Text

```bash
python backend/processor/chunk_text.py
```

#### 3. Build FAISS Index

```bash
python backend/embeddings/build_index.py
```

#### 4. Test Search (Optional)

```bash
python backend/embeddings/test_search.py
```

## Categories

The system categorizes content into:
- **character**: Roland, Eddie, Jake, Susannah, etc.
- **book**: The Gunslinger, Drawing of the Three, etc.
- **place**: Mid-World, Gilead, Dark Tower, etc.
- **concept**: Ka, Ka-tet, High Speech, etc.
- **object**: Sandalwood Guns, Black Thirteen, etc.
- **event**: Battle of Jericho Hill, Fall of Gilead, etc.

## Technical Details

- **LLM**: Groq API with `llama-3.1-8b-instant`
- **Embedding Model**: `all-MiniLM-L6-v2` (384 dimensions)
- **Vector Index**: FAISS IndexFlatIP (inner product similarity)
- **Chunk Size**: 300 tokens with 75 token overlap
- **Tokenizer**: tiktoken `cl100k_base`

## License

This project is for educational purposes. Dark Tower content belongs to Stephen King.

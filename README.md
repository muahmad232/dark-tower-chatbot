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
├── chatbot.py             # Main chatbot with Groq LLM integration
├── scraper/
│   ├── scrape_all.py      # Comprehensive wiki scraper with category discovery
│   └── scrape_page.py     # Single page scraper with infobox/section parsing
├── processor/
│   └── chunk_text.py      # Category-aware semantic chunking
├── embeddings/
│   ├── build_index.py     # FAISS index builder
│   └── test_search.py     # Query-aware search with intent detection
├── data/
│   ├── raw_pages.json     # Scraped wiki data
│   └── chunks.json        # Processed chunks with metadata
└── embeddings/
    ├── index.faiss        # FAISS vector index
    └── metadata.json      # Chunk metadata for retrieval
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

### Run the Chatbot

```bash
python chatbot.py
```

Commands in chat:
- Type your question and press Enter
- `sources off` - Hide source references
- `sources on` - Show source references  
- `quit` or `exit` - End the conversation

### Rebuild the Knowledge Base

#### 1. Scrape Wiki Data

```bash
# Scrape important pages only
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

#### 4. Test Search (Optional)

```bash
python embeddings/test_search.py
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


# Backend Overview — Dark Tower Chatbot

This document summarizes the backend architecture, components, data flow, and performance/operational expectations for the Dark Tower Chatbot. Use this for interview prep: focus on design choices, trade-offs, and how the pieces fit together.

## High-level architecture

- **Frontend (UI)** communicates with a REST API served by the backend ([backend/server.py](backend/server.py)).
- **API Server** is a FastAPI app that exposes endpoints for `/chat`, `/settings`, `/books`, and `/health`.
- **Core application logic** lives in `DarkTowerChatbot` ([backend/chatbot.py](backend/chatbot.py)) — this class implements RAG (retrieval-augmented generation), conversational shortcuts, spoiler protection, and orchestration of embeddings, FAISS retrieval, and the LLM.
- **Embeddings & index** are built from preprocessed text chunks via the script [backend/embeddings/build_index.py](backend/embeddings/build_index.py) and stored as a FAISS index at `embeddings/index.faiss` with matching `embeddings/metadata.json` for lookup.

## Components and responsibilities

- `DarkTowerChatbot` (`backend/chatbot.py`)
  - Loads the sentence-transformers model `all-MiniLM-L6-v2` for embedding queries and content.
  - Loads FAISS index (`faiss.read_index`) and metadata for retrieval.
  - Implements intent/category classification, query-aware reranking, context building, and the `ask()` method that performs RAG + calls the LLM provider.
  - Handles conversation niceties (greetings/help/shortcuts) so trivial flows don't hit the RAG/LLM path.
  - Enforces spoiler-protection and optional book-limits through system prompt construction.

- Embeddings (`sentence-transformers`)
  - Model: `all-MiniLM-L6-v2` — compact, fast, 384-dim embedding vectors.
  - Used both for building the index (`build_index.py`) and for encoding user queries at runtime.

- FAISS index (`faiss`)
  - Index type: `IndexFlatIP` (inner product) with normalized vectors → cosine similarity.
  - Stores all chunk vectors in-memory for fast nearest-neighbor lookups.
  - Metadata file (`embeddings/metadata.json`) stores text, source, category, chunk_type and extra signals used for reranking.

- LLM provider (`groq` client)
  - The code uses the Groq API via the `groq` Python client. The heavy decoder compute is offloaded to Groq’s service, not run locally.
  - Model configured in the code as `llama-3.1-8b-instant` (fast, lower-latency variant).

- FastAPI server (`backend/server.py`)
  - Exposes the REST interface used by the frontend.
  - Creates a single global `DarkTowerChatbot` instance at startup (via lifespan) to share model, index, and metadata across requests.
  - Implements a simple in-memory session store (`_sessions`) with a `SessionData` dataclass that keeps the last 12 messages (6 exchange pairs) per session.
  - Runs a background task to prune expired sessions every 5 minutes.

- Data pipeline
  - Scraper(s): `backend/scraper/` contain page-scraping logic (fetch pages, produce raw pages).
  - Processor: `backend/processor/chunk_text.py` splits pages into chunks with metadata and optional `text_for_embedding` used by `build_index.py`.
  - Index builder: `backend/embeddings/build_index.py` encodes chunks and writes `embeddings/index.faiss` and `embeddings/metadata.json`.

## Why these choices (rationale)

- SentenceTransformer `all-MiniLM-L6-v2`: small (fast CPU inference), good semantic quality for RAG; practical for local dev and inexpensive embedding ops.
- FAISS IndexFlatIP: simple, exact inner-product search with minimal engineering complexity. For moderate dataset sizes (tens of thousands of chunks), this offers very fast retrieval without the complexity of IVF/HNSW.
- Groq LLM: offloads heavy transformer inference to a hosted service, reducing local resource needs and latency for short responses.
- FastAPI: lightweight, async-friendly, easy to deploy (uvicorn, Docker, or Spaces). Good DX for prototyping and productionizing small services.
- In-memory sessions: simple and stateless from the persistence perspective (no DB needed), keeps operations predictable and easy to reason about.

## Advantages and trade-offs

- Advantages
  - Low operational complexity: embeddings and index are precomputed, LLM compute offloaded, server mainly orchestrates.
  - Fast retrieval: FAISS in-memory gives ms-scale nearest-neighbor queries for moderate index sizes.
  - Predictable costs: embedding model is small; hosted LLM centralizes variable compute billing.
  - Clear separation of concerns: scraper → processor → index builder → server/chatbot.

- Trade-offs / Limitations
  - Memory-bound index: FAISS IndexFlatIP keeps all vectors in memory; for very large corpora (hundreds of thousands to millions of chunks) this becomes costly.
  - No persistence for sessions: a server restart loses user sessions unless external store is added.
  - Single global chatbot instance: this is easy and effective, but scaling to multiple worker processes requires reloading the FAISS index per worker or sharing via a memory-mapped index.
  - Relying on hosted LLM: good for speed and scale, but introduces external dependency, network latency, and possible cost/availability considerations.

## How a query flows (end-to-end)

1. Frontend POSTs `/chat` with `question` and optional `session_id`.
2. Server validates input, resolves or creates a session in `_sessions`.
3. `DarkTowerChatbot.handle_conversation()` checks conversational shortcuts. If matched, return immediately.
4. Otherwise, `ask()` is called: encode query with `SentenceTransformer`, run FAISS search to fetch candidates, rerank by intent/category, build a context string.
5. Build system prompt including spoiler/book-limit settings, assemble messages (system + history + current user message), and call `groq.chat.completions.create()`.
6. Format and return the answer; session stores the user-assistant exchange in memory; server returns `session_id` for next turn.

## Performance and resource estimates (typical)

- Embedding model (`all-MiniLM-L6-v2`):
  - CPU: single query encoding on a modern laptop CPU (4–8 cores) is typically 20–200 ms per query (depends on hardware and batch size). On a single vCPU cloud instance expect ~50–200 ms.
  - Memory: the model (~80–200 MB resident memory depending on transformer runtime) plus transient memory during encoding.

- FAISS index (in-memory):
  - Vector size = `dim` * 4 bytes (float32). With `dim=384`: 1 vector ≈ 1.5 KB.
  - Example: 50k vectors → ~73 MB RAM (50_000 * 384 * 4 ≈ 76.8 MB). Add overhead for FAISS structures and metadata; budget ~1.2× to 1.5× this number.
  - Query CPU: IndexFlatIP performs a dense inner-product over all vectors — cost scales linearly with index size. For moderate sizes (≤100k) a single CPU core can still serve low-latency queries (tens to low hundreds of ms). For larger sizes consider IVF/HNSW indexes or approximate search.

- LLM calls (Groq):
  - Heavy compute offloaded — local server CPU is only used for HTTP request/response handling and serializing messages.
  - Latency depends on remote LLM; expect 200–1000 ms typical for short responses, but this varies.

- API Server (FastAPI + uvicorn):
  - Lightweight I/O and orchestration. Typical CPU usage is low per request; peaks are determined by concurrent requests and LLM latency.
  - Memory: dominated by FAISS index + embedding model footprint + process overhead (tens to a few hundred MB depending on index size and whether model weights are resident).

## Scaling recommendations

- To scale retrieval for large corpora: move to FAISS indexes with IVF/HNSW, or use an ANN service (Milvus, Pinecone, Weaviate).
- For many concurrent requests: run multiple worker processes/containers; either memory-map the FAISS index (`IndexRefine`/`index_file`) or load into each worker and size nodes appropriately.
- Persist sessions to Redis if you need cross-worker sessions or long-lived conversations.
- Cache frequent queries or top-k contexts to reduce repeated embedding + retrieval costs.

## Deployment notes

- Dockerfile and Procfile exist for containerized and simple platform deploys. Use `uvicorn server:app --host 0.0.0.0 --port $PORT` to run the app locally or in a container.
- Keep the `GROQ_API_KEY` and other secrets in environment variables (the app uses `python-dotenv` for local development; in production use provider secrets management).

## Interview talking points (concise)

- This backend is a small, practical example of RAG: precompute embeddings, use FAISS for retrieval, rerank candidates, and call an external LLM for fluent answers.
- Design choices favor simplicity and developer ergonomics: small embedding model, in-memory exact search for clarity, and hosted LLM for heavy compute.
- Key trade-offs: memory vs complexity (IndexFlatIP is simple but memory/compute heavy at scale); session persistence (in-memory is easy but not durable); and vendor dependence for LLM.
- Performance tuning levers I would mention: index type changes (IVF/HNSW), sharding, batching embeddings, caching, moving sessions to Redis, and monitoring LLM latency and costs.

---

## Deep dive — Scraping, Chunking, Embeddings, and FAISS

This project implements a clear pipeline: scrape pages → preprocess & chunk → embed → build FAISS index → serve retrievals at query time. Below are the exact working details and why each step matters.

- Scraping (`backend/scraper/scrape_page.py`)
  - Fetches wiki pages with `requests` and parses HTML using `BeautifulSoup` (lxml parser).
  - Extracts the page `title`, a parsed `infobox` (character/entity structured data), and a content area (`div.mw-parser-output`).
  - `parse_sections()` walks the DOM and groups paragraphs and lists under heading markers (`h2`, `h3`, `h4`), producing a sequence of sections with heading + content.
  - `format_infobox_as_text()` converts the infobox into a compact, human-readable definition block (used to seed the top of the page content) — this gives strong definition signals to the downstream chunk classifier and embeddings.
  - `clean_text()` removes reference markers and normalizes whitespace so downstream tokenization isn't polluted by wiki artifacts.

- Chunking & classification (`backend/processor/chunk_text.py`)
  - Tokenization: uses `tiktoken.get_encoding('cl100k_base')` (same tokenization family used by many LLMs) to count and slice by tokens rather than characters.
  - Chunk parameters (tuned for semantic focus):
    - `CHUNK_SIZE = 300` tokens
    - `CHUNK_OVERLAP = 75` tokens
    - `MIN_CHUNK_SIZE = 50` tokens
  - Section-aware splitting: the code respects `##` headings and tries not to mix unrelated sections in the same chunk.
  - Paragraph-aware and sentence-aware splitting: very long paragraphs are split on sentence boundaries into multiple chunks.
  - Overlap tokens are preserved between adjacent chunks to maintain context continuity across chunk boundaries (helps retrieval quality when the relevant information spans a boundary).
  - Each chunk is classified by `classify_chunk_type()` into semantic types (`definition`, `background`, `plot`, `death`, `summary`, `location`) using heuristics on headings and regex matches; the `is_first_chunk` and `category` signals bias classification for better reranking.
  - Each processed chunk includes:
    - `id` (UUID), `text`, `text_for_embedding` (title + category + section prefix + chunk text), and `metadata` (source, url, category, chunk_type, section, chunk_index, is_first_chunk).

- Why title-prefixed `text_for_embedding` matters
  - Including the `title` + `(category)` + section heading before the chunk supplies strong global context to the embedding model so that short chunks carry the page-level identity.
  - This helps retrieval precision: queries like "Who is X?" will match chunks that contain character definitions even if the chunk itself is short.

- Building embeddings and converting to FAISS vectors (`backend/embeddings/build_index.py`)
  - The build script loads `data/chunks.json` (produced by the processor) and creates an array of texts using `text_for_embedding` when present.
  - Embeddings are produced with `SentenceTransformer('all-MiniLM-L6-v2')` using `model.encode(..., convert_to_numpy=True, normalize_embeddings=True)`.
    - Normalization is important: with normalized vectors, cosine similarity equals inner product, allowing `IndexFlatIP` to be used for cosine nearest neighbors.
  - The script constructs a FAISS index with `faiss.IndexFlatIP(dim)` where `dim` is the embedding dimensionality (384 for the chosen model).
  - `index.add(embeddings)` appends vectors in the same order as the `chunks` array. The code then writes the index file `embeddings/index.faiss` and the metadata `embeddings/metadata.json` (array of chunk dicts) to disk.

- How chunks map to FAISS indices
  - Because the embedding script adds vectors in the same order as the chunk list, FAISS index positions (0..N-1) correspond directly to entries in `metadata.json` by index. This is why the server can safely look up `metadata[idx]` for the index result `idx`.
  - At query time the server does `scores, indices = index.search(query_embedding, k)` and maps each returned `idx` to `metadata[idx]`.

- Query-time retrieval and reranking (`backend/chatbot.py`)
  - Query embedding: the server encodes the user's question with the same `SentenceTransformer` and normalizes the vector.
  - FAISS search: runs `IndexFlatIP.search()` to fetch nearest neighbors (exact inner-product search; fast because it uses optimized BLAS-style operations over a dense matrix).
  - Reranking: candidates are adjusted using metadata signals — e.g., boost if `chunk_type` matches the classified query intent, or if `category` matches an inferred category — improving relevance beyond pure embedding similarity.
  - Context assembly: top-k results are concatenated with source labels and injected into the LLM prompt (RAG).

- Importance of FAISS in this pipeline
  - FAISS provides efficient vector nearest-neighbor search. Key benefits:
    - Speed: optimized for dense linear algebra; exact search (IndexFlatIP) is extremely fast for small-to-moderate collections (thousands–low-hundreds of thousands of vectors) and leverages CPU vectorization.
    - Simplicity: `IndexFlatIP` requires no training or clustering; adding vectors is straightforward and deterministic.
    - Compatibility: works with numpy arrays and integrates cleanly with the sentence-transformers workflow.
  - Limitations & considerations:
    - Memory usage: an IndexFlatIP stores all vectors in RAM (float32) — plan capacity accordingly. For our dataset of **268 chunks**, RAM is negligible (~0.4 MB for raw vectors). For larger corpora consider IVF/HNSW or external ANN services.
    - Cost of exact search scales linearly; approximate indexes trade a small recall drop for large speed/memory gains.

- Concrete numbers (from this repo)
  - Total processed chunks: 268
  - Category distribution: `{'character': 141, 'book': 88, 'place': 24, 'concept': 15}`
  - Chunk-type distribution: `{'definition': 36, 'background': 38, 'plot': 78, 'death': 18, 'summary': 88, 'location': 10}`
  - Embedding dim: 384 (model `all-MiniLM-L6-v2`).
  - Approx raw vector memory: 268 * 384 * 4 ≈ 412,000 bytes (~0.4 MB) plus FAISS overhead and metadata.

## Practical tips to improve retrieval quality

- Tune `CHUNK_SIZE` and `CHUNK_OVERLAP` for your dataset: smaller chunks can increase precision but may lose context; overlap helps continuity.
- Use title/section prefixing (as implemented) to reduce false positives from isolated short fragments.
- Normalize embeddings (already done) and use Inner Product index for cosine similarity.
- Add domain-specific rerank signals (TF-IDF, regex matches, or learned ranker) to improve results where embeddings alone are ambiguous.

---

If you'd like, I can: add latency benchmarks with the current dataset, generate a short slide-ready summary for interview notes, or expand any section with concrete numbers from `embeddings/metadata.json` (e.g., exact vector counts and approximate index size). Which should I do next?

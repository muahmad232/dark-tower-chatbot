import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

# Load embedding model (downloads once)
model = SentenceTransformer("all-MiniLM-L6-v2")

if __name__ == "__main__":
    # Load chunks
    with open("data/chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)

    # Use prefixed text for embeddings (includes title context)
    # Falls back to regular text if text_for_embedding not present
    texts = [
        chunk.get("text_for_embedding", chunk["text"]) 
        for chunk in chunks
    ]

    print(f"🔹 Generating embeddings for {len(texts)} chunks...")
    print(f"   (Using title-prefixed text for better context)")
    
    embeddings = model.encode(
        texts,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    dim = embeddings.shape[1]

    # Create FAISS index (cosine similarity via inner product)
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)

    # Save index
    faiss.write_index(index, "embeddings/index.faiss")

    # Save metadata (for lookup later)
    # Include all chunk info for query-aware retrieval
    with open("embeddings/metadata.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    # Print chunk type distribution
    type_counts = {}
    for chunk in chunks:
        chunk_type = chunk.get("metadata", {}).get("chunk_type", "unknown")
        type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
    
    print(f"\n✅ FAISS index built with {index.ntotal} vectors")
    print(f"\n📊 Indexed chunk types:")
    for ctype, count in type_counts.items():
        print(f"   - {ctype}: {count}")

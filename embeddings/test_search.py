import json
import re
import faiss
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

# Load index & metadata
index = faiss.read_index("embeddings/index.faiss")

with open("embeddings/metadata.json", "r", encoding="utf-8") as f:
    chunks = json.load(f)


def classify_query_intent(query):
    """
    Classify the user's query intent to determine retrieval strategy.
    Returns: tuple of (intent_type, preferred_category)
    
    Intent types: 'definition', 'death', 'background', 'location', 'book_info', 'general'
    Categories: 'character', 'book', 'place', 'object', 'concept', 'event', None
    """
    query_lower = query.lower()
    
    # Detect preferred category from query
    category = None
    if any(word in query_lower for word in ['book', 'novel', 'read', 'written', 'author', 'published']):
        category = 'book'
    elif any(word in query_lower for word in ['place', 'location', 'where is', 'city', 'town', 'land of']):
        category = 'place'
    elif any(word in query_lower for word in ['object', 'weapon', 'artifact', 'item']):
        category = 'object'
    elif any(word in query_lower for word in ['what is ka', 'concept', 'meaning of']):
        category = 'concept'
    
    # Definition-type questions (who/what is)
    definition_patterns = [
        r'^who (is|was|are)\b',
        r'^what (is|was|are)\b',
        r'^describe\b',
        r'^tell me about\b',
        r'^explain\b',
        r'\bwho is\b',
        r'\bwhat is\b',
    ]
    if any(re.search(pattern, query_lower) for pattern in definition_patterns):
        return 'definition', category or 'character'
    
    # Death-related questions
    death_patterns = [
        r'\b(die|died|death|dead|killed|murder)\b',
        r'\bhow did .* die\b',
        r'\blast words\b',
        r'\bfinal moments\b',
    ]
    if any(re.search(pattern, query_lower) for pattern in death_patterns):
        return 'death', category or 'character'
    
    # Background questions
    background_patterns = [
        r'\b(family|parents|born|childhood|origin|history)\b',
        r'\bwhere (is|was) .* from\b',
        r'\brelatives\b',
    ]
    if any(re.search(pattern, query_lower) for pattern in background_patterns):
        return 'background', category or 'character'
    
    # Location questions
    location_patterns = [
        r'\bwhere is\b',
        r'\blocation of\b',
        r'\bfind .* at\b',
    ]
    if any(re.search(pattern, query_lower) for pattern in location_patterns):
        return 'location', 'place'
    
    # Book-specific questions
    book_patterns = [
        r'\bplot of\b',
        r'\bsummary of\b',
        r'\bwhat happens in\b',
        r'\bbook about\b',
    ]
    if any(re.search(pattern, query_lower) for pattern in book_patterns):
        return 'book_info', 'book'
    
    return 'general', category


def search(query, k=5):
    """
    Query-aware search that prioritizes chunks based on query intent and category.
    
    Strategy:
    1. Detect query intent and preferred category
    2. Fetch more candidates than needed (k * 3)
    3. Re-rank based on chunk_type and category matching intent
    4. Return top k results
    """
    intent, preferred_category = classify_query_intent(query)
    
    # Fetch more candidates for re-ranking
    fetch_k = min(k * 4, index.ntotal)
    
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores, indices = index.search(query_embedding, fetch_k)
    
    # Build candidate list with metadata
    candidates = []
    for i, idx in enumerate(indices[0]):
        chunk = chunks[idx]
        metadata = chunk.get("metadata", {})
        chunk_type = metadata.get("chunk_type", "plot")
        category = metadata.get("category", "unknown")
        is_first = metadata.get("is_first_chunk", False)
        
        candidates.append({
            "text": chunk["text"],
            "score": float(scores[0][i]),
            "chunk_type": chunk_type,
            "category": category,
            "is_first_chunk": is_first,
            "source": metadata.get("source", "Unknown"),
            "section": metadata.get("section", ""),
            "url": metadata.get("url", "")
        })
    
    # Re-rank based on intent and category
    reranked = rerank_by_intent(candidates, intent, preferred_category)
    
    return reranked[:k], intent, preferred_category


def rerank_by_intent(candidates, intent, preferred_category):
    """
    Re-rank candidates based on query intent and preferred category.
    Gives bonus scores to chunks matching the intent and category.
    """
    # Intent to preferred chunk types mapping
    intent_preferences = {
        'definition': ['definition', 'background'],
        'death': ['death', 'plot'],
        'background': ['background', 'definition'],
        'location': ['location', 'definition'],
        'book_info': ['summary', 'plot', 'definition'],
        'general': ['plot', 'definition', 'background', 'death']
    }
    
    preferred_types = intent_preferences.get(intent, ['plot'])
    
    for candidate in candidates:
        chunk_type = candidate["chunk_type"]
        category = candidate["category"]
        
        # Base score from embedding similarity
        adjusted_score = candidate["score"]
        
        # Bonus for matching chunk type
        if chunk_type in preferred_types:
            bonus = 0.15 if chunk_type == preferred_types[0] else 0.08
            adjusted_score += bonus
        
        # Bonus for matching category
        if preferred_category and category == preferred_category:
            adjusted_score += 0.12
        
        # Extra bonus for first chunk on definition queries
        if intent == 'definition' and candidate["is_first_chunk"]:
            adjusted_score += 0.1
        
        candidate["adjusted_score"] = adjusted_score
    
    # Sort by adjusted score
    candidates.sort(key=lambda x: x["adjusted_score"], reverse=True)
    
    return candidates


def search_simple(query, k=3):
    """Simple search without re-ranking (for comparison)."""
    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    scores, indices = index.search(query_embedding, k)

    results = []
    for idx in indices[0]:
        results.append(chunks[idx]["text"][:500])

    return results


if __name__ == "__main__":
    # Test queries covering different categories and intents
    test_queries = [
        # Character queries
        ("Who is Roland Deschain?", "character", "definition"),
        ("What are some relatives of Roland Deschain?", "character", "definition"),
        ("How did Eddie Dean die?", "character", "death"),
        
        # Book queries
        ("What is The Gunslinger about?", "book", "book_info"),
        ("Who wrote the Dark Tower series?", "book", "definition"),
        
        # Place queries
        ("What is Mid-World?", "place", "definition"),
        ("Where is Gilead located?", "place", "location"),
        
        # Concept queries
        ("What is Ka?", "concept", "definition"),
        ("What is a ka-tet?", "concept", "definition"),
        
        # Event queries
        ("What happened at the Battle of Jericho Hill?", "event", "general"),
        
        # Object queries
        ("What are the guns of a gunslinger?", "object", "definition"),
    ]
    
    print("=" * 70)
    print("🔍 DARK TOWER CHATBOT - SEARCH TEST SUITE")
    print("=" * 70)
    
    for query, expected_category, expected_intent in test_queries:
        results, intent, category = search(query, k=3)
        
        # Check if intent/category detection worked
        intent_match = "✅" if intent == expected_intent else "⚠️"
        cat_match = "✅" if category == expected_category else "⚠️"
        
        print(f"\n{'─' * 70}")
        print(f"🔍 Query: {query}")
        print(f"📋 Intent: {intent} {intent_match} | Category: {category} {cat_match}")
        print(f"{'─' * 70}")
        
        for i, res in enumerate(results, 1):
            print(f"\n  Result {i} [{res['category']}/{res['chunk_type']}] (score: {res['adjusted_score']:.3f})")
            print(f"  Source: {res['source']}")
            print(f"  {res['text'][:250]}...")
    
    # Summary statistics
    print("\n" + "=" * 70)
    print("📊 INDEX STATISTICS")
    print("=" * 70)
    
    category_counts = {}
    type_counts = {}
    for chunk in chunks:
        cat = chunk.get("metadata", {}).get("category", "unknown")
        ctype = chunk.get("metadata", {}).get("chunk_type", "unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
        type_counts[ctype] = type_counts.get(ctype, 0) + 1
    
    print(f"\nTotal chunks: {len(chunks)}")
    print(f"\nBy category:")
    for cat, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"  - {cat}: {count}")
    print(f"\nBy chunk type:")
    for ctype, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  - {ctype}: {count}")

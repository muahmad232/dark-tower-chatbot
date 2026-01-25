import json
import tiktoken
import uuid
import re

# Tokenizer similar to GPT models
tokenizer = tiktoken.get_encoding("cl100k_base")

# Smaller chunks for better semantic focus
CHUNK_SIZE = 300       # tokens (reduced from 500)
CHUNK_OVERLAP = 75     # tokens (reduced for smaller chunks)
MIN_CHUNK_SIZE = 50    # minimum tokens to keep a chunk


def count_tokens(text):
    return len(tokenizer.encode(text))


def classify_chunk_type(text, section_heading="", is_first_chunk=False, category=""):
    """
    Classify chunk into semantic categories:
    - definition: Character/entity definitions, descriptions, attributes
    - background: Origins, history, relationships, early life
    - plot: Story events, battles, journeys
    - death: Death scenes, endings, final moments
    - summary: Book/media summaries and overviews
    - location: Place descriptions
    """
    text_lower = text.lower()
    heading_lower = section_heading.lower()
    
    # Category-specific defaults for first chunks
    if is_first_chunk:
        if category in ["character", "creature"]:
            if '**' in text or 'is the' in text_lower or 'was the' in text_lower:
                return "definition"
        elif category == "book":
            return "summary"
        elif category == "place":
            return "location"
        elif category == "object":
            return "definition"
        elif category == "concept":
            return "definition"
    
    # Check section heading first for strong signals
    if any(word in heading_lower for word in ['death', 'final', 'end', 'fate']):
        return "death"
    if any(word in heading_lower for word in ['early life', 'childhood', 'background', 'history', 'origin', 'birth']):
        return "background"
    if any(word in heading_lower for word in ['summary', 'plot', 'synopsis', 'overview']):
        return "summary"
    if any(word in heading_lower for word in ['location', 'geography', 'description']):
        return "location"
    if 'character information' in heading_lower or 'infobox' in heading_lower:
        return "definition"
    
    # Death indicators
    death_patterns = [
        r'\bdied\b', r'\bkilled\b', r'\bdeath\b', r'\bmurdered\b',
        r'\bfell to (his|her|their) death\b', r'\blast words\b',
        r'\bburied\b', r'\bgrave\b', r'\bfuneral\b',
        r'\bmortally wound', r'\bcommit.*suicide\b'
    ]
    if any(re.search(pattern, text_lower) for pattern in death_patterns):
        death_count = sum(1 for p in death_patterns if re.search(p, text_lower))
        if death_count >= 2 or 'last words' in text_lower:
            return "death"
    
    # Definition indicators
    definition_patterns = [
        r'^#\s+',
        r'\*\*Alias\*\*', r'\*\*Occupation\*\*', r'\*\*Species\*\*',
        r'\*\*Author\*\*', r'\*\*Published\*\*', r'\*\*Type\*\*',
        r'main protagonist', r'main antagonist', r'archenemy',
        r'is the son of', r'is the daughter of',
        r'\baka\b', r'also known as', r'otherwise known as',
    ]
    if any(re.search(pattern, text, re.IGNORECASE) for pattern in definition_patterns):
        return "definition"
    
    # Background indicators
    background_patterns = [
        r'\bborn to\b', r'\bborn in\b', r'\bearly life\b', r'\bchildhood\b',
        r'\bfamily\b', r'\brelatives\b', r'\bparents\b', r'\bfather\b', r'\bmother\b',
        r'\bbackground\b', r'\bhistory\b', r'\borigin\b',
        r'as a (boy|girl|child|young)', r'\bgrew up\b',
        r'inspired by', r'personality'
    ]
    if any(re.search(pattern, text_lower) for pattern in background_patterns):
        return "background"
    
    # Location indicators (for places)
    if category == "place":
        location_patterns = [
            r'\blocated\b', r'\bfound in\b', r'\bsituated\b',
            r'\bregion\b', r'\bterritory\b', r'\bland of\b'
        ]
        if any(re.search(pattern, text_lower) for pattern in location_patterns):
            return "location"
    
    # Default to plot (narrative events)
    return "plot"


def split_into_paragraphs(text):
    """
    Split text into paragraph-like segments based on natural boundaries.
    Respects section markers (## headings) as boundaries.
    """
    parts = re.split(r'(^##\s+.+$)', text, flags=re.MULTILINE)
    
    paragraphs = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        if part.startswith('##'):
            paragraphs.append(part)
            continue
        
        sub_parts = re.split(r'\n\n+', part)
        for sub in sub_parts:
            sub = sub.strip()
            if sub:
                paragraphs.append(sub)
    
    result = []
    for para in paragraphs:
        tokens = count_tokens(para)
        if tokens > CHUNK_SIZE * 1.5 and not para.startswith('##'):
            sentences = re.split(r'(?<=[.!?])\s+', para)
            result.extend(sentences)
        else:
            result.append(para)
    
    return result


def get_overlap_text(text, overlap_tokens):
    """Get the last N tokens of text as overlap for next chunk."""
    tokens = tokenizer.encode(text)
    if len(tokens) <= overlap_tokens:
        return text
    overlap = tokens[-overlap_tokens:]
    return tokenizer.decode(overlap)


def chunk_text_semantic(text, page_title, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Create semantically-focused chunks with:
    1. Section-aware splitting (respects ## headings)
    2. Paragraph-aware splitting
    3. Overlap for context continuity
    """
    paragraphs = split_into_paragraphs(text)
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    current_section = "Introduction"
    chunk_index = 0
    
    for para in paragraphs:
        if para.startswith('##'):
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                if count_tokens(chunk_text) >= MIN_CHUNK_SIZE:
                    chunks.append({
                        'text': chunk_text,
                        'index': chunk_index,
                        'section': current_section
                    })
                    chunk_index += 1
                current_chunk = []
                current_tokens = 0
            
            current_section = para.replace('##', '').strip()
            continue
        
        para_tokens = count_tokens(para)
        
        if para_tokens > chunk_size:
            if current_chunk:
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'index': chunk_index,
                    'section': current_section
                })
                chunk_index += 1
                overlap_text = get_overlap_text(chunk_text, overlap)
                current_chunk = [overlap_text] if overlap_text else []
                current_tokens = count_tokens(overlap_text) if overlap_text else 0
            
            tokens = tokenizer.encode(para)
            start = 0
            while start < len(tokens):
                end = start + chunk_size
                chunk_tokens = tokens[start:end]
                chunk_text_piece = tokenizer.decode(chunk_tokens)
                
                if count_tokens(chunk_text_piece) >= MIN_CHUNK_SIZE:
                    chunks.append({
                        'text': chunk_text_piece,
                        'index': chunk_index,
                        'section': current_section
                    })
                    chunk_index += 1
                
                start += chunk_size - overlap
        else:
            if current_tokens + para_tokens > chunk_size:
                if current_chunk:
                    chunk_text = ' '.join(current_chunk)
                    if count_tokens(chunk_text) >= MIN_CHUNK_SIZE:
                        chunks.append({
                            'text': chunk_text,
                            'index': chunk_index,
                            'section': current_section
                        })
                        chunk_index += 1
                    
                    overlap_text = get_overlap_text(chunk_text, overlap)
                    current_chunk = [overlap_text] if overlap_text else []
                    current_tokens = count_tokens(overlap_text) if overlap_text else 0
            
            current_chunk.append(para)
            current_tokens += para_tokens
    
    if current_chunk:
        chunk_text = ' '.join(current_chunk)
        if count_tokens(chunk_text) >= MIN_CHUNK_SIZE:
            chunks.append({
                'text': chunk_text,
                'index': chunk_index,
                'section': current_section
            })
    
    return chunks


def process_page(page):
    """
    Process a single page into enriched chunks with:
    - Category awareness
    - Section awareness
    - Title prefix for embedding context
    - Semantic type classification
    - Rich metadata
    """
    text = page["text"]
    title = page["title"]
    url = page["url"]
    category = page.get("category", "unknown")
    sections = page.get("sections", [])
    
    raw_chunks = chunk_text_semantic(text, title)
    
    processed_chunks = []
    for i, chunk_data in enumerate(raw_chunks):
        chunk_text = chunk_data['text'].strip()
        is_first = (chunk_data['index'] == 0)
        section = chunk_data.get('section', 'Introduction')
        
        # Classify chunk type (now with category context)
        chunk_type = classify_chunk_type(
            chunk_text, 
            section_heading=section, 
            is_first_chunk=is_first,
            category=category
        )
        
        # Create title-prefixed text for better embeddings
        # Include category and section for additional context
        if section and section != "Introduction":
            prefixed_text = f"{title} ({category}) - {section}: {chunk_text}"
        else:
            prefixed_text = f"{title} ({category}): {chunk_text}"
        
        processed_chunks.append({
            "id": str(uuid.uuid4()),
            "text": chunk_text,
            "text_for_embedding": prefixed_text,
            "metadata": {
                "source": title,
                "url": url,
                "category": category,
                "chunk_type": chunk_type,
                "section": section,
                "chunk_index": chunk_data['index'],
                "is_first_chunk": is_first
            }
        })
    
    return processed_chunks


if __name__ == "__main__":
    with open("data/raw_pages.json", "r", encoding="utf-8") as f:
        pages = json.load(f)

    all_chunks = []
    type_counts = {"definition": 0, "background": 0, "plot": 0, "death": 0, "summary": 0, "location": 0}
    category_counts = {}

    for page in pages:
        chunks = process_page(page)
        all_chunks.extend(chunks)
        
        # Count chunk types and categories
        for chunk in chunks:
            chunk_type = chunk["metadata"]["chunk_type"]
            category = chunk["metadata"]["category"]
            type_counts[chunk_type] = type_counts.get(chunk_type, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1

    with open("data/chunks.json", "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"✅ Created {len(all_chunks)} chunks from {len(pages)} pages")
    print(f"\n📊 Chunk type distribution:")
    for chunk_type, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        if count > 0:
            print(f"   - {chunk_type}: {count}")
    
    print(f"\n📂 Category distribution:")
    for category, count in sorted(category_counts.items(), key=lambda x: -x[1]):
        print(f"   - {category}: {count}")
    
    # Show sample chunks
    print(f"\n📝 Sample chunks by category:")
    shown_categories = set()
    for chunk in all_chunks:
        cat = chunk["metadata"]["category"]
        if cat not in shown_categories:
            shown_categories.add(cat)
            print(f"\n[{cat.upper()}] {chunk['metadata']['source']} - {chunk['metadata']['section']}")
            print(f"   Type: {chunk['metadata']['chunk_type']}")
            print(f"   {chunk['text'][:120]}...")

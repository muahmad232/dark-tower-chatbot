"""
Dark Tower Chatbot - Groq-powered Q&A with RAG
Uses FAISS index for context retrieval and Groq for response generation.
"""

import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

# Paths
EMBEDDINGS_DIR = "embeddings"
INDEX_PATH = os.path.join(EMBEDDINGS_DIR, "index.faiss")
METADATA_PATH = os.path.join(EMBEDDINGS_DIR, "metadata.json")

# System prompt for the chatbot
SYSTEM_PROMPT = """You are a knowledgeable assistant specializing in Stephen King's Dark Tower series. 
You answer questions ONLY based on the provided context from the Dark Tower wiki.

Guidelines:
- Use ONLY the information provided in the context below
- If the context doesn't contain enough information to answer, say so honestly
- Structure your answers clearly with paragraphs
- Use bullet points for lists when appropriate
- Reference character names, places, and events accurately
- Keep answers informative but concise
- If asked about something not in the context, say "I don't have information about that in my knowledge base."

Remember: You are a Dark Tower expert. Speak with authority but stay faithful to the source material."""


class DarkTowerChatbot:
    def __init__(self):
        print("🗼 Initializing Dark Tower Chatbot...")
        
        # Load embedding model
        print("  Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Load FAISS index
        print("  Loading FAISS index...")
        self.index = faiss.read_index(INDEX_PATH)
        
        # Load metadata
        print("  Loading metadata...")
        with open(METADATA_PATH, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        
        # Initialize Groq client
        print("  Connecting to Groq...")
        self.groq = Groq(api_key=os.getenv("GROQ_API_KEY"))
        self.llm_model = "llama-3.1-8b-instant"  # Fast, free model
        
        print("✅ Chatbot ready!\n")
    
    def classify_query_intent(self, query: str) -> tuple:
        """Classify the intent and category of a query."""
        query_lower = query.lower()
        
        # Intent keywords
        death_keywords = ['die', 'died', 'death', 'kill', 'killed', 'dead', 'dies']
        location_keywords = ['where', 'located', 'location', 'place', 'find']
        definition_keywords = ['who is', 'what is', 'what are', 'define', 'explain', 'tell me about']
        
        # Determine intent
        intent = 'general'
        if any(kw in query_lower for kw in death_keywords):
            intent = 'death'
        elif any(kw in query_lower for kw in location_keywords):
            intent = 'location'
        elif any(kw in query_lower for kw in definition_keywords):
            intent = 'definition'
        
        # Determine category
        category = None
        character_indicators = ['who', 'character', 'person', 'gunslinger', 'roland', 'eddie', 'jake', 'susannah', 'oy']
        place_indicators = ['where', 'place', 'city', 'world', 'location', 'mid-world', 'gilead', 'lud']
        book_indicators = ['book', 'novel', 'story', 'read', 'written', 'series']
        concept_indicators = ['what is ka', 'ka-tet', 'concept', 'meaning', 'high speech']
        
        if any(kw in query_lower for kw in concept_indicators):
            category = 'concept'
        elif any(kw in query_lower for kw in book_indicators):
            category = 'book'
        elif any(kw in query_lower for kw in place_indicators):
            category = 'place'
        elif any(kw in query_lower for kw in character_indicators):
            category = 'character'
        
        return intent, category
    
    def search(self, query: str, top_k: int = 5) -> list:
        """Search for relevant chunks using FAISS."""
        # Get query embedding
        query_embedding = self.embedding_model.encode([query], normalize_embeddings=True)
        
        # Search FAISS index
        scores, indices = self.index.search(query_embedding.astype('float32'), top_k * 2)
        
        # Get intent and category for reranking
        intent, category = self.classify_query_intent(query)
        
        # Collect results with reranking
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.metadata):
                chunk = self.metadata[idx]
                meta = chunk.get('metadata', {})
                
                # Apply reranking boosts
                adjusted_score = float(score)
                
                # Boost matching intent
                if meta.get('chunk_type') == intent:
                    adjusted_score += 0.15
                
                # Boost matching category
                if category and meta.get('category') == category:
                    adjusted_score += 0.1
                
                results.append({
                    'text': chunk['text'],
                    'source': meta.get('source', 'Unknown'),
                    'category': meta.get('category', 'unknown'),
                    'chunk_type': meta.get('chunk_type', 'unknown'),
                    'score': adjusted_score
                })
        
        # Sort by adjusted score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def build_context(self, results: list) -> str:
        """Build context string from search results."""
        context_parts = []
        
        for i, result in enumerate(results, 1):
            source_info = f"[Source: {result['source']} ({result['category']})]"
            context_parts.append(f"{source_info}\n{result['text']}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def ask(self, question: str, show_sources: bool = True) -> str:
        """Ask a question and get a response."""
        # Search for relevant context
        results = self.search(question, top_k=5)
        
        if not results:
            return "I couldn't find any relevant information in my knowledge base."
        
        # Build context
        context = self.build_context(results)
        
        # Build user message
        user_message = f"""CONTEXT FROM DARK TOWER WIKI:
{context}

USER QUESTION: {question}

Please provide a helpful, accurate answer based solely on the context above."""

        # Get response from Groq
        try:
            response = self.groq.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,
                max_tokens=1024
            )
            answer = response.choices[0].message.content
        except Exception as e:
            return f"Error getting response from Groq: {str(e)}"
        
        # Format output
        output = answer
        
        if show_sources:
            sources = list(set(r['source'] for r in results))
            output += f"\n\n📚 **Sources:** {', '.join(sources)}"
        
        return output
    
    def chat(self):
        """Interactive chat loop."""
        print("=" * 60)
        print("🗼 DARK TOWER CHATBOT")
        print("=" * 60)
        print("Ask me anything about the Dark Tower series!")
        print("Type 'quit' or 'exit' to end the conversation.")
        print("Type 'sources off' to hide sources, 'sources on' to show them.")
        print("=" * 60 + "\n")
        
        show_sources = True
        
        while True:
            try:
                question = input("🔮 You: ").strip()
                
                if not question:
                    continue
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("\n👋 Long days and pleasant nights!")
                    break
                
                if question.lower() == 'sources off':
                    show_sources = False
                    print("📚 Sources hidden.\n")
                    continue
                
                if question.lower() == 'sources on':
                    show_sources = True
                    print("📚 Sources will be shown.\n")
                    continue
                
                print("\n🤖 Gunslinger Bot:")
                response = self.ask(question, show_sources=show_sources)
                print(response)
                print()
                
            except KeyboardInterrupt:
                print("\n\n👋 May you have twice the number!")
                break


def main():
    # Check for API key
    if not os.getenv("GROQ_API_KEY") or os.getenv("GROQ_API_KEY") == "your_api_key_here":
        print("❌ Error: Please set your GROQ_API_KEY in the .env file")
        print("   Get your free API key at: https://console.groq.com/keys")
        return
    
    # Initialize and run chatbot
    chatbot = DarkTowerChatbot()
    chatbot.chat()


if __name__ == "__main__":
    main()

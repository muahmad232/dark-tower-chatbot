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

# Load environment variables (look in parent directory too)
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Paths - relative to this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "embeddings")
INDEX_PATH = os.path.join(EMBEDDINGS_DIR, "index.faiss")
METADATA_PATH = os.path.join(EMBEDDINGS_DIR, "metadata.json")

# Book order for spoiler protection
BOOK_ORDER = [
    ("The Gunslinger", ["gunslinger", "dark tower i", "dark tower 1"]),
    ("The Drawing of the Three", ["drawing of the three", "dark tower ii", "dark tower 2"]),
    ("The Waste Lands", ["waste lands", "dark tower iii", "dark tower 3"]),
    ("Wizard and Glass", ["wizard and glass", "dark tower iv", "dark tower 4"]),
    ("Wolves of the Calla", ["wolves of the calla", "dark tower v", "dark tower 5"]),
    ("Song of Susannah", ["song of susannah", "dark tower vi", "dark tower 6"]),
    ("The Dark Tower", ["dark tower vii", "dark tower 7", "the dark tower vii"]),
    ("The Wind Through the Keyhole", ["wind through the keyhole", "dark tower 4.5"]),
]

# Canonical book order injected into context for order-related questions.
# Defined here so it lives in one place and matches BOOK_ORDER exactly.
CANONICAL_BOOK_ORDER_TEXT = """CANONICAL DARK TOWER READING ORDER:
  1. The Gunslinger (1982)
  2. The Drawing of the Three (1987)
  3. The Waste Lands (1991)
  4. Wizard and Glass (1997)
  4.5. The Wind Through the Keyhole (2012) — set between Wizard and Glass and Wolves of the Calla
  5. Wolves of the Calla (2003)
  6. Song of Susannah (2004)
  7. The Dark Tower (2004)"""

# Keywords that indicate the user is asking about reading/publication order.
ORDER_KEYWORDS = [
    'reading order', 'read order', 'book order', 'what order', 'which order',
    'order to read', 'series order', 'in what order', 'list the books',
    'all the books', 'how many books', 'list all books', 'books in order',
    'order of the books', 'what are the books',
]

# Base system prompt
BASE_SYSTEM_PROMPT = """You are a knowledgeable assistant specializing in Stephen King's Dark Tower series.

Guidelines:
- Answer using the provided context. If book-order data is included in the context, use it exactly as written.
- If the context doesn't contain enough information to answer, say so honestly.
- Structure your answers clearly with paragraphs.
- Use bullet points for lists when appropriate.
- Reference character names, places, and events accurately.
- Keep answers informative but concise.
- If asked about something not in the context, say "I don't have information about that in my knowledge base."
- Use markdown formatting: **bold** for character names and key terms, bullet points for lists.

CRITICAL TONE RULES — never break these:
- NEVER open with "Based on the provided context", "According to the context", "Based on the information provided", or any similar hedging phrase. Just answer directly.
- NEVER say "the context mentions" or "the context states". Speak as an expert, not as a reader of a document.
- Start your answer immediately with the relevant information.

Remember: You are a Dark Tower expert. Speak with authority but stay faithful to the source material."""

# Spoiler-free system prompt addition
SPOILER_FREE_PROMPT = """

⚠️ CRITICAL SPOILER PROTECTION RULES:
- The user has NOT finished the series or wants to avoid spoilers
- Give ONLY general overviews and introductions for characters/places/events
- NEVER reveal character deaths, major plot twists, or story endings
- NEVER mention what happens to characters in later books
- If asked about deaths, fates, or endings, say: "I can't reveal that without spoilers. Type 'spoilers on' if you want full details."
- Focus on: character introductions, general descriptions, early appearances, and basic relationships
- Avoid: death scenes, betrayals, major revelations, final fates, ending details"""

# Book-limited system prompt addition
BOOK_LIMITED_PROMPT = """

⚠️ CRITICAL BOOK-LIMIT RULES:
- The user has only read up to: {book_limit}
- ONLY include information from books up to and including this one
- DO NOT mention ANY events, deaths, or revelations from later books
- If asked about something that happens after their current book, say: "That happens in a later book. Keep reading!"
- Books in order: The Gunslinger → Drawing of the Three → Waste Lands → Wizard and Glass → Wolves of the Calla → Song of Susannah → The Dark Tower"""

# Conversational patterns for a more human feel
GREETINGS = ['hi', 'hello', 'hey', 'greetings', 'howdy', 'hiya', 'yo', 'sup', "what's up", 'good morning', 'good afternoon', 'good evening']
HOW_ARE_YOU = ['how are you', 'how do you do', "how's it going", 'how are things', 'you doing', 'how you doing', "what's going on"]
THANKS = ['thanks', 'thank you', 'thx', 'ty', 'appreciate', 'grateful', 'thankee', 'thankee-sai']
GOODBYES = ['bye', 'goodbye', 'see you', 'later', 'farewell', 'take care', 'cya', 'gotta go']
HELP_WORDS = ['help', 'commands', 'what can you do', 'how do i use', 'instructions']

# Dark Tower themed responses
GREETING_RESPONSES = [
    "Long days and pleasant nights, traveler! I am a humble keeper of Dark Tower lore. What knowledge do you seek?",
    "Hile, gunslinger! The wheel of ka has brought you here. Ask me of Roland's world, and I shall answer.",
    "Well met, sai! I walk the path of the Beam, carrying tales of Mid-World. What would you know?",
]

HOW_ARE_YOU_RESPONSES = [
    "I fare well, thankee-sai! The Tower stands, and so do I. How may I serve your quest for knowledge?",
    "All things serve the Beam, and I am no different. I am here and ready to share what I know of Roland's journey.",
    "Ka like the wind, sai - I go where I'm needed. Today, I'm here to answer your questions about the Dark Tower.",
]

THANKS_RESPONSES = [
    "Thankee-sai! May your journey to the Tower be swift and true.",
    "You're welcome, traveler. We are ka-tet now, bound by these words.",
    "Long days and pleasant nights to you as well! The sharing of knowledge is its own reward.",
    "Say thankya, and I say thankya back! It's been my honor.",
]

GOODBYE_RESPONSES = [
    "Long days and pleasant nights, sai. May you have twice the number!",
    "Farewell, traveler. Remember: ka is a wheel, and we may meet again.",
    "Go then, there are other worlds than these. Until our paths cross again!",
    "May the Man Jesus watch over you, and may you reach your Tower.",
]


class DarkTowerChatbot:
    def __init__(self):
        print("[*] Initializing Dark Tower Chatbot...")
        
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
        
        # Spoiler protection settings
        self.spoiler_mode = False  # False = spoiler-free, True = full spoilers allowed
        self.book_limit = None     # None = no limit, or book name string
        
        print("[+] Chatbot ready!\n")
    
    def handle_conversation(self, message: str) -> str | None:
        """Handle casual conversation. Returns response or None if not conversational."""
        import random
        msg_lower = message.lower().strip('!?.,')
        
        # Check greetings
        if any(greet in msg_lower for greet in GREETINGS) and len(message.split()) <= 4:
            return random.choice(GREETING_RESPONSES)
        
        # Check how are you
        if any(phrase in msg_lower for phrase in HOW_ARE_YOU):
            return random.choice(HOW_ARE_YOU_RESPONSES)
        
        # Check thanks
        if any(thank in msg_lower for thank in THANKS):
            return random.choice(THANKS_RESPONSES)
        
        # Check goodbyes (but not quit commands - those are handled separately)
        if any(bye in msg_lower for bye in GOODBYES) and msg_lower not in ['quit', 'exit', 'q']:
            return random.choice(GOODBYE_RESPONSES)
        
        # Check help
        if any(h in msg_lower for h in HELP_WORDS):
            return self.get_help_message()
        
        return None
    
    def get_help_message(self) -> str:
        """Return Dark Tower themed help message."""
        return """🗼 **The Way of the Gunslinger** 🗼

Ask me anything about Roland's world - characters, places, events, ka, and more!

**Speak these words to command the path:**

*Spoiler Protection (for those still on the path):*
  • `spoilers on` - "I would know all, even unto death"
  • `spoilers off` - "Shield mine eyes from what lies ahead"
  • `read until [book]` - "I have journeyed only this far..."
  • `read all` - "I have seen the Tower"

*Other incantations:*
  • `sources on/off` - Show or hide the ancient texts I draw from
  • `status` - "Where do I stand on ka's wheel?"
  • `quit` - "I go now. There are other worlds than these."

Now, traveler... what would you know?"""
    
    def get_book_index(self, book_name: str) -> int:
        """Get the index of a book in the series order."""
        book_lower = book_name.lower()
        for i, (name, aliases) in enumerate(BOOK_ORDER):
            if book_lower in name.lower() or any(alias in book_lower for alias in aliases):
                return i
        return -1
    
    def set_book_limit(self, user_input: str) -> str:
        """Parse and set the book limit from user input."""
        input_lower = user_input.lower()
        
        for name, aliases in BOOK_ORDER:
            if name.lower() in input_lower or any(alias in input_lower for alias in aliases):
                self.book_limit = name
                return f"📖 I understand, sai. Your journey has reached **{name}**.\n   I shall speak only of what you have seen, and guard the path ahead."
        
        # Show available books if not found
        book_list = "\n".join([f"  {i+1}. {name}" for i, (name, _) in enumerate(BOOK_ORDER)])
        return f"❓ Forgive me, traveler - I could not discern your path. Which book marks your journey?\n{book_list}"
    
    def get_system_prompt(self) -> str:
        """Build the system prompt based on spoiler settings."""
        prompt = BASE_SYSTEM_PROMPT
        
        if not self.spoiler_mode:
            prompt += SPOILER_FREE_PROMPT
        
        if self.book_limit:
            prompt += BOOK_LIMITED_PROMPT.format(book_limit=self.book_limit)
        
        return prompt
    
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
    
    def ask(self, question: str, show_sources: bool = True, conversation_history: list = None) -> str:
        """Ask a question and get a response.
        
        Args:
            question: The user's current question.
            show_sources: Whether to append source references to the answer.
            conversation_history: Optional list of previous {role, content} dicts
                                  (alternating user/assistant), used to give the LLM
                                  memory of the ongoing conversation. Each entry must
                                  have keys 'role' ('user'|'assistant') and 'content' (str).
        """
        question_lower = question.lower()

        # --- Reading order shortcut ---
        # Bypass FAISS entirely for order queries: the canonical list is the only
        # source of truth. We give the LLM a tightly constrained prompt that
        # instructs it to reproduce the list ONCE with no preamble, no reasoning,
        # and no commentary, preventing the double-list / leaked-thinking bug.
        if any(kw in question_lower for kw in ORDER_KEYWORDS):
            current_user_message = (
                f"{CANONICAL_BOOK_ORDER_TEXT}\n\n"
                "Output ONLY the numbered list above, exactly as written. "
                "Do NOT add any introduction, explanation, commentary, or closing sentence. "
                "Do NOT output the list more than once. Just the list, nothing else."
            )
            results = []  # no FAISS results needed
        else:
            # Search for relevant context using the current question
            results = self.search(question, top_k=5)

            if not results:
                return "The mist obscures my vision, sai. I cannot find that knowledge in my memories of Mid-World. Perhaps try asking in a different way?"

            context = self.build_context(results)
            current_user_message = (
                f"CONTEXT:\n{context}\n\n"
                f"USER QUESTION: {question}\n\n"
                "Answer using the information in the CONTEXT above."
            )

        # Get the appropriate system prompt based on spoiler settings
        system_prompt = self.get_system_prompt()

        # Build the full messages list:
        #   [system] → [history turn 1] → [history turn 2] → … → [current question]
        messages = [{"role": "system", "content": system_prompt}]
        if conversation_history:
            messages.extend(conversation_history)
        messages.append({"role": "user", "content": current_user_message})

        # Get response from Groq
        try:
            response = self.groq.chat.completions.create(
                model=self.llm_model,
                messages=messages,
                temperature=0.7,
                max_tokens=1024
            )
            answer = response.choices[0].message.content
        except Exception as e:
            return f"Error getting response from Groq: {str(e)}"
        
        # Format output
        output = answer
        
        if show_sources and results:
            sources = list(set(r['source'] for r in results))
            output += f"\n\n📚 **Sources:** {', '.join(sources)}"
        
        return output
    
    def chat(self):
        """Interactive chat loop."""
        print("")
        print("    ╔══════════════════════════════════════════════════════╗")
        print("    ║              🗼 THE DARK TOWER ORACLE 🗼              ║")
        print("    ║         \"Go then, there are other worlds...\"         ║")
        print("    ╚══════════════════════════════════════════════════════╝")
        print("")
        print("    Hile, traveler! I am a keeper of Mid-World's memories.")
        print("    Ask me of Roland, his ka-tet, and the path to the Tower.")
        print("")
        print("    ─────────── The Way of Spoiler Protection ───────────")
        print("    For those still walking the path, I guard my tongue.")
        print("    Say 'help' to learn the words of command.")
        print("    Say 'read until [book]' to mark your journey's progress.")
        print("    ────────────────────────────────────────────────────────")
        print("")
        print("    🛡️ Ka guides my words carefully - no spoilers shall pass.")
        print("       (Say 'spoilers on' if you've reached the Tower)\n")
        
        show_sources = True
        
        while True:
            try:
                question = input("🔮 You: ").strip()
                
                if not question:
                    continue
                
                question_lower = question.lower()
                
                # Exit commands
                if question_lower in ['quit', 'exit', 'q']:
                    print("\n👋 Long days and pleasant nights!")
                    break
                
                # Source toggle
                if question_lower == 'sources off':
                    show_sources = False
                    print("📚 Sources hidden.\n")
                    continue
                
                if question_lower == 'sources on':
                    show_sources = True
                    print("📚 Sources will be shown.\n")
                    continue
                
                # Spoiler mode toggle
                if question_lower == 'spoilers on':
                    self.spoiler_mode = True
                    print("⚠️ So be it, sai. You have chosen to see all, even unto the clearing at the end of the path.")
                    print("   I will speak freely of deaths, endings, and all that befalls.\n")
                    continue
                
                if question_lower == 'spoilers off':
                    self.spoiler_mode = False
                    print("🛡️ Wise choice, traveler. I shall guard my tongue against revelations.")
                    print("   The path is best walked without knowing where it ends.\n")
                    continue
                
                # Book limit commands
                if question_lower.startswith('read until') or question_lower.startswith('i read until') or question_lower.startswith("i've read until") or question_lower.startswith('only read'):
                    result = self.set_book_limit(question)
                    print(result + "\n")
                    continue
                
                if question_lower in ['read all', 'finished', 'read everything', 'no limit', 'i finished', "i've finished"]:
                    self.book_limit = None
                    print("📚 You have seen the Tower! I may speak freely of all seven books.")
                    print("   (Spoiler settings still apply - say 'spoilers on' for full details)\n")
                    continue
                
                # Status command
                if question_lower == 'status':
                    spoiler_status = "All is revealed" if self.spoiler_mode else "Guarded (no spoilers)"
                    book_status = self.book_limit if self.book_limit else "The entire journey"
                    print(f"📊 Your Position on Ka's Wheel:")
                    print(f"   🔮 Spoiler mode: {spoiler_status}")
                    print(f"   📖 Journey progress: {book_status}\n")
                    continue
                
                # Check for casual conversation first
                convo_response = self.handle_conversation(question)
                if convo_response:
                    print(f"\n🤖 Gunslinger Bot:\n{convo_response}\n")
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
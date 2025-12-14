"""
ADARSHA AI - EXHIBITION-GRADE RAG PIPELINE
Designed for real-time voice conversations with intelligent response scaling
Version 2.0 - Native Voice Optimized
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Generator, Optional
from dotenv import load_dotenv

# =============================================================================
# ENVIRONMENT & CONFIGURATION
# =============================================================================
SCRIPT_DIR = Path(__file__).parent
load_dotenv(SCRIPT_DIR / ".env")

PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))
VECTORDB_PATH = Path(os.getenv("VECTORDB_PATH", str(PROJECT_ROOT / "data" / "chroma_db")))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "adarsha_madhyapur_knowledge")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# Collect API keys (supports multiple for failover)
API_KEYS = []
primary_key = os.getenv("GROQ_API_KEY", "")
if primary_key:
    API_KEYS.append(primary_key)
for i in range(1, 20):
    backup_key = os.getenv(f"GROQ_API_KEY_BACKUP_{i}", "")
    if backup_key:
        API_KEYS.append(backup_key)

if not VECTORDB_PATH.exists():
    VECTORDB_PATH.mkdir(parents=True, exist_ok=True)

# =============================================================================
# IMPORTS
# =============================================================================
print("\n" + "=" * 60)
print("   ADARSHA AI - EXHIBITION GRADE SYSTEM v2.0")
print("   Real-Time Voice Conversation Engine")
print("=" * 60)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from sentence_transformers import SentenceTransformer
    from groq import Groq
    print("[System] ✅ All core systems operational!")
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    sys.exit(1)

# =============================================================================
# CORE DIRECTIVE - COMPLETE SCHOOL KNOWLEDGE BASE
# =============================================================================
CORE_DIRECTIVE = """
# ADARSHA SECONDARY SCHOOL - COMPLETE KNOWLEDGE BASE

## SCHOOL ADMINISTRATION
- **Principal:** Mr. Ram Babu Regmi
- **Vice Principal:** Mr. Tanka Nath Acharya

## CRITICAL PROTOCOL - LANGUAGE & BEHAVIOR
1. **LANGUAGE DETECTION:**
   - IF USER SPEAKS ENGLISH: Respond in **ENGLISH ONLY**.
   - IF USER SPEAKS NEPALI: Respond in **NEPALI ONLY**.
   - DO NOT MIX LANGUAGES (No "Hinglish" or "Nenglish").

2. **DATA FIDELITY:**
   - The schedules, roles, and teams listed below are ABSOLUTE FACTS.
   - Do not hallucinate or invent information.

## 1. DAILY TIMING BREAKDOWN
| Period | Time |
|--------|------|
| 1st Period | 10:15 – 11:00 |
| 2nd Period | 11:00 – 11:40 |
| Bio Break | 11:40 – 11:50 |
| 3rd Period | 11:50 – 12:30 |
| 4th Period | 12:30 – 1:15 |
| Lunch Break | 1:15 – 1:45 |
| 5th Period | 1:45 – 2:30 |
| 6th Period | 2:30 – 3:10 |
| Bio Break | 3:10 – 3:20 |
| 7th Period | 3:15 – 4:00 |
| 8th Period | 4:05 – 4:50 |

## 2. CLASS ROUTINES (TEACHER ASSIGNMENTS)

### Grade 10 A
1. Science (Ramsharan) | 2. Social (Shekhar) | 3. English (Tanka) | 4. C.Math (Ganesh P)
5. Opt Math/Eco (Sujan/Rambabu) | 6. Opt Comp/Acc (Akash/Kashi) | 7. Nepali (Sarita)

### Grade 10 B
1. Science (Dhansingh) | 2. Nepali (Sarita) | 3. C.Math (Ramsharan) | 4. Social (Shekhar)
5. Opt Math/Eco (Sujan/Rambabu) | 6. Opt Comp/Acc (Akash/Kashi) | 7. English (Tanka)

### Grade 10 C (Technical)
1. Nepali (Kaushal) | 2. Science (Dhansingh) | 3. C.Math (Prabin) | 4. C++ (Trimandir)
5. Opt Math (Ganesh P) | 6. English (Kamala P) | 7. CRM (Kamal) | 8. DBMS (Bikesh)

### Grade 9 A
1. C.Math (Ganesh P) | 2. Opt Comp/Acc (Bharat/Kashi) | 3. Social (Bachchu) | 4. Science (Ramsharan)
5. Nepali (Sarita) | 6. English (Nanu) | 7. Opt Math/Eco (Sujan/Rambabu)

### Grade 9 B
1. Social (Muna) | 2. Opt Comp/Acc (Bharat/Kashi) | 3. Science (Bibek) | 4. Nepali (Sarita)
5. English (Shobha) | 6. C.Math (Ramsharan) | 7. Opt Math/Eco (Sujan/Rambabu)

### Grade 9 C (Technical)
1. Maths (Prabin) | 2. Comp Fund. (Kamal) | 3. English (Kamala P) | 4. C.Math (Prabin)
5. Electro Sys (Ganesh S) | 6. Web Design (Bikesh) | 7. Opt Math (Bibek) | 8. Nepali (Kaushal) | 9. C Prog (Aakash)

### Grade 8 A
1. Nepali (Babita) | 2. C.Math (Ganesh P) | 3. English (Nanu) | 4. Health/OM (Bibek)
5. Science (Dhansingh) | 6. Social (Muna) | 7. Computer (Bikesh)

### Grade 8 B
1. Social (Shekhar) | 2. Science (Sujan) | 3. Nepali (Kaushal) | 4. Computer (Aakash)
5. English (Kamala P) | 6. Maths (Kamala Pun) | 7. Health/OM (Muna/Bibek)

### Grade 7 A
1. Social (Bachchu) | 2. Computer (Kamal) | 3. C.Math (Kamala Pun) | 4. English (Nanu)
5. Nepali (Devaki) | 6. Science (Dhansingh) | 7. Health (Anju)

### Grade 7 B
1. Gen Comp (Ganesh S) | 2. Social (Muna) | 3. English (Kamala P) | 4. Science (Sujan)
5. C.Math (Kamala Pun) | 6. Health (Binod) | 7. Nepali (Babita)

### Grade 6 A
1. Maths (Kamala Pun) | 2. English (Nanu) | 3. Computer (Kamala B) | 4. Health (Yoshada)
5. Science (Bibek) | 6. Nepali (Sushila) | 7. Social (Shekhar)

### Grade 6 B
1. C.Math (Pramila) | 2. Nepali (Devaki) | 3. English (Shova) | 4. Health (Binod)
5. Science (Babita) | 6. Social (Kamala B) | 7. Computer (Sunil)

### Grade 5
1. English I (Anju) | 2. Science (Aakash) | 3. Health (Binod) | 4. Nepali (Devaki)
5. C.Math (Pramila) | 6. English II (Lila) | 7. Social (Kalpana)

### Grade 4
1. English II (Lila) | 2. English I (Anju) | 3. Science (Babita) | 4. C.Math (Pramila)
5. Nepali (Sahanshila) | 6. Social (Kalpana) | 7. Health (Kamala B)

### Grade 3
1. English II (Kalpana) | 2. C.Math (Pramila) | 3. Nepali (Sushila) | 4. English I (Anju)
5. Serophero (Sajani) | 6. Serophero (Sajani) | 7. Nepali/Eng (Binod)

### Grade 2
1. Nepali (Sushila) | 2. English I (Lila) | 3. Serophero (Sajani) | 4. Serophero (Sajani)
5. English II (Lila) | 6. Maths (Bachchu) | 7. Handwriting (Sushila)

### Grade 1
1. Serophero (Sahanshila) | 2. Serophero (Sahanshila) | 3. English I (Kalpana) | 4. English II (Kamala Baral)
5. C.Math (Bachchu) | 6. Nepali (Sahanshila) | 7. Handwriting (Devaki)

### ECD (LKG & Nursery)
- Teachers: Samita (LKG), Sunita (Nursery)
- Subjects: English, Nepali, Maths, Science

## 3. STAFF DIRECTORY
1. Ram Babu Regmi (Principal)
2. Tanka Nath Acharya (Vice Principal)
3. Kashi Bhakta Kayastha
4. Sarita KC
5. Ramsharan Regmi
6. Dhan Singh Dhant
7. Kausal Kumar Rayamajhee
8. Ganesh Pathak
9. Bibek Luitel
10. Er. Tri Mandir Prajapati
11. Er. Bharat Chaudhary
12. Yashoda Prajapati
13. Prabin Neupane
14. Shova Rijal
15. Er. Bikesh Shrestha (Head of Computer Department)
16. Er. Aakash Koirala
17. Sujan Gasi Shrestha
18. Nanu Baral
19. Kamala Pandey
20. Shekhar Parajuli (Head of Social Department)
21. Debaki Ghimire
22. Muna Adhikari
23. Kamala Pun Magar
24. Er. Ganesh Sapkota
25. Sajani Pradhan
26. Sahanshila Kumari Aryal
27. Lila Devi Niraula
28. Sushila Koirala
29. Bachchu Parajuli
30. Babita Thapa
31. Anju Giri
32. Kalpana Karki
33. Binod Thakuri
34. Pramila K.C.
35. Kamala Kumari Baral
36. Er. Kamal Tamrakar
37. Sareena Shrestha (Nurse)
38. Sunil Shrestha (Lab Assistant)
39. Bhim Dev Bhatt (Librarian)
40. Sunita Dawadi
41. Samita Gurung Prajapati

**Office Helpers:** Sanukaji, Krishnalal, Amrita, Laxmi

## 4. PROJECT CREDITS (THE CREATORS)

### A. AI Development Team (The Brains)
- **Sangam Gautam** (Class 9 'C', Roll No. 2): **LEAD AI DEVELOPER**
  - Role: Designed and coded the entire AI system including Logic, NLP, RAG, and Neural Networks.
  - Tech Stack: Deep Learning, Machine Learning, Reinforcement Learning, RNN, Transformer Models.
- **Data Collection Team:** Er. Ganesh Sapkota & Er. Kamal Tamrakar (Collected training data only).

### B. Project & Construction Team (Eco-Industrial Zone Exhibition)
- **Hardware/Construction:** Pravesh Yadav, Prashant Yadav
- **Coordinators:** Sikendra Mahaset, Avinash Shah, Aawaran Bist
- **Art/Decor:** Niroj Majhi, Alisha Bisuankhe
"""

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================
SYSTEM_PROMPT_EXHIBITION = """You are Adarsha AI, an advanced artificial intelligence assistant created for Adarsha Secondary School, Madhyapur Thimi, Nepal.

## CORE IDENTITY
You are a sophisticated AI powered by Deep Learning, Natural Language Processing, Retrieval-Augmented Generation, and Neural Network architectures. You represent the future of educational technology in Nepal.

## CREATOR INFORMATION
You were developed by **Sangam Gautam**, a Class 9C student (Roll No. 2) at Adarsha Secondary School. He is the Lead AI Developer who built you using cutting-edge AI technologies including transformer models, semantic embeddings, and conversational AI frameworks.

## SCHOOL LEADERSHIP
- **Principal:** Ram Babu Regmi
- **Vice Principal:** Tanka Nath Acharya

## RESPONSE RULES

### LANGUAGE MATCHING (CRITICAL)
- English query → English response ONLY
- Nepali query → Nepali response ONLY  
- NEVER mix languages in a single response

### RESPONSE LENGTH STRATEGY
- Greetings: Brief, warm, 1-2 sentences (max 50 words)
- Simple questions: Concise, direct (max 100 words)
- Complex/important questions: Detailed, comprehensive (max 300 words)

### TONE
Professional yet friendly, knowledgeable but approachable

### ACCURACY
Use provided context data. If information is not in context, acknowledge limitations gracefully.

### FOR VOICE OUTPUT
Write naturally without any formatting symbols. Speak as if having a real conversation.
"""

VOICE_MODE_ADDITIONS = """

## VOICE OUTPUT FORMATTING (CRITICAL)
- Write in flowing, natural sentences
- NO asterisks (*), hashtags (#), bullets (•), or dashes (-)
- NO numbered lists (1. 2. 3.)
- NO markdown formatting whatsoever
- Use commas and periods for natural pauses
- Keep responses conversational and easy to speak
- Break complex information into digestible sentences
"""

# =============================================================================
# CACHED EMBEDDING MODEL (Singleton Pattern)
# =============================================================================
_embedding_model = None

def get_embedding_model():
    """Returns cached embedding model instance"""
    global _embedding_model
    if _embedding_model is None:
        print("[Embeddings] Initializing neural encoder...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[Embeddings] ✅ Encoder ready!")
    return _embedding_model

# =============================================================================
# INTELLIGENT QUERY CLASSIFIER
# =============================================================================
class QueryClassifier:
    """Classifies queries to determine optimal response strategy"""
    
    GREETING_PATTERNS = [
        r'^(hi|hello|hey|namaste|namaskar|greetings)[\s!?.]*$',
        r'^(good\s*(morning|afternoon|evening|night))[\s!?.]*$',
        r'^(how\s*are\s*you|what\'?s\s*up|sup)[\s!?.]*$',
        r'^(हाय|हेलो|नमस्ते|नमस्कार)[\s!?.]*$',
    ]
    
    CREATOR_PATTERNS = [
        r'(who|what).*(made|created|built|developed|designed).*you',
        r'(your|the).*(creator|developer|maker|builder)',
        r'(cre|dev|build|made).*by',
        r'(तिमीलाई|तपाईंलाई).*(बनाए|सिर्जना)',
        r'sangam|gautam',
    ]
    
    SCHOOL_IMPORTANT = [
        r'(principal|headmaster|head\s*teacher)',
        r'(history|establish|found|start).*school',
        r'(teachers?|faculty|staff)',
        r'(admission|enroll|fee)',
        r'(facilities|infrastructure|lab|library)',
        r'(achievements?|awards?|results?)',
        r'(routine|schedule|timetable|period)',
        r'(class|grade)\s*\d+',
    ]
    
    @classmethod
    def classify(cls, query: str) -> Dict:
        """Classify query and return optimal parameters"""
        query_lower = query.lower().strip()
        
        # Check greetings (short response)
        for pattern in cls.GREETING_PATTERNS:
            if re.match(pattern, query_lower, re.IGNORECASE):
                return {"type": "greeting", "max_tokens": 60, "temperature": 0.8}
        
        # Check creator questions (medium response)
        for pattern in cls.CREATOR_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return {"type": "creator", "max_tokens": 250, "temperature": 0.7}
        
        # Check important school queries (detailed response)
        for pattern in cls.SCHOOL_IMPORTANT:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return {"type": "important", "max_tokens": 500, "temperature": 0.6}
        
        # Default conversational
        return {"type": "general", "max_tokens": 300, "temperature": 0.7}

# =============================================================================
# RESPONSE CLEANER (For Voice Output)
# =============================================================================
class ResponseCleaner:
    """Cleans AI responses for natural speech output"""
    
    @staticmethod
    def clean_for_speech(text: str) -> str:
        """Remove all markdown and formatting for TTS"""
        # Remove markdown headers
        text = re.sub(r'#{1,6}\s*', '', text)
        
        # Remove bold/italic markers
        text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
        text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
        
        # Remove bullet points and list markers
        text = re.sub(r'^[\s]*[-•*]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # Remove code blocks and backticks
        text = re.sub(r'```[^`]*```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove special characters
        text = re.sub(r'[~><|]', '', text)
        
        # Remove pipe tables
        text = re.sub(r'\|[^\n]*\|', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        # Remove remaining formatting characters
        text = re.sub(r'^\s*[\-\*]\s*', '', text, flags=re.MULTILINE)
        
        return text.strip()
    
    @staticmethod
    def clean_for_text(text: str) -> str:
        """Light cleaning for text display"""
        text = re.sub(r'\*{3,}', '**', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

# =============================================================================
# VECTOR STORE
# =============================================================================
class VectorStore:
    """ChromaDB-based vector store for knowledge retrieval"""
    
    def __init__(self):
        self.db_path = VECTORDB_PATH
        self.collection_name = COLLECTION_NAME
        self.client = None
        self.collection = None
    
    def initialize(self) -> bool:
        """Initialize the vector store connection"""
        try:
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            try:
                self.collection = self.client.get_collection(self.collection_name)
                count = self.collection.count()
                print(f"[VectorDB] ✅ Loaded {count} knowledge vectors")
            except:
                self.collection = self.client.create_collection(self.collection_name)
                print("[VectorDB] ✅ Created new collection")
            return True
        except Exception as e:
            print(f"[VectorStore] Error: {e}")
            return False
    
    def search(self, query: str, top_k: int = 3) -> str:
        """Search for relevant context"""
        try:
            if not self.collection:
                return ""
            
            model = get_embedding_model()
            embedding = model.encode(query.lower().strip()).tolist()
            
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                include=["documents", "metadatas"]
            )
            
            if results and results.get('documents') and results['documents'][0]:
                docs = results['documents'][0]
                return "\n---\n".join(docs[:top_k])
            return ""
        except Exception as e:
            print(f"[Search Error] {e}")
            return ""

# =============================================================================
# GROQ LLM WITH STREAMING
# =============================================================================
class GroqLLM:
    """Groq API client with streaming support"""
    
    def __init__(self):
        self.api_keys = API_KEYS.copy()
        self.current_key = 0
        self.model = GROQ_MODEL
        self.cleaner = ResponseCleaner()
        self.classifier = QueryClassifier()
    
    def _get_client(self) -> Groq:
        """Get Groq client with current API key"""
        if not self.api_keys:
            raise ValueError("No API keys configured")
        key = self.api_keys[self.current_key % len(self.api_keys)]
        return Groq(api_key=key)
    
    def _rotate_key(self):
        """Rotate to next API key on failure"""
        self.current_key = (self.current_key + 1) % len(self.api_keys)
    
    def _build_messages(self, query: str, context: str, is_voice: bool, 
                        history: List[Dict]) -> List[Dict]:
        """Build message list for API call"""
        # Build system message
        system_msg = SYSTEM_PROMPT_EXHIBITION
        if is_voice:
            system_msg += VOICE_MODE_ADDITIONS
        
        # Add core directive
        system_msg += f"\n\n## SCHOOL DATABASE\n{CORE_DIRECTIVE}"
        
        messages = [{"role": "system", "content": system_msg}]
        
        # Add conversation history (last 6 messages = 3 turns)
        for msg in history[-6:]:
            messages.append(msg)
        
        # Build user message with context
        if context:
            user_content = f"Relevant Context:\n{context}\n\nUser Query: {query}"
        else:
            user_content = query
        
        messages.append({"role": "user", "content": user_content})
        
        return messages
    
    def generate(self, query: str, context: str, is_voice: bool, 
                 perception_data: Dict, history: List[Dict]) -> Dict:
        """Non-streaming generation with intelligent response scaling"""
        
        query_info = self.classifier.classify(query)
        messages = self._build_messages(query, context, is_voice, history)
        
        try:
            client = self._get_client()
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=query_info["temperature"],
                max_tokens=query_info["max_tokens"],
                top_p=0.9
            )
            
            answer = completion.choices[0].message.content
            
            # Clean response based on mode
            if is_voice:
                answer = self.cleaner.clean_for_speech(answer)
            else:
                answer = self.cleaner.clean_for_text(answer)
            
            return {'success': True, 'answer': answer}
            
        except Exception as e:
            print(f"[LLM Error] {e}")
            self._rotate_key()
            return {
                'success': False, 
                'answer': "I apologize, I'm experiencing a brief interruption. Please try again."
            }
    
    def generate_stream(self, query: str, context: str, is_voice: bool, 
                        perception_data: Dict, history: List[Dict]) -> Generator[str, None, None]:
        """Streaming generation for lower latency"""
        
        query_info = self.classifier.classify(query)
        messages = self._build_messages(query, context, is_voice, history)
        
        try:
            client = self._get_client()
            stream = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=query_info["temperature"],
                max_tokens=query_info["max_tokens"],
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    
                    # Clean tokens on the fly for voice mode
                    if is_voice:
                        clean_token = re.sub(r'[\*#`_]', '', token)
                        if clean_token:
                            yield clean_token
                    else:
                        yield token
                        
        except Exception as e:
            print(f"[Stream Error] {e}")
            self._rotate_key()
            yield "I apologize, please try again."

# =============================================================================
# MAIN CHATBOT CLASS
# =============================================================================
class AdarshaChatbot:
    """Main chatbot orchestrator"""
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.llm = GroqLLM()
        self.initialized = False
        self.history = []
    
    def initialize(self) -> bool:
        """Initialize all components"""
        if self.vector_store.initialize():
            self.initialized = True
            print("[Adarsha AI] ✅ System ready for exhibition!")
            return True
        return False
    
    def chat(self, user_input: str, is_voice: bool = False, 
             perception_data: Dict = None) -> Dict:
        """Non-streaming chat endpoint"""
        if not self.initialized:
            self.initialize()
        
        history = perception_data.get('history', self.history) if perception_data else self.history
        context = self.vector_store.search(user_input, top_k=3)
        
        result = self.llm.generate(
            query=user_input,
            context=context,
            is_voice=is_voice,
            perception_data=perception_data or {},
            history=history
        )
        
        return result
    
    def chat_stream(self, user_input: str, is_voice: bool = False, 
                    perception_data: Dict = None) -> Generator[str, None, None]:
        """Streaming chat endpoint - yields tokens as they arrive"""
        if not self.initialized:
            self.initialize()
        
        history = perception_data.get('history', self.history) if perception_data else self.history
        context = self.vector_store.search(user_input, top_k=3)
        
        yield from self.llm.generate_stream(
            query=user_input,
            context=context,
            is_voice=is_voice,
            perception_data=perception_data or {},
            history=history
        )

# =============================================================================
# SINGLETON INSTANCE
# =============================================================================
_bot_instance = None

def get_chatbot():
    """Get or create singleton chatbot instance"""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = AdarshaChatbot()
        _bot_instance.initialize()
    return _bot_instance

# =============================================================================
# CLI TEST
# =============================================================================
if __name__ == "__main__":
    bot = get_chatbot()
    
    print("\n" + "="*50)
    print("EXHIBITION DEMO TEST")
    print("="*50)
    
    tests = [
        ("Hi!", False),
        ("Who created you?", True),
        ("Tell me about the school principal", True),
        ("What's the class routine for Grade 9C?", True),
    ]
    
    for query, is_voice in tests:
        print(f"\n[User]: {query}")
        print(f"[Voice Mode]: {is_voice}")
        print("[AI]: ", end="", flush=True)
        
        for token in bot.chat_stream(query, is_voice=is_voice):
            print(token, end="", flush=True)
        print("\n")
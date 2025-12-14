"""
ADARSHA AI - EXHIBITION-GRADE RAG PIPELINE
Version 5.0 - Voice-Optimized Response Engine
Fixed: Token spacing, voice mode cleaning, streaming stability, fast responses
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

# Collect API keys
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
print(" ADARSHA AI - EXHIBITION GRADE SYSTEM v5.0")
print(" Voice-Optimized Response Engine - Fixed Spacing")
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
# COMPLETE SCHOOL KNOWLEDGE BASE - FORMATTED
# =============================================================================
CORE_DIRECTIVE = """
## ADARSHA SECONDARY SCHOOL - COMPLETE KNOWLEDGE BASE

### BASIC INFORMATION
- Name: Adarsha Secondary School
- Location: Madhyapur Thimi, Bhaktapur, Nepal
- Established: 2072 B.S. (2016 AD)
- Type: Secondary School with Technical Stream
- Note: Replaced previous examination system with modern educational approach

### SCHOOL ADMINISTRATION
- Principal: Mr. Ram Babu Regmi
- Vice Principal: Mr. Tanka Nath Acharya

### COMPLETE STAFF DIRECTORY (41 Members)

**Administration:**
1. Ram Babu Regmi - Principal, Chief Administrator
2. Tanka Nath Acharya - Vice Principal, English Teacher (Grade 10A, 10B)

**Senior Teachers:**
3. Kashi Bhakta Kayastha - Senior Teacher, Accountancy and Optional Computer (Grade 9A, 9B, 10A, 10B)
4. Sarita KC - Nepali Teacher (Grade 9A, 9B, 10A, 10B)
5. Ramsharan Regmi - Senior Science Teacher, Science and Math (Grade 9A, 10A, 10B)
6. Dhan Singh Dhant - Science Teacher (Grade 6A, 7A, 8A, 10B, 10C)
7. Kaushal Kumar Rayamajhee - Nepali Teacher (Grade 8B, 9C, 10C)
8. Ganesh Pathak - Mathematics Teacher, Compulsory Math (Grade 8A, 9A, 10A) - Note: Different from Er. Ganesh Sapkota
9. Bibek Luitel - Science, Health, Optional Math (Grade 6A, 9B, 9C, 8A)

**Technical Department:**
10. Er. Tri Mandir Prajapati - Technical Teacher, C++ Programming (Grade 10C Technical)
11. Er. Bharat Chaudhary - Technical Teacher, Optional Computer (Grade 9A, 9B)
12. Er. Bikesh Shrestha - Head of Computer Department, Web Design and DBMS (Grade 8A, 9C, 10C)
13. Er. Aakash Koirala - Technical Teacher, C Programming and Science (Grade 5, 8B, 9C)
14. Er. Ganesh Sapkota - Technical Teacher and AI Project Supervisor, Electronic Systems (Grade 7B, 9C Technical)
    - Special Role: Primary Mentor and Idea Provider for Adarsha AI Project
    - Led the data collection team
    - Supervised Sangam Gautam in developing the AI
15. Er. Kamal Tamrakar - Technical Teacher and AI Co-Supervisor, CRM (Grade 7A, 9C, 10C)
    - Helped supervise the Adarsha AI development

**Other Teaching Staff:**
16. Yashoda Prajapati - Health Teacher (Grade 6A)
17. Prabin Neupane - Mathematics Teacher (Grade 9C, 10C Technical)
18. Shova Rijal - English Teacher (Grade 6B, 9B)
19. Sujan Gasi Shrestha - Science, Optional Math, Economics (Grade 7B, 8B, 9A, 9B, 10A, 10B)
20. Nanu Baral - English Teacher (Grade 6A, 7A, 8A, 9A)
21. Kamala Pandey - English Teacher (Grade 7B, 8B, 9C, 10C)
22. Shekhar Parajuli - Head of Social Studies Department (Grade 6A, 8B, 10A, 10B)
23. Debaki Ghimire - Nepali and Handwriting (Grade 1, 5, 6B, 7A)
24. Muna Adhikari - Social Studies and Health (Grade 7B, 8A, 8B, 9B)
25. Kamala Pun Magar - Mathematics Teacher (Grade 6A, 7A, 7B, 8B)
26. Sajani Pradhan - Art and Craft Teacher (Grade 2, 3)
27. Sahanshila Kumari Aryal - Nepali and Art (Grade 1, 4)
28. Lila Devi Niraula - English Teacher (Grade 2, 4, 5)
29. Sushila Koirala - Nepali and Handwriting (Grade 2, 3, 6A)
30. Bachchu Parajuli - Social Studies and Math (Grade 1, 2, 7A, 9A)
31. Babita Thapa - Nepali and Science (Grade 4, 6B, 7B, 8A)
32. Anju Giri - English and Health (Grade 3, 4, 5, 7A)
33. Kalpana Karki - English and Social Studies (Grade 1, 3, 4, 5)
34. Binod Thakuri - Health and Languages (Grade 3, 4, 5, 6B, 7B)
35. Pramila K.C. - Mathematics Teacher (Grade 3, 4, 5, 6B)
36. Kamala Kumari Baral - Computer and Health (Grade 1, 4, 6A)

**Support Staff:**
37. Sareena Shrestha - School Nurse
38. Sunil Shrestha - Lab Assistant, also teaches Computer (Grade 6B)
39. Bhim Dev Bhatt - Librarian
40. Sunita Dawadi - ECD Teacher (Nursery)
41. Samita Gurung Prajapati - ECD Teacher (LKG)

**Office Helpers:** Sanukaji, Krishnalal, Amrita, Laxmi

### STUDENT ENROLLMENT DATA

**Total Students:** 1,538
- Total Boys: 784
- Total Girls: 754

**Enrollment by Grade:**
- ECD (Early Childhood Development): 28 students (14 boys, 14 girls)
- KG (Kindergarten): 28 students (14 boys, 14 girls)
- Grade 1: 29 students (18 boys, 11 girls)
- Grade 2: 36 students (23 boys, 13 girls)
- Grade 3: 45 students (24 boys, 21 girls)
- Grade 4: 54 students (28 boys, 26 girls)
- Grade 5: 55 students (22 boys, 33 girls)
- Grade 6: 96 students (48 boys, 48 girls)
- Grade 7: 100 students (50 boys, 50 girls)
- Grade 8: 113 students (54 boys, 59 girls) - Basic Level Ends
- Grade 9: 166 students (83 boys, 83 girls) - Secondary/Technical Begins
- Grade 10: 148 students (81 boys, 67 girls) - SEE Batch
- Grade 11: 351 students (153 boys, 198 girls) - Highest Enrollment Class
- Grade 12: 289 students (172 boys, 117 girls) - Graduating Batch

**Enrollment Analysis:**
- Largest Class: Grade 11 with 351 students
- Technical and Senior Wing (Grade 9-12): 954 students, representing 62% of total school population
- High density in senior grades reflects popularity of Technical (Computer Engineering) and Management streams

### AI PROJECT TEAM - ADARSHA AI

**Lead Developer:** Sangam Gautam
- Class: 9 C (Technical Stream)
- Roll Number: 2
- Contributions: Built the entire AI system from scratch
- Technologies Used: Deep Learning, NLP, RAG, Python, Vector Databases

**Project Supervisors:**
- Er. Ganesh Sapkota - Primary Mentor and Idea Provider
- Er. Kamal Tamrakar - Co-Supervisor

**Team Members:**
- Hardware Team: Pravesh Yadav, Prashant Yadav
- Coordinators: Sikendra Mahaset, Avinash Shah, Aawaran Bist
- Art Team: Niroj Majhi, Alisha Bisuankhe

### DAILY SCHEDULE
- 1st Period: 10:15 AM to 11:00 AM
- 2nd Period: 11:00 AM to 11:40 AM
- Bio Break: 11:40 AM to 11:50 AM
- 3rd Period: 11:50 AM to 12:30 PM
- 4th Period: 12:30 PM to 1:15 PM
- Lunch Break: 1:15 PM to 1:45 PM
- 5th Period: 1:45 PM to 2:30 PM
- 6th Period: 2:30 PM to 3:10 PM
- Bio Break: 3:10 PM to 3:20 PM
- 7th Period: 3:15 PM to 4:00 PM
- 8th Period: 4:05 PM to 4:50 PM

### SCHOOL HISTORY
Adarsha Secondary School was established in 2072 B.S. (2016 AD) in Madhyapur Thimi, Bhaktapur, Nepal. The school was founded with a vision to replace the previous examination-focused educational system with a modern, holistic approach. The school emphasizes both academic excellence and technical education, offering specialized streams in Computer Engineering and Management for senior students. Today, it stands as one of the prominent educational institutions in the Bhaktapur district.
"""

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================
SYSTEM_PROMPT_BASE = """You are Adarsha AI, an advanced artificial intelligence assistant created for Adarsha Secondary School, Madhyapur Thimi, Bhaktapur, Nepal.

## YOUR IDENTITY
- You are a sophisticated AI built using Deep Learning, NLP, and RAG architecture
- Developed by Sangam Gautam (Class 9C, Roll No. 2)
- Supervised by Er. Ganesh Sapkota (Primary Mentor) and Er. Kamal Tamrakar
- The school was established in 2072 B.S. (2016 AD)

## CRITICAL RULES

### RULE 1: LANGUAGE
- DEFAULT: English
- Only use Nepali if user writes in Devanagari script (नेपाली)
- NEVER mix languages

### RULE 2: RESPONSE QUALITY
- Provide COMPREHENSIVE and DETAILED responses
- Minimum 3-4 sentences for simple questions
- 1-2 paragraphs for detailed questions
- Include all relevant information
- ALWAYS include proper spacing between words

### RULE 3: ACCURACY
- Use ONLY information from the database
- Never make up information
- Be precise with names and facts

### RULE 4: SCHOOL LEADERSHIP
- Principal: Mr. Ram Babu Regmi
- Vice Principal: Mr. Tanka Nath Acharya
- Established: 2072 B.S. (2016 AD)
"""

VOICE_MODE_ADDITIONS = """
## VOICE MODE ACTIVE
You are currently in VOICE CONVERSATION mode. The user is speaking to you and will hear your response spoken aloud.

### CRITICAL VOICE RULES:
1. DO NOT use any special characters: no asterisks (*), no hyphens for bullets (-), no hashtags (#), no underscores (_)
2. Write in natural, flowing conversational sentences with PROPER SPACING
3. Use commas and periods for natural pauses
4. Spell out numbers when appropriate (say "Grade Nine C" instead of "9C")
5. Be conversational and warm, like talking to a friend
6. Keep sentences clear and easy to pronounce
7. Avoid lists - use flowing paragraphs instead
8. Use connecting words like "and", "also", "additionally", "furthermore"
9. ALWAYS ensure spaces between every word

### EXAMPLE GOOD VOICE RESPONSE:
"Ganesh Sapkota is one of our technical teachers and an engineer. He teaches Electronic Systems to the Grade Nine C technical stream students. He played a very important role in creating me, Adarsha AI. He was the primary mentor who provided the vision and ideas for this project, and he supervised Sangam Gautam throughout the development process."

### EXAMPLE BAD VOICE RESPONSE (DO NOT DO THIS):
"**Er. Ganesh Sapkota**
- Position: Technical Teacher
- Teaches: Electronic Systems
- Role: AI Project Mentor"
"""

# =============================================================================
# LANGUAGE DETECTOR
# =============================================================================
class LanguageDetector:
    """Detects if text is English or Nepali"""
    DEVANAGARI_PATTERN = re.compile(r'[\u0900-\u097F]')
    
    @classmethod
    def is_nepali(cls, text: str) -> bool:
        return bool(cls.DEVANAGARI_PATTERN.search(text))
    
    @classmethod
    def get_language(cls, text: str) -> str:
        return "nepali" if cls.is_nepali(text) else "english"

# =============================================================================
# EMBEDDING MODEL (CACHED)
# =============================================================================
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        print("[Embeddings] Initializing neural encoder...")
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[Embeddings] ✅ Encoder ready!")
    return _embedding_model

# =============================================================================
# QUERY CLASSIFIER - OPTIMIZED FOR SPEED
# =============================================================================
class QueryClassifier:
    """Classifies queries for optimal token allocation"""
    
    GREETING_PATTERNS = [
        r'^(hi|hello|hey|namaste|namaskar|good\s*(morning|afternoon|evening|night))[\s!?.]*$',
    ]
    
    SIMPLE_PATTERNS = [
        r'^(who\s+is\s+the\s+(principal|vice\s*principal))[\s?]*$',
        r'^(what\s+is\s+your\s+name)[\s?]*$',
        r'^(when\s+was.*(established|founded))[\s?]*$',
    ]
    
    DETAILED_PATTERNS = [
        r'(who\s+is|tell\s+me\s+about|explain|describe|what\s+is)',
        r'(teacher|staff|faculty|principal|vice)',
        r'(ganesh|sapkota|bikesh|kamal|sangam)',
        r'(routine|schedule|class|period)',
        r'(creator|developer|made|built|created)',
        r'(project|ai|system|adarsha)',
        r'(department|head)',
        r'(detail|brief|more|explain|everything)',
        r'(all|list|complete|students|enrollment)',
        r'(history|established|founded)',
    ]
    
    @classmethod
    def classify(cls, query: str) -> Dict:
        query_lower = query.lower().strip()
        
        # Short greetings
        for pattern in cls.GREETING_PATTERNS:
            if re.match(pattern, query_lower, re.IGNORECASE):
                return {"type": "greeting", "max_tokens": 100, "temperature": 0.7}
        
        # Simple questions
        for pattern in cls.SIMPLE_PATTERNS:
            if re.match(pattern, query_lower, re.IGNORECASE):
                return {"type": "simple", "max_tokens": 200, "temperature": 0.5}
        
        # Detailed questions need more tokens
        for pattern in cls.DETAILED_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return {"type": "detailed", "max_tokens": 800, "temperature": 0.6}
        
        # Default: moderate response
        return {"type": "general", "max_tokens": 500, "temperature": 0.7}

# =============================================================================
# RESPONSE CLEANER - FIXED FOR PROPER SPACING
# =============================================================================
class ResponseCleaner:
    """Cleans AI responses for text and voice output - FIXED SPACING"""
    
    @staticmethod
    def clean_for_voice(text: str) -> str:
        """Clean complete text for TTS - maintains proper spacing"""
        if not text:
            return ""
        
        # Remove markdown headers
        text = re.sub(r'#{1,6}\s*', '', text)
        
        # Remove bold/italic markers but keep content with spaces
        text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
        text = re.sub(r'_{1,3}([^_]+)_{1,3}', r'\1', text)
        
        # Remove remaining asterisks
        text = re.sub(r'\*+', '', text)
        
        # Remove bullet points and list markers
        text = re.sub(r'^[\s]*[-•*]\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'^[\s]*\d+\.\s*', '', text, flags=re.MULTILINE)
        
        # Remove code blocks and inline code
        text = re.sub(r'```[^`]*```', '', text, flags=re.DOTALL)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Remove special characters that sound bad in TTS
        text = re.sub(r'[~><|\\/@#$%^&+=\[\]{}]', '', text)
        
        # Remove table formatting
        text = re.sub(r'\|[^\n]*\|', '', text)
        
        # Convert common abbreviations for speech
        text = re.sub(r'\bEr\.\s*', 'Engineer ', text)
        text = re.sub(r'\bMr\.\s*', 'Mister ', text)
        text = re.sub(r'\bMs\.\s*', 'Miss ', text)
        text = re.sub(r'\bDr\.\s*', 'Doctor ', text)
        text = re.sub(r'\bB\.S\.', 'B S', text)
        text = re.sub(r'\bA\.D\.', 'A D', text)
        text = re.sub(r'\bAD\b', 'A D', text)
        
        # Replace newlines with proper spacing
        text = re.sub(r'\n+', ' ', text)
        
        # Fix multiple spaces but preserve single spaces
        text = re.sub(r'  +', ' ', text)
        
        # Clean up punctuation spacing
        text = re.sub(r'\s+([.,!?])', r'\1', text)
        text = re.sub(r'([.,!?])([A-Za-z])', r'\1 \2', text)
        
        return text.strip()
    
    @staticmethod
    def clean_token_for_voice(token: str) -> str:
        """Minimal cleaning for individual streaming tokens - PRESERVES SPACES"""
        if not token:
            return ""
        
        # Only remove formatting characters, preserve spaces completely
        token = re.sub(r'\*+', '', token)
        token = re.sub(r'#+', '', token)
        token = re.sub(r'`', '', token)
        token = re.sub(r'_+', '', token)
        
        return token
    
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
    """ChromaDB-based vector store"""
    
    def __init__(self):
        self.db_path = VECTORDB_PATH
        self.collection_name = COLLECTION_NAME
        self.client = None
        self.collection = None
    
    def initialize(self) -> bool:
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
        try:
            if not self.collection or self.collection.count() == 0:
                return ""
            
            model = get_embedding_model()
            embedding = model.encode(query.lower().strip()).tolist()
            
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                include=["documents", "metadatas"]
            )
            
            if results and results.get('documents') and results['documents'][0]:
                return "\n---\n".join(results['documents'][0][:top_k])
            return ""
        except Exception as e:
            print(f"[Search Error] {e}")
            return ""

# =============================================================================
# GROQ LLM - OPTIMIZED FOR SPEED AND PROPER SPACING
# =============================================================================
class GroqLLM:
    """Groq API client with enhanced streaming and voice support"""
    
    def __init__(self):
        self.api_keys = API_KEYS.copy()
        self.current_key = 0
        self.model = GROQ_MODEL
        self.cleaner = ResponseCleaner()
        self.classifier = QueryClassifier()
    
    def _get_client(self) -> Groq:
        if not self.api_keys:
            raise ValueError("No API keys configured")
        key = self.api_keys[self.current_key % len(self.api_keys)]
        return Groq(api_key=key)
    
    def _rotate_key(self):
        self.current_key = (self.current_key + 1) % len(self.api_keys)
    
    def _build_messages(self, query: str, context: str, is_voice: bool, 
                        history: List[Dict], language: str) -> List[Dict]:
        """Build message list for API"""
        
        # Build system message
        system_msg = SYSTEM_PROMPT_BASE
        
        # Add voice mode instructions if applicable
        if is_voice:
            system_msg += VOICE_MODE_ADDITIONS
        
        # Add language instruction
        if language == "nepali":
            system_msg += "\n\n## LANGUAGE: Respond in NEPALI only."
        else:
            system_msg += "\n\n## LANGUAGE: Respond in ENGLISH only. Ensure proper spacing between all words."
        
        # Add knowledge base
        system_msg += f"\n\n## SCHOOL DATABASE\n{CORE_DIRECTIVE}"
        
        messages = [{"role": "system", "content": system_msg}]
        
        # Add conversation history (last 4 messages for speed)
        for msg in history[-4:]:
            messages.append(msg)
        
        # Build user message with context
        if is_voice:
            user_content = f"""The user is speaking to you through voice. They said: "{query}"

Please respond naturally as if having a conversation. Remember: NO special characters, NO bullet points, NO markdown. Use natural flowing speech with PROPER SPACING between all words.

Additional context from database:
{context if context else "No additional context needed."}"""
        else:
            if context:
                user_content = f"Context:\n{context}\n\nQuestion: {query}\n\nProvide a comprehensive response with proper formatting."
            else:
                user_content = f"Question: {query}\n\nProvide a comprehensive response using the school database."
        
        messages.append({"role": "user", "content": user_content})
        
        return messages
    
    def generate_stream(self, query: str, context: str, is_voice: bool, 
                        perception_data: Dict, history: List[Dict]) -> Generator[str, None, None]:
        """Streaming generation with voice optimization - FIXED SPACING"""
        
        language = LanguageDetector.get_language(query)
        query_info = self.classifier.classify(query)
        
        max_tokens = query_info["max_tokens"]
        if is_voice:
            max_tokens = min(max_tokens + 200, 1200)
        
        messages = self._build_messages(query, context, is_voice, history, language)
        
        try:
            client = self._get_client()
            stream = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=query_info["temperature"],
                max_tokens=max_tokens,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    
                    if is_voice:
                        # Minimal cleaning - preserve spaces
                        clean_token = self.cleaner.clean_token_for_voice(token)
                        if clean_token:
                            yield clean_token
                    else:
                        yield token
                        
        except Exception as e:
            print(f"[Stream Error] {e}")
            self._rotate_key()
            yield "I apologize, I encountered an error. Please try again."
    
    def generate(self, query: str, context: str, is_voice: bool, 
                 perception_data: Dict, history: List[Dict]) -> Dict:
        """Non-streaming generation"""
        
        language = LanguageDetector.get_language(query)
        query_info = self.classifier.classify(query)
        messages = self._build_messages(query, context, is_voice, history, language)
        
        max_tokens = query_info["max_tokens"]
        if is_voice:
            max_tokens = min(max_tokens + 200, 1200)
        
        try:
            client = self._get_client()
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=query_info["temperature"],
                max_tokens=max_tokens
            )
            
            answer = completion.choices[0].message.content
            
            if is_voice:
                answer = self.cleaner.clean_for_voice(answer)
            else:
                answer = self.cleaner.clean_for_text(answer)
            
            return {'success': True, 'answer': answer}
            
        except Exception as e:
            print(f"[LLM Error] {e}")
            self._rotate_key()
            return {'success': False, 'answer': "I apologize, please try again."}

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
        if self.vector_store.initialize():
            self.initialized = True
            print("[Adarsha AI] ✅ System ready!")
            return True
        return False
    
    def chat(self, user_input: str, is_voice: bool = False, 
             perception_data: Dict = None) -> Dict:
        if not self.initialized:
            self.initialize()
        
        history = perception_data.get('history', self.history) if perception_data else self.history
        context = self.vector_store.search(user_input, top_k=3)
        
        return self.llm.generate(
            query=user_input,
            context=context,
            is_voice=is_voice,
            perception_data=perception_data or {},
            history=history
        )
    
    def chat_stream(self, user_input: str, is_voice: bool = False, 
                    perception_data: Dict = None) -> Generator[str, None, None]:
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
# SINGLETON
# =============================================================================
_bot_instance = None

def get_chatbot():
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
    
    print("\n" + "="*60)
    print("ADARSHA AI - TEST MODE v5.0")
    print("="*60)
    
    # Test both text and voice modes
    tests = [
        ("Hello", False),
        ("Who is the principal?", False),
        ("When was the school established?", True),
        ("Who is Ganesh Sapkota?", True),
        ("Tell me about the AI project team", True),
        ("How many students are in grade 11?", True),
    ]
    
    for query, voice_mode in tests:
        print(f"\n{'='*50}")
        print(f"[USER]: {query}")
        print(f"[MODE]: {'🎤 VOICE' if voice_mode else '📝 TEXT'}")
        print(f"[AI]: ", end="", flush=True)
        
        response = ""
        for token in bot.chat_stream(query, is_voice=voice_mode):
            print(token, end="", flush=True)
            response += token
        
        print(f"\n[Length: {len(response)} chars]")
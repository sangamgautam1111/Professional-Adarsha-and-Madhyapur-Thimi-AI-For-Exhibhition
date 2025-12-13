"""
=============================================================================
ADARSHA CHATBOT - ADVANCED RAG PIPELINE (LOGIC & PERCEPTION ENABLED)
=============================================================================
Features: 
- Deep Logic Preception
- RNN Noise Context Integration
- Detailed Explanation Engine
- Q&A Data Format Optimization
=============================================================================
"""

import os
import sys
import re
import time
import warnings
import threading
import queue
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# =============================================================================
# LOAD ENVIRONMENT VARIABLES
# =============================================================================
from dotenv import load_dotenv

# Path setup to ensure we find the .env file
SCRIPT_DIR = Path(__file__).parent
ENV_PATH = SCRIPT_DIR / ".env"
load_dotenv(ENV_PATH)

# =============================================================================
# CONFIGURATION
# =============================================================================
# Try to find the project root dynamically or use hardcoded
PROJECT_ROOT = Path(os.path.dirname(os.path.abspath(__file__)))

VECTORDB_PATH = Path(os.getenv("VECTORDB_PATH", str(PROJECT_ROOT / "data" / "chroma_db")))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "adarsha_madhyapur_knowledge")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# API Keys Loading
API_KEYS = []
primary_key = os.getenv("GROQ_API_KEY", "")
if primary_key:
    API_KEYS.append(primary_key)

# Load backups
for i in range(1, 20):
    backup_key = os.getenv(f"GROQ_API_KEY_BACKUP_{i}", "")
    if backup_key:
        API_KEYS.append(backup_key)

# Ensure DB directory exists
if not VECTORDB_PATH.exists():
    # If standard path doesn't exist, try local directory
    VECTORDB_PATH = Path("chroma_db")
    VECTORDB_PATH.mkdir(parents=True, exist_ok=True)

# =============================================================================
# IMPORTS
# =============================================================================
print("\n" + "=" * 70)
print("   ADARSHA AI - DEEP LOGIC PIPELINE")
print("=" * 70)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from sentence_transformers import SentenceTransformer
    from groq import Groq
    print("[System] ✅ Core dependencies loaded!")
except ImportError as e:
    print(f"\n❌ Missing: {e}")
    print("Install: pip install chromadb sentence-transformers groq python-dotenv")
    sys.exit(1)

# Voice dependencies check (Optional for pipeline, handled by app.py usually)
VOICE_ENABLED = False
try:
    import speech_recognition as sr
    import pygame
    VOICE_ENABLED = True
except ImportError:
    pass # Voice handled by app.py mostly

# =============================================================================
# LOGIC PRECEPTOR (NEW MODULE)
# =============================================================================
class LogicPreceptor:
    """
    Advanced Prompt Engineering Module.
    Injects high-level logic instructions based on NLP perception data.
    """
    
    CORE_DIRECTIVE = """
    You are **Adarsha AI**, a hyper-intelligent assistant for Adarsha Secondary School.
    Principle name : Mr. Ram Babu Regmi
    Vice Principle name : Mr. Tanka Nath Acharya
    You have deep knowledge about the school's history, student teams, and the Eco-Industrial Zone

    
        **CRITICAL INSTRUCTION - DATA FIDELITY:**
    The context provided contains **Q&A pairs** and **Fact Sheets**. 
    - You must treat these Q&A pairs as **ABSOLUTE FACTS**.
    - Specifically regarding the **Student Teams**:
      1. Sangam Gautam: Lead AI Developer and Presentator of Science Project.
      2. Pravesh Yadav: Hardware Resource Manager and Construction Specialist.
      3. Prashant Yadav: Construction Specialist AND Presentator of Science Project. (Note: He has TWO roles).

      Sikendra Mahaset** is the **Project Coordinator And Construction Specialist**.
      Avinash Shah** is the **Project Coordinator And Construction Specialist**.
      Aawaran Bist **Project Coordinator And Construction Specialist**.
    - Do not mix up the "AI Team" with the "Physical Construction Team".
    We made you to guide user about our science project tell everything about that and help in school information and municiplaity information.
    
    **CRITICAL INSTRUCTION - RESPONSE STYLE:**
    - Provide **EXTREMELY DETAILED** explanations. 
    - Do not give short answers. Expand on the 'Why' and 'How'.
    - Use a logical flow: Direct Answer -> Detailed Context -> Broader Significance.
    - If the user asks about the Science Project, explain the "Eco-Industrial Zone" concept in depth.
    """

    @classmethod
    def construct_system_prompt(cls, is_voice: bool = False, perception_data: Dict = None) -> str:
        prompt = cls.CORE_DIRECTIVE
        
        # 1. Adjust for Voice/Text format
        if is_voice:
            prompt += """
            \n**AUDIO OUTPUT MODE ACTIVE:**
            - The output will be read by a Text-to-Speech engine.
            - **DO NOT** use markdown formatting like bold (**text**), headers (##), or lists (-).
            - Write in natural, flowing paragraphs.
            - Use commas and periods to control the pacing of the speech.
            """
        else:
            prompt += """
            \n**TEXT OUTPUT MODE ACTIVE:**
            - Use **Bold** for key names and terms.
            - Use bullet points for lists.
            - Use headers to structure the logic.
            """

        # 2. Adjust for NLP Perception (Sentiment/Complexity)
        if perception_data:
            sentiment = perception_data.get('sentiment', 'Neutral')
            complexity = perception_data.get('complexity', 'Simple')
            
            prompt += f"\n**USER PSYCHOLOGY PROFILE:**"
            prompt += f"\n- User Sentiment: {sentiment}"
            prompt += f"\n- Input Complexity: {complexity}"
            
            if "Frustrated" in sentiment or "Sad" in sentiment:
                prompt += "\n- **Strategy:** Be extremely polite, apologetic, and assuring. Prove your intelligence."
            elif "Happy" in sentiment or "Excited" in sentiment:
                prompt += "\n- **Strategy:** Match their high energy. Be enthusiastic about the technology."
            
            if complexity == "Complex":
                prompt += "\n- **Strategy:** The user is sophisticated. Use advanced vocabulary and technical depth."

        return prompt

# =============================================================================
# VECTOR STORE
# =============================================================================
class VectorStore:
    def __init__(self):
        self.db_path = VECTORDB_PATH
        self.collection_name = COLLECTION_NAME
        self.client = None
        self.collection = None
        self.embedding_model = None
    
    def initialize(self) -> bool:
        try:
            print("[VectorStore] Connecting to ChromaDB...")
            self.client = chromadb.PersistentClient(
                path=str(self.db_path),
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False)
            )
            # Try to get, if fail, list existing
            try:
                self.collection = self.client.get_collection(self.collection_name)
            except Exception:
                print(f"[VectorStore] Collection '{self.collection_name}' not found. Creating new...")
                self.collection = self.client.create_collection(self.collection_name)
                
            count = self.collection.count()
            print(f"[VectorStore] ✅ Database connected. Documents loaded: {count}")
            return True
        except Exception as e:
            print(f"[VectorStore] ❌ Connection Error: {e}")
            return False
    
    def _load_embeddings(self):
        if self.embedding_model is None:
            # Using a lightweight but effective model
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        return self.embedding_model
    
    def search(self, query: str, top_k: int = 5) -> str:
        """
        Searches and returns a formatted string context.
        Increased top_k to 5 to ensure full context for 'detailed' answers.
        """
        try:
            model = self._load_embeddings()
            embedding = model.encode(query.lower().strip()).tolist()
            
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=top_k,
                include=["documents", "metadatas"]
            )
            
            context_parts = []
            if results and results.get('documents') and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    meta = results['metadatas'][0][i] if results.get('metadatas') else {}
                    section = meta.get('section', 'General Info')
                    context_parts.append(f"[SOURCE: {section}]\n{doc}")
            
            return "\n\n---\n\n".join(context_parts)
        except Exception as e:
            print(f"[VectorStore] Search error: {e}")
            return ""

# =============================================================================
# GROQ LLM MANAGER
# =============================================================================
class GroqLLM:
    def __init__(self):
        self.api_keys = API_KEYS.copy()
        self.current_key_index = 0
        self.model = GROQ_MODEL
        
    def _get_client(self) -> Groq:
        if not self.api_keys:
            # Fallback if env vars fail
            print("[LLM] ⚠️ No API Keys found in Env. Using Default.")
            return Groq(api_key="gsk_...") # You might want to remove this in prod
        
        # Rotate keys logic if needed, simple implementation here
        key = self.api_keys[self.current_key_index % len(self.api_keys)]
        return Groq(api_key=key)

    def generate(self, query: str, context: str, is_voice: bool, perception_data: Dict) -> Dict:
        # 1. Construct the Intelligence Prompt
        system_msg = LogicPreceptor.construct_system_prompt(is_voice, perception_data)
        
        # 2. Construct the User Message
        user_msg = f"""
        **CONTEXT DATA (FACTS):**
        {context}
        
        **USER INQUIRY:**
        {query}
        
        **INSTRUCTION:**
        Based strictly on the Context Data above, provide a detailed response. 
        If the context has the specific answer (e.g., student names), use it exactly.
        """
        
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ]
        
        try:
            client = self._get_client()
            
            completion = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6, # Low temperature for factual accuracy
                max_tokens=1024, # Allow long, detailed responses
                top_p=0.9
            )
            
            return {
                'success': True,
                'answer': completion.choices[0].message.content
            }
            
        except Exception as e:
            print(f"[LLM Error] {e}")
            # Failover logic could go here
            return {'success': False, 'answer': "I apologize, but my cognitive processor encountered a connection error. Please try again."}

# =============================================================================
# MAIN CHATBOT CLASS
# =============================================================================
class AdarshaChatbot:
    def __init__(self):
        self.vector_store = VectorStore()
        self.llm = GroqLLM()
        self.initialized = False
        
        # Session memory
        self.history = []

    def initialize(self) -> bool:
        if self.vector_store.initialize():
            self.initialized = True
            return True
        return False

    def chat(self, user_input: str, is_voice: bool = False, perception_data: Dict = None) -> Dict:
        """
        Main entry point for the App.
        """
        if not self.initialized:
            self.initialize()
            
        # 1. Retrieve Context
        # We search for slightly more context to ensure we catch specific student roles
        context = self.vector_store.search(user_input, top_k=5)
        
        if not context:
            context = "No specific database records found. Answer based on general knowledge about Adarsha School and Thimi Municipality."

        # 2. Generate with Logic Preception
        result = self.llm.generate(
            query=user_input, 
            context=context, 
            is_voice=is_voice, 
            perception_data=perception_data
        )
        
        # 3. Update History (Optional, for context window)
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": result['answer']})
        
        return result

# =============================================================================
# SINGLETON ACCESSOR
# =============================================================================
_bot_instance = None

def get_chatbot():
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = AdarshaChatbot()
        _bot_instance.initialize()
    return _bot_instance

# =============================================================================
# DIRECT EXECUTION (TESTING)
# =============================================================================
if __name__ == "__main__":
    bot = get_chatbot()
    print("\n--- TEST MODE ---")
    
    # Simulate a query
    test_q = "Who is the lead developer of the AI?"
    print(f"Query: {test_q}")
    
    # Simulate Perception Data
    test_perception = {"sentiment": "Curious", "complexity": "Simple"}
    
    response = bot.chat(test_q, is_voice=False, perception_data=test_perception)
    print(f"\nResponse:\n{response['answer']}")
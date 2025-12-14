import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# ==========================================
# DIAGNOSTIC TOOL FOR ADARSHA AI
# ==========================================

print("\n" + "="*60)
print(" 🩺 ADARSHA AI SYSTEM DIAGNOSTIC TOOL")
print("="*60 + "\n")

# 1. DEFINE PATHS
current_dir = Path(__file__).parent.absolute()
env_path = current_dir / ".env"
data_db_path = current_dir / "data" / "chroma_db"
root_db_path = current_dir / "chroma_db"

print(f"📂 Scanning Directory: {current_dir}")

# 2. CHECK DEPENDENCIES
print("\n[1/5] Checking Dependencies...")
try:
    import groq
    print("   ✅ Groq Library installed.")
except ImportError:
    print("   ❌ ERROR: 'groq' library missing. Run: pip install groq")

try:
    import chromadb
    print("   ✅ ChromaDB Library installed.")
except ImportError:
    print("   ❌ ERROR: 'chromadb' library missing. Run: pip install chromadb")

# 3. CHECK .ENV FILE
print("\n[2/5] Checking Environment Variables...")
if env_path.exists():
    print(f"   ✅ .env file found at: {env_path.name}")
    load_dotenv(env_path)
    
    api_key = os.getenv("GROQ_API_KEY")
    if api_key and api_key.startswith("gsk_"):
        print("   ✅ GROQ_API_KEY found and looks valid (starts with gsk_).")
    else:
        print("   ❌ ERROR: GROQ_API_KEY is missing or invalid in .env file!")
else:
    print("   ❌ ERROR: .env file NOT found! Create one in the backend folder.")

# 4. CHECK DATABASE PATHS
print("\n[3/5] Checking Vector Database...")

real_db_found = False
target_db_path = None

# Check the 'data/chroma_db' location (Likely the correct one)
if data_db_path.exists() and (data_db_path / "chroma.sqlite3").exists():
    print(f"   ✅ Valid Database found at: backend/data/chroma_db")
    real_db_found = True
    target_db_path = data_db_path
else:
    print(f"   ⚠️  No database at: backend/data/chroma_db")

# Check the 'chroma_db' location (Likely the empty one)
if root_db_path.exists():
    if (root_db_path / "chroma.sqlite3").exists():
        print(f"   ⚠️  Another Database found at: backend/chroma_db")
        if not real_db_found:
            target_db_path = root_db_path
            real_db_found = True
    else:
        print(f"   ℹ️  Empty/Invalid folder found at: backend/chroma_db (Safe to ignore if the other one works)")

if not real_db_found:
    print("   ❌ CRITICAL ERROR: Could not find 'chroma.sqlite3' in any expected folder!")
    print("      Make sure you have run 'create_vector_db.py' first.")

# 5. TEST GROQ CONNECTION
print("\n[4/5] Testing Groq API Connection...")
if os.getenv("GROQ_API_KEY"):
    try:
        client = groq.Groq(api_key=os.getenv("GROQ_API_KEY"))
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": "Say 'Test Successful'"}],
            model="llama-3.1-8b-instant",
        )
        print(f"   ✅ Groq API Response: {chat_completion.choices[0].message.content}")
    except Exception as e:
        print(f"   ❌ Groq API Failed: {e}")
else:
    print("   ⏭️  Skipping API test (No Key found).")

# 6. TEST DATABASE SEARCH
print("\n[5/5] Testing Knowledge Retrieval...")
if real_db_found and target_db_path:
    try:
        client = chromadb.PersistentClient(path=str(target_db_path))
        # Try to guess collection name or list them
        collections = client.list_collections()
        if collections:
            col_name = collections[0].name
            print(f"   ✅ Collection found: '{col_name}'")
            collection = client.get_collection(col_name)
            count = collection.count()
            print(f"   ✅ Document Count: {count}")
            
            # Simple query
            results = collection.query(query_texts=["Adarsha School"], n_results=1)
            if results['documents'][0]:
                print(f"   ✅ Retrieval Test: Successfully read data.")
            else:
                print(f"   ⚠️  Retrieval Test: Database is empty.")
        else:
            print("   ❌ Database exists but contains NO collections.")
    except Exception as e:
        print(f"   ❌ Database Error: {e}")
else:
    print("   ⏭️  Skipping Database test.")

print("\n" + "="*60)
print(" DIAGNOSTIC COMPLETE")
print("="*60 + "\n")
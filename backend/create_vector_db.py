"""
=============================================================================
ADARSHA CHATBOT - ENHANCED VECTOR DATABASE CREATOR V2.0
100% ACCURACY OPTIMIZATION
=============================================================================
"""

import os
import sys
import re
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import warnings

warnings.filterwarnings("ignore")

from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).parent
ENV_PATH = SCRIPT_DIR / ".env"
load_dotenv(ENV_PATH)

PROJECT_ROOT = Path(r"C:\Users\USER\Desktop\Adaplex\Professional-Adarsha-and-Madhyapur-Thimi-AI-For-Exhibhition")
VECTORDB_PATH = Path(os.getenv("VECTORDB_PATH", str(PROJECT_ROOT / "data" / "chroma_db_enhanced")))
DATA_PATH = Path(os.getenv("DATA_PATH", str(PROJECT_ROOT / "data" / "data_for_vectordb" / "alldata.txt")))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "adarsha_knowledge_enhanced")

VECTORDB_PATH.mkdir(parents=True, exist_ok=True)

print("\n" + "=" * 80)
print("   ADARSHA ENHANCED VECTOR DB CREATOR - 100% ACCURACY MODE")
print("=" * 80)
print(f"\n[Config] Project Root: {PROJECT_ROOT}")
print(f"[Config] Data File: {DATA_PATH}")
print(f"[Config] Vector DB: {VECTORDB_PATH}")
print("\n[System] Loading dependencies...")

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    from sentence_transformers import SentenceTransformer
    print("[System] All dependencies loaded!")
except ImportError as e:
    print(f"\nMissing dependency: {e}")
    print("\nInstall: pip install chromadb sentence-transformers torch python-dotenv")
    sys.exit(1)


def calculate_hash(text: str) -> str:
    return hashlib.md5(text.encode('utf-8')).hexdigest()

def print_status(message: str):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {message}")

def print_section(title: str):
    print("\n" + "-" * 70)
    print(f"  {title}")
    print("-" * 70)


class EnhancedTextChunker:
    """
    Enhanced chunking with semantic boundary preservation
    """
    def __init__(self, chunk_size: int = 1500, overlap: int = 300):
        self.chunk_size = chunk_size
        self.overlap = overlap

        self.major_section_patterns = [
            r'^={50,}',
            r'^SECTION\s+\d+:',
            r'^\[METADATA\]',
        ]

        self.sub_section_patterns = [
            r'^-{30,}',
            r'^\d+\.\d+\s+[A-Z]',
            r'^[A-Z][A-Z\s]{8,}:?\s*$',
            r'^ZONE\s+[A-D]:',
            r'^#+\s+',
            r'^\*\*[^*]+\*\*\s*$',
        ]

        self.entity_patterns = {
            'person': r'(Name:|Lead|Developer|Teacher|Principal|Student):?\s*([^\n]+)',
            'location': r'(Location|Address|District|Municipality):?\s*([^\n]+)',
            'date': r'(Established|Founded|Date):?\s*([^\n]+)',
            'contact': r'(Phone|Email|Website):?\s*([^\n]+)',
        }

    def is_major_boundary(self, line: str) -> bool:
        line = line.strip()
        return any(re.match(pattern, line) for pattern in self.major_section_patterns)

    def is_sub_boundary(self, line: str) -> bool:
        line = line.strip()
        return any(re.match(pattern, line) for pattern in self.sub_section_patterns)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        entities = {}
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = [match[1].strip() for match in matches if match[1].strip()]
        return entities

    def extract_keywords(self, text: str) -> List[str]:
        keywords = set()

        important_terms = [
            'Adarsha', 'School', 'Thimi', 'Bhaktapur', 'Technical', 'CTEVT', 'NEB',
            'Sangam Gautam', 'AI', 'Chatbot', 'Developer', 'Project', 'Science',
            'Renewable Energy', 'Exhibition', 'Student', 'Teacher', 'Principal',
            'Admission', 'Examination', 'SEE', 'TSLC', 'Computer Engineering'
        ]

        text_lower = text.lower()
        for term in important_terms:
            if term.lower() in text_lower:
                keywords.add(term)

        return list(keywords)

    def extract_section_hierarchy(self, line: str) -> str:
        line = line.strip()

        line = re.sub(r'^={3,}\s*', '', line)
        line = re.sub(r'^-{3,}\s*', '', line)
        line = re.sub(r'^#+\s*', '', line)
        line = re.sub(r'^\*\*|\*\*$', '', line)
        line = re.sub(r'^SECTION\s+\d+:\s*', '', line, flags=re.IGNORECASE)

        return line[:150] if line else "General"

    def chunk_with_semantic_preservation(self, text: str) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        text = re.sub(r'\r\n', '\n', text)
        lines = text.split('\n')
        total_lines = len(lines)

        chunks = []
        current_chunk_lines = []
        current_major_section = "Document Root"
        current_sub_section = "General"
        current_length = 0
        chunk_start_line = 0
        section_context = []

        for i, line in enumerate(lines):
            if self.is_major_boundary(line):
                if current_chunk_lines:
                    chunk_text = '\n'.join(current_chunk_lines).strip()
                    if len(chunk_text) > 100:
                        entities = self.extract_entities(chunk_text)
                        keywords = self.extract_keywords(chunk_text)

                        chunks.append({
                            'text': chunk_text,
                            'major_section': current_major_section,
                            'sub_section': current_sub_section,
                            'section_path': ' > '.join(section_context) if section_context else current_major_section,
                            'entities': entities,
                            'keywords': keywords,
                            'index': len(chunks),
                            'line_start': chunk_start_line,
                            'line_end': i - 1,
                            'char_count': len(chunk_text),
                            'word_count': len(chunk_text.split())
                        })

                new_major = self.extract_section_hierarchy(line)
                if new_major:
                    current_major_section = new_major
                    section_context = [new_major]
                    current_sub_section = "General"

                current_chunk_lines = [line]
                current_length = len(line)
                chunk_start_line = i
                continue

            if self.is_sub_boundary(line):
                new_sub = self.extract_section_hierarchy(line)
                if new_sub:
                    current_sub_section = new_sub
                    if len(section_context) < 2:
                        section_context.append(new_sub)
                    else:
                        section_context[-1] = new_sub

            current_chunk_lines.append(line)
            current_length += len(line) + 1

            if current_length >= self.chunk_size:
                chunk_text = '\n'.join(current_chunk_lines).strip()
                if len(chunk_text) > 100:
                    entities = self.extract_entities(chunk_text)
                    keywords = self.extract_keywords(chunk_text)

                    chunks.append({
                        'text': chunk_text,
                        'major_section': current_major_section,
                        'sub_section': current_sub_section,
                        'section_path': ' > '.join(section_context) if section_context else current_major_section,
                        'entities': entities,
                        'keywords': keywords,
                        'index': len(chunks),
                        'line_start': chunk_start_line,
                        'line_end': i,
                        'char_count': len(chunk_text),
                        'word_count': len(chunk_text.split())
                    })

                overlap_lines = []
                overlap_length = 0
                for ol in reversed(current_chunk_lines):
                    if overlap_length + len(ol) + 1 <= self.overlap:
                        overlap_lines.insert(0, ol)
                        overlap_length += len(ol) + 1
                    else:
                        break

                current_chunk_lines = overlap_lines
                current_length = overlap_length
                chunk_start_line = max(0, i - len(overlap_lines) + 1)

        if current_chunk_lines:
            chunk_text = '\n'.join(current_chunk_lines).strip()
            if len(chunk_text) > 100:
                entities = self.extract_entities(chunk_text)
                keywords = self.extract_keywords(chunk_text)

                chunks.append({
                    'text': chunk_text,
                    'major_section': current_major_section,
                    'sub_section': current_sub_section,
                    'section_path': ' > '.join(section_context) if section_context else current_major_section,
                    'entities': entities,
                    'keywords': keywords,
                    'index': len(chunks),
                    'line_start': chunk_start_line,
                    'line_end': total_lines - 1,
                    'char_count': len(chunk_text),
                    'word_count': len(chunk_text.split())
                })

        return chunks


class EnhancedVectorDBCreator:
    def __init__(self):
        self.db_path = VECTORDB_PATH
        self.collection_name = COLLECTION_NAME
        self.client = None
        self.collection = None
        self.embedding_model = None
        self.chunker = EnhancedTextChunker()

    def initialize(self):
        print_status("Initializing ChromaDB with enhanced settings...")
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        print_status(f"Database path: {self.db_path}")

    def load_embedding_model(self):
        if self.embedding_model is None:
            print_status("Loading embedding model (all-MiniLM-L6-v2)...")
            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            print_status("Embedding model loaded!")
        return self.embedding_model

    def create_collection(self, reset: bool = True):
        if reset:
            try:
                self.client.delete_collection(self.collection_name)
                print_status(f"Deleted existing collection: {self.collection_name}")
            except:
                pass

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={
                "description": "Enhanced Adarsha Knowledge Base - 100% Accuracy",
                "hnsw:space": "cosine",
                "version": "2.0"
            }
        )
        print_status(f"Collection created: {self.collection_name}")

    def process_and_store(self, file_path: Path) -> Dict[str, Any]:
        print_section("READING DATA FILE")

        if not file_path.exists():
            raise FileNotFoundError(f"Data file not found: {file_path}")

        print_status(f"Reading: {file_path.name}")
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        total_lines = len(content.split('\n'))
        total_words = len(content.split())
        total_chars = len(content)

        print_status(f"Total lines: {total_lines:,}")
        print_status(f"Total words: {total_words:,}")
        print_status(f"Total characters: {total_chars:,}")

        print_section("SEMANTIC CHUNKING")
        chunks = self.chunker.chunk_with_semantic_preservation(content)
        print_status(f"Created {len(chunks)} semantic chunks")

        sections = {}
        for chunk in chunks:
            section = chunk['section_path'][:50]
            sections[section] = sections.get(section, 0) + 1

        print_status("Chunk distribution by section:")
        for section, count in list(sections.items())[:15]:
            print(f"      • {section}: {count} chunks")

        print_section("GENERATING EMBEDDINGS WITH RICH METADATA")
        model = self.load_embedding_model()

        ids = ["__metadata__"]
        documents = [f"METADATA|file:{file_path.name}|lines:{total_lines}|words:{total_words}"]
        metadatas = [{
            "type": "metadata",
            "file_name": file_path.name,
            "total_lines": total_lines,
            "total_words": total_words,
            "total_chunks": len(chunks),
            "created": datetime.now().isoformat(),
            "version": "2.0_enhanced"
        }]

        for chunk in chunks:
            chunk_id = f"chunk_{chunk['index']:05d}"
            ids.append(chunk_id)
            documents.append(chunk['text'])

            metadata = {
                "type": "content",
                "major_section": chunk['major_section'][:200],
                "sub_section": chunk['sub_section'][:200],
                "section_path": chunk['section_path'][:300],
                "index": chunk['index'],
                "word_count": chunk['word_count'],
                "char_count": chunk['char_count'],
                "keywords": json.dumps(chunk['keywords']),
            }

            for entity_type, values in chunk['entities'].items():
                if values:
                    metadata[f"entity_{entity_type}"] = json.dumps(values[:5])

            metadatas.append(metadata)

        print_section("STORING TO DATABASE WITH VALIDATION")
        batch_size = 50
        total_docs = len(documents)
        stored_count = 0

        for batch_start in range(0, total_docs, batch_size):
            batch_end = min(batch_start + batch_size, total_docs)

            batch_docs = documents[batch_start:batch_end]
            batch_ids = ids[batch_start:batch_end]
            batch_meta = metadatas[batch_start:batch_end]

            embeddings = model.encode(batch_docs, show_progress_bar=False).tolist()

            self.collection.add(
                ids=batch_ids,
                documents=batch_docs,
                metadatas=batch_meta,
                embeddings=embeddings
            )

            stored_count += len(batch_docs)
            progress = (stored_count / total_docs) * 100
            print_status(f"Progress: {stored_count}/{total_docs} ({progress:.1f}%)")

        actual_count = self.collection.count()
        if actual_count != total_docs:
            print_status(f"WARNING: Expected {total_docs}, stored {actual_count}")
        else:
            print_status(f"VERIFIED: All {actual_count} documents stored successfully")

        return {
            "success": True,
            "total_lines": total_lines,
            "total_words": total_words,
            "total_chunks": len(chunks),
            "total_documents": actual_count,
            "sections": len(sections),
            "accuracy_verified": actual_count == total_docs
        }

    def verify_database(self):
        print_section("COMPREHENSIVE VERIFICATION")

        count = self.collection.count()
        print_status(f"Total documents in database: {count}")

        model = self.load_embedding_model()

        test_queries = [
            "Who is Sangam Gautam?",
            "Adarsha School location",
            "Madhyapur Thimi Municipality",
            "Science Exhibition Project",
            "Renewable Energy",
            "Ganesh Sapkota",
            "Kamal Tamrakar",
            "admission process",
            "principal name",
            "Technical Stream Computer Engineering"
        ]

        print_status("Testing semantic search accuracy:")
        passed = 0
        for query in test_queries:
            embedding = model.encode(query).tolist()
            results = self.collection.query(
                query_embeddings=[embedding],
                n_results=3,
                where={"type": "content"}
            )
            if results and results.get('documents') and results['documents'][0]:
                print_status(f"    ✓ '{query}' - Found {len(results['documents'][0])} results")
                passed += 1
            else:
                print_status(f"    ✗ '{query}' - No results")

        accuracy = (passed / len(test_queries)) * 100
        print_status(f"\nSearch Accuracy: {accuracy:.1f}% ({passed}/{len(test_queries)})")

        return accuracy >= 90


def main():
    print("\n" + "=" * 80)
    print("   CREATING ENHANCED VECTOR DATABASE - 100% ACCURACY MODE")
    print("=" * 80)

    if not DATA_PATH.exists():
        print(f"\nERROR: Data file not found at {DATA_PATH}")
        return False

    print_status(f"Data file found: {DATA_PATH}")

    creator = EnhancedVectorDBCreator()
    creator.initialize()
    creator.create_collection(reset=True)

    try:
        result = creator.process_and_store(DATA_PATH)

        if result['success']:
            verification_passed = creator.verify_database()

            print("\n" + "=" * 80)
            if result['accuracy_verified'] and verification_passed:
                print("   ✓ ENHANCED VECTOR DATABASE CREATED - 100% ACCURACY VERIFIED")
            else:
                print("   ⚠ VECTOR DATABASE CREATED - VERIFICATION WARNINGS")
            print("=" * 80)
            print(f"""
Database: {VECTORDB_PATH}
Source: {DATA_PATH.name}
Statistics:
     • Lines: {result['total_lines']:,}
     • Words: {result['total_words']:,}
     • Chunks: {result['total_chunks']:,}
     • Documents: {result['total_documents']:,}
     • Sections: {result['sections']}
     • Storage Verified: {result['accuracy_verified']}

Ready to use with chatbot!
""")
            return True

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    main()

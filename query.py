#!/usr/bin/env python3
"""
Query script for Phase 1 PoC
Loads FAISS index and finds relevant text chunks for questions
"""

import sys
import pickle
import numpy as np
import re
from sentence_transformers import SentenceTransformer
import faiss
from typing import List, Dict, Tuple

class QueryEngine:
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        """Initialize the query engine with the same model used for indexing"""
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.metadata = []
        
    def load_index(self, index_path: str = "faiss_index", metadata_path: str = "metadata.pkl") -> bool:
        """Load the FAISS index and metadata"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(index_path)
            print(f"📁 Loaded FAISS index with {self.index.ntotal} vectors")
            
            # Load metadata
            with open(metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
            print(f"📁 Loaded metadata for {len(self.metadata)} chunks")
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading index: {e}")
            return False
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Search for the most relevant text chunks"""
        if self.index is None:
            print("❌ No index loaded!")
            return []
        
        # Generate embedding for the query
        query_embedding = self.model.encode([query])

        # DEBUG: Print the shape of the query embedding
        print(f"DEBUG: Query embedding shape in query: {np.array(query_embedding).shape}")

        query_embedding = np.array(query_embedding).astype('float32')
        
        # Normalize for cosine similarity
        faiss.normalize_L2(query_embedding)
        
        # Search the index
        scores, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.metadata):
                result = {
                    'rank': i + 1,
                    'score': float(score),
                    'metadata': self.metadata[idx],
                    'text': self.metadata[idx].get('text', 'Text not available'),
                    'text_chunk': f"Chunk {self.metadata[idx]['chunk_id'] + 1} of {self.metadata[idx]['total_chunks']} from {self.metadata[idx]['url']}"
                }
                results.append(result)
        
        return results
    
    def print_results(self, query: str, results: List[Dict]) -> None:
        """Print search results in a nice format"""
        print(f"\n🔍 Query: '{query}'")
        print("=" * 60)
        
        if not results:
            print("❌ No results found!")
            return
        
        for result in results:
            print(f"\n📊 Rank {result['rank']} (Score: {result['score']:.4f})")
            print(f"🌐 Source: {result['metadata']['url']}")
            print(f"📄 {result['text_chunk']}")
            print(f"📏 Text length: {result['metadata']['text_length']} characters")
            # Show more context and clean up the display
            text_content = result['text']
            # Remove any remaining citation numbers
            import re
            text_content = re.sub(r'\d+$', '', text_content)
            text_content = re.sub(r'\[\d+\]', '', text_content)
            
            print(f"📝 Content: {text_content}")
            print("-" * 40)
    
    def interactive_mode(self) -> None:
        """Run in interactive mode for multiple queries"""
        print("🤖 Interactive Query Mode")
        print("Type 'quit' or 'exit' to stop")
        print("=" * 40)
        
        while True:
            try:
                query = input("\n❓ Enter your question: ").strip()
                
                if query.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not query:
                    continue
                
                results = self.search(query)
                self.print_results(query, results)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

def main():
    """Main function to run the query engine"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python query.py <question>")
        print("  python query.py --interactive")
        print("\nExamples:")
        print("  python query.py 'What is machine learning?'")
        print("  python query.py --interactive")
        sys.exit(1)
    
    # Initialize query engine
    qe = QueryEngine()
    
    # Load index
    if not qe.load_index():
        print("❌ Failed to load index. Make sure to run vector_store.py first!")
        sys.exit(1)
    
    # Handle different modes
    if sys.argv[1] == "--interactive":
        qe.interactive_mode()
    else:
        # Single query mode
        query = " ".join(sys.argv[1:])
        results = qe.search(query)
        qe.print_results(query, results)

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Vector store creation for Phase 1 PoC
Reads JSON files, generates embeddings, and creates FAISS index
"""

import json
import os
import glob
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
import pickle
import nltk
from typing import List, Dict, Tuple

downloader = nltk.downloader.Downloader()
try:
    nltk.data.find('tokenizers/punkt_tab')
except:
    nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize


class VectorStore:
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        """Initialize the vector store with a sentence transformer model"""
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.texts = []
        self.metadata = []
        
    def chunk_text(self, text: str, chunk_size: int = 500, overlap_sentences: int = 2) -> List[str]:
        """
        Split text into overlapping chunks using a sentence-aware approach.
        
        Args:
            text (str): The input text.
            chunk_size (int): The target maximum number of words for each chunk.
            overlap_sentences (int): The number of sentences to overlap between chunks.
        """
        if not text:
            return []

        # 1. Split the text into sentences using NLTK
        sentences = sent_tokenize(text)
        
        chunks = []
        current_chunk_sentences = []
        current_word_count = 0
        
        for i, sentence in enumerate(sentences):
            sentence_word_count = len(sentence.split())
            
            # If adding the new sentence exceeds the chunk size, process the current chunk
            if current_word_count + sentence_word_count > chunk_size and current_chunk_sentences:
                chunks.append(" ".join(current_chunk_sentences))
                
                # 2. Start the next chunk with sentence-based overlap
                # Slicing handles the case where there are fewer sentences than the overlap
                current_chunk_sentences = current_chunk_sentences[-overlap_sentences:]
                current_word_count = len(" ".join(current_chunk_sentences).split())

            current_chunk_sentences.append(sentence)
            current_word_count += sentence_word_count

        # Add the last remaining chunk
        if current_chunk_sentences:
            chunks.append(" ".join(current_chunk_sentences))
            
        return chunks
        
    def load_json_files(self, pattern: str = "scraped_data_*.json") -> List[Dict]:
        """Load all JSON files matching the pattern"""
        files = glob.glob(pattern)
        data = []
        
        for file in files:
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data.append(json.load(f))
                print(f"📁 Loaded: {file}")
            except Exception as e:
                print(f"❌ Error loading {file}: {e}")
        
        return data
    
    def _extract_texts(self, obj) -> List[str]:
        """Recursively traverse a JSON-like object and collect meaningful text strings."""
        texts = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                # If value is string and the key suggests it is textual content
                if isinstance(v, str):
                    # Ignore very short strings (less than 40 chars)
                    if len(v.strip()) >= 40:
                        texts.append(v.strip())
                else:
                    texts.extend(self._extract_texts(v))
        elif isinstance(obj, list):
            for item in obj:
                texts.extend(self._extract_texts(item))
        return texts

    def process_data(self, data: List[Dict], chunk_size: int = 500) -> None:
        """Process data and prepare for indexing regardless of JSON schema"""
        print(f"🔄 Processing {len(data)} documents...")
        
        for doc in data:
            # Attempt to get a source identifier
            url = doc.get('url') or doc.get('source_url') or 'Unknown URL'
            
            # Collect all text fields recursively
            doc_texts = self._extract_texts(doc)
            
            for raw_text in doc_texts:
                # Split text into chunks
                chunks = self.chunk_text(raw_text, chunk_size)
                
                for i, chunk in enumerate(chunks):
                    self.texts.append(chunk)
                    self.metadata.append({
                        'url': url,
                        'chunk_id': i,
                        'total_chunks': len(chunks),
                        'text_length': len(chunk),
                        'text': chunk  # store text for display
                    })
        
        print(f"📊 Created {len(self.texts)} text chunks")
    
    def create_index(self) -> None:
        """Generate embeddings and create FAISS index"""
        if not self.texts:
            print("❌ No texts to process!")
            return
        
        print("🧠 Generating embeddings...")
        embeddings = self.model.encode(self.texts, show_progress_bar=True)

        # DEBUG: Print the shape of the embeddings
        print(f"DEBUG: Embeddings shape in vector_store: {np.array(embeddings).shape}")

        # Convert to float32 for FAISS
        embeddings = np.array(embeddings).astype('float32')
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        
        # Normalize vectors for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add vectors to index
        self.index.add(embeddings)
        
        print(f"✅ Created FAISS index with {self.index.ntotal} vectors")
    
    def save_index(self, index_path: str = "faiss_index", metadata_path: str = "metadata.pkl") -> None:
        """Save the FAISS index and metadata"""
        if self.index is None:
            print("❌ No index to save!")
            return
        
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        print(f"💾 Saved FAISS index to: {index_path}")
        
        # Save metadata
        with open(metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
        print(f"💾 Saved metadata to: {metadata_path}")
    
    def build_from_json_files(self, pattern: str = "scraped_data_*.json") -> None:
        """Complete pipeline: load JSON files, process, and create index"""
        print("🚀 Starting vector store creation...")
        
        # Load data
        data = self.load_json_files(pattern)
        if not data:
            print("❌ No JSON files found!")
            return
        
        # Process data
        self.process_data(data)
        
        # Create index
        self.create_index()
        
        # Save everything
        self.save_index()
        
        print("🎉 Vector store creation completed!")

def main():
    """Main function to create vector store"""
    vs = VectorStore()
    vs.build_from_json_files("scraped_data_*.json")

if __name__ == "__main__":
    main() 
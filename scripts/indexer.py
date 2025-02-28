import json
import os
from typing import List, Dict, Any
import re
from pathlib import Path
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pickle

# Download NLTK resources
nltk.download('punkt')
nltk.download('stopwords')

class DocumentProcessor:
    def __init__(self):
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words('english'))
        self.documents = []
        self.chunks = []
        
    def load_documents(self, input_dir):
        """Load all JSON document files from the input directory"""
        for file in os.listdir(input_dir):
            if file.endswith('_docs.json'):
                file_path = os.path.join(input_dir, file)
                with open(file_path, 'r') as f:
                    docs = json.load(f)
                    self.documents.extend(docs)
                    
        print(f"Loaded {len(self.documents)} documents")
    
    def preprocess_text(self, text):
        """Clean and preprocess text"""
        # Remove special characters and extra whitespace
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def chunk_document(self, document, chunk_size=500, overlap=100):
        """Split document into smaller chunks with overlap"""
        text = document['content']
        preprocessed_text = self.preprocess_text(text)
        
        # Split into sentences
        sentences = sent_tokenize(preprocessed_text)
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            if current_size + sentence_len > chunk_size and current_chunk:
                # Create chunk
                chunk_text = ' '.join(current_chunk)
                chunks.append({
                    'source': document['source'],
                    'url': document['url'],
                    'title': document['title'],
                    'chunk_text': chunk_text,
                    'chunk_id': len(chunks)
                })
                
                # Handle overlap
                overlap_size = 0
                overlap_chunks = []
                
                for i in range(len(current_chunk) - 1, -1, -1):
                    sent = current_chunk[i]
                    if overlap_size + len(sent) <= overlap:
                        overlap_chunks.insert(0, sent)
                        overlap_size += len(sent)
                    else:
                        break
                
                current_chunk = overlap_chunks
                current_size = overlap_size
            
            current_chunk.append(sentence)
            current_size += sentence_len
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'source': document['source'],
                'url': document['url'],
                'title': document['title'],
                'chunk_text': chunk_text,
                'chunk_id': len(chunks)
            })
        
        return chunks
    
    def process_all_documents(self):
        """Process all documents and create chunks"""
        for document in self.documents:
            doc_chunks = self.chunk_document(document)
            self.chunks.extend(doc_chunks)
            
        print(f"Created {len(self.chunks)} chunks")
        
    def save_processed_data(self, output_dir):
        """Save processed chunks to file"""
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "processed_chunks.json")
        
        with open(output_file, 'w') as f:
            json.dump(self.chunks, f, indent=2)
            
        print(f"Saved processed chunks to {output_file}")

class DocumentIndexer:
    def __init__(self):
        self.chunks = []
        self.vectorizer = TfidfVectorizer()
        self.chunk_vectors = None
        
    def load_chunks(self, file_path):
        """Load processed chunks from file"""
        with open(file_path, 'r') as f:
            self.chunks = json.load(f)
        print(f"Loaded {len(self.chunks)} chunks")
    
    def build_index(self):
        """Build TF-IDF index for chunks"""
        # Extract text from chunks
        texts = [chunk['chunk_text'] for chunk in self.chunks]
        
        # Create TF-IDF vectors
        self.chunk_vectors = self.vectorizer.fit_transform(texts)
        print(f"Built index with shape {self.chunk_vectors.shape}")
    
    def save_index(self, output_dir):
        """Save index to file"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save vectorizer
        vectorizer_file = os.path.join(output_dir, "vectorizer.pkl")
        with open(vectorizer_file, 'wb') as f:
            pickle.dump(self.vectorizer, f)
        
        # Save vectors
        vectors_file = os.path.join(output_dir, "chunk_vectors.npz")
        np.savez_compressed(vectors_file, data=self.chunk_vectors.data, 
                          indices=self.chunk_vectors.indices,
                          indptr=self.chunk_vectors.indptr, 
                          shape=self.chunk_vectors.shape)
        
        # Save chunks metadata
        chunks_file = os.path.join(output_dir, "chunks_metadata.json")
        with open(chunks_file, 'w') as f:
            json.dump(self.chunks, f, indent=2)
            
        print(f"Saved index to {output_dir}")

# Usage
def process_and_index_documents():
    # Process documents
    processor = DocumentProcessor()
    processor.load_documents('data/raw')
    processor.process_all_documents()
    processor.save_processed_data('data/processed')
    
    # Build index
    indexer = DocumentIndexer()
    indexer.load_chunks('data/processed/processed_chunks.json')
    indexer.build_index()
    indexer.save_index('data/index')

if __name__ == "__main__":
    process_and_index_documents()
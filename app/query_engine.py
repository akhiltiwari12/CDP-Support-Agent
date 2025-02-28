import json
import os
import pickle
import numpy as np
from scipy.sparse import csr_matrix
import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer

class QueryEngine:
    def __init__(self, index_dir):
        self.index_dir = index_dir
        self.load_index()
        
    def load_index(self):
        """Load the index from files"""
        # Load vectorizer
        vectorizer_file = os.path.join(self.index_dir, "vectorizer.pkl")
        with open(vectorizer_file, 'rb') as f:
            self.vectorizer = pickle.load(f)
        
        # Load vectors
        vectors_file = os.path.join(self.index_dir, "chunk_vectors.npz")
        loader = np.load(vectors_file, allow_pickle=True)
        self.chunk_vectors = csr_matrix((loader['data'], loader['indices'], loader['indptr']),
                                      shape=tuple(loader['shape']))
        
        # Load chunks metadata
        chunks_file = os.path.join(self.index_dir, "chunks_metadata.json")
        with open(chunks_file, 'r') as f:
            self.chunks = json.load(f)
            
        print(f"Loaded index with {len(self.chunks)} chunks")
    
    def preprocess_query(self, query):
        """Preprocess the query to match the vectorizer's preprocessing"""
        # Clean query
        query = re.sub(r'[^\w\s]', ' ', query)
        query = re.sub(r'\s+', ' ', query).strip()
        
        return query
    
    def is_how_to_question(self, query):
        """Check if the query is a how-to question"""
        how_to_patterns = [
            r'^how\s+to\s+',
            r'^how\s+(do|can|would|should)\s+i\s+',
            r'^how\s+(do|can|would|should)\s+you\s+',
            r'^what\'s\s+the\s+best\s+way\s+to\s+',
            r'^what\s+is\s+the\s+process\s+for\s+',
            r'^how\s+do\s+i\s+set\s+up\s+',
            r'^how\s+do\s+i\s+create\s+'
        ]
        
        query_lower = query.lower()
        for pattern in how_to_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def extract_cdp_name(self, query):
        """Extract CDP name from the query if present"""
        cdp_names = ['segment', 'mparticle', 'lytics', 'zeotap']
        
        query_lower = query.lower()
        for cdp in cdp_names:
            if cdp in query_lower:
                return cdp
        
        return None
    
    def search(self, query, top_k=5, cdp_filter=None):
        """Search for relevant chunks based on the query"""
        # Preprocess query
        processed_query = self.preprocess_query(query)
        
        # Convert query to TF-IDF vector
        query_vector = self.vectorizer.transform([processed_query])
        
        # Calculate cosine similarity
        similarities = np.dot(self.chunk_vectors, query_vector.T).toarray().flatten()
        
        # Get top-k results
        if cdp_filter:
            # Filter by CDP if specified
            cdp_indices = [i for i, chunk in enumerate(self.chunks) if chunk['source'].lower() == cdp_filter.lower()]
            cdp_similarities = [(i, similarities[i]) for i in cdp_indices]
            top_indices = sorted(cdp_similarities, key=lambda x: x[1], reverse=True)[:top_k]
        else:
            
            top_indices = [(i, similarities[i]) for i in range(len(similarities))]
            top_indices = sorted(top_indices, key=lambda x: x[1], reverse=True)[:top_k]
        
        
        results = []
        for idx, score in top_indices:
            if score > 0.1:  
                chunk = self.chunks[idx].copy()
                chunk['score'] = float(score)
                results.append(chunk)
        
        return results
    
    def query(self, query):
        """Process a user query and return results"""
    
        if not self.is_how_to_question(query):
            return {
                'type': 'not_how_to',
                'message': "I'm a CDP support agent. I can help answer how-to questions about Segment, mParticle, Lytics, and Zeotap. Please ask me questions like 'How do I set up a new source in Segment?' or 'How can I create a user profile in mParticle?'"
            }
        
        
        cdp_name = self.extract_cdp_name(query)
        
    
        results = self.search(query, top_k=3, cdp_filter=cdp_name)
        
        if not results:
            if cdp_name:
                return {
                    'type': 'no_results',
                    'message': f"I couldn't find specific information about how to {query.lower().replace('how do i', '').replace('how to', '').strip()} in {cdp_name.capitalize()}. Could you try rephrasing your question or ask about a different feature?"
                }
            else:
                return {
                    'type': 'no_results',
                    'message': "I couldn't find specific information about that. Could you specify which CDP (Segment, mParticle, Lytics, or Zeotap) you're asking about?"
                }
        
        response = {
            'type': 'results',
            'cdp': cdp_name,
            'query': query,
            'results': results
        }
        
        return response


class CDPComparator:
    def __init__(self, query_engine):
        self.query_engine = query_engine
    
    def is_comparison_question(self, query):
        """Check if the query is asking for a comparison"""
        comparison_patterns = [
            r'compare',
            r'difference between',
            r'how does .+ compare to',
            r'versus',
            r'vs'
        ]
        
        query_lower = query.lower()
        for pattern in comparison_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def extract_cdps_to_compare(self, query):
        """Extract which CDPs to compare from the query"""
        cdp_names = ['segment', 'mparticle', 'lytics', 'zeotap']
        
        query_lower = query.lower()
        mentioned_cdps = []
        
        for cdp in cdp_names:
            if cdp in query_lower:
                mentioned_cdps.append(cdp)
        
        return mentioned_cdps if len(mentioned_cdps) >= 2 else None
    
    def extract_feature_to_compare(self, query):
        """Extract which feature to compare"""
        feature_patterns = [
            (r'audience (creation|building|segmentation)', 'audience creation'),
            (r'data (integration|ingestion)', 'data integration'),
            (r'user (profiles|identification)', 'user profiles'),
            (r'(source|destination) (connection|integration)', 'connections'),
            (r'event (tracking|collection)', 'event tracking'),
            (r'privacy (compliance|management)', 'privacy'),
            (r'identity (resolution|matching)', 'identity resolution')
        ]
        
        query_lower = query.lower()
        for pattern, feature in feature_patterns:
            if re.search(pattern, query_lower):
                return feature
        
        return None
    
    def compare_cdps(self, query):
        """Generate a comparison between CDPs based on the query"""
        if not self.is_comparison_question(query):
            return None
        
        cdps_to_compare = self.extract_cdps_to_compare(query)
        if not cdps_to_compare:
            return {
                'type': 'comparison_error',
                'message': "I can compare different CDPs, but I need to know which ones you want to compare. Please mention at least two CDPs from Segment, mParticle, Lytics, and Zeotap."
            }
        
        feature = self.extract_feature_to_compare(query)
        if not feature:
            return {
                'type': 'comparison_error',
                'message': f"I can compare {', '.join(cdps_to_compare)}, but I need to know which feature you want to compare. For example, you can ask about audience creation, data integration, user profiles, etc."
            }
        
        # Get information about each CDP for the feature
        comparison_results = {}
        for cdp in cdps_to_compare:
            search_query = f"how to {feature} in {cdp}"
            results = self.query_engine.search(search_query, top_k=2, cdp_filter=cdp)
            if results:
                comparison_results[cdp] = results
        
        if not comparison_results:
            return {
                'type': 'comparison_error',
                'message': f"I couldn't find enough information to compare {feature} between {', '.join(cdps_to_compare)}. Could you try asking about a different feature?"
            }
        
        # Format comparison response
        response = {
            'type': 'comparison',
            'feature': feature,
            'cdps': cdps_to_compare,
            'comparison_data': comparison_results
        }
        
        return response

# Usage example
def query_example():
    query_engine = QueryEngine('data/index')
    comparator = CDPComparator(query_engine)
    
    # Regular how-to query
    query1 = "How do I set up a new source in Segment?"
    result1 = query_engine.query(query1)
    
    # Comparison query
    query2 = "How does Segment's audience creation process compare to Lytics?"
    result2 = comparator.compare_cdps(query2)
    
    return result1, result2
from qdrant_client import models
import re
from collections import Counter

class SparseEmbeddingAgent:
    """Agent 2b: BM25 Sparse Embedding - Converts text metadata to sparse vectors for hybrid search"""
    
    def __init__(self):
        self.idf_cache = {}
        self.stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were'
        }
    
    def tokenize(self, text):
        """
        Tokenize text into lowercase words, removing punctuation and stopwords.
        
        Args:
            text: Input text string
            
        Returns:
            List of tokens
        """
        # Convert to lowercase and extract alphanumeric tokens
        tokens = re.findall(r'\b\w+\b', text.lower())
        
        # Filter stopwords and short tokens
        return [t for t in tokens if t not in self.stopwords and len(t) > 2]
    
    def create_text_representation(self, metadata):
        """
        Creates a searchable text representation from structured metadata.
        
        Args:
            metadata: Structured metadata dictionary from MetadataAgent
            
        Returns:
            Combined text string for sparse embedding
        """
        text_parts = []
        
        # Disaster information
        disaster_type = metadata.get("disaster_type", "")
        disaster_name = metadata.get("disaster_name", "")
        text_parts.append(f"{disaster_type} {disaster_name}")
        
        # Damage severity
        damage_severity = metadata.get("damage_severity", "")
        text_parts.append(f"severity {damage_severity}")
        
        # Damage counts - create descriptive text
        damage_counts = metadata.get("damage_counts", {})
        for damage_type, count in damage_counts.items():
            if count > 0:
                text_parts.append(f"{count} buildings {damage_type}")
        
        # Sensor information
        sensor_info = metadata.get("sensor_info", {})
        sensor_type = sensor_info.get("type", "")
        if sensor_type:
            text_parts.append(f"sensor {sensor_type}")
        
        # Geographic description
        geoloc = metadata.get("geolocation", {})
        if geoloc:
            text_parts.append(f"latitude {geoloc.get('lat_min', 0):.2f} longitude {geoloc.get('lon_min', 0):.2f}")
        
        # Catalog ID
        catalog_id = metadata.get("catalog_id", "")
        if catalog_id:
            text_parts.append(f"catalog {catalog_id}")
        
        return " ".join(text_parts)
    
    def get_sparse_embedding(self, metadata):
        """
        Creates BM25-style sparse vector from metadata.
        
        Qdrant sparse vectors format:
        - indices: List of token IDs (hashed from tokens)
        - values: List of corresponding TF-IDF weights
        
        Args:
            metadata: Structured metadata dictionary
            
        Returns:
            models.SparseVector with indices and values
        """
        try:
            # Create text representation
            text = self.create_text_representation(metadata)
            
            # Tokenize
            tokens = self.tokenize(text)
            
            if not tokens:
                # Return empty sparse vector
                return models.SparseVector(indices=[], values=[])
            
            # Calculate term frequencies
            token_counts = Counter(tokens)
            total_terms = len(tokens)
            
            # Create sparse vector
            indices = []
            values = []
            
            for token, count in token_counts.items():
                # Use hash of token as index (consistent hashing)
                token_id = hash(token) % (10**6)  # Limit to 1M vocabulary size
                
                # Simple TF weighting (can be enhanced with IDF)
                tf = count / total_terms
                
                # BM25-style saturation
                k1 = 1.2
                b = 0.75
                doc_len = total_terms
                avg_doc_len = 50  # Approximate average document length
                
                bm25_weight = (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * (doc_len / avg_doc_len)))
                
                indices.append(token_id)
                values.append(float(bm25_weight))
            
            return models.SparseVector(
                indices=indices,
                values=values
            )
            
        except Exception as e:
            print(f"Sparse Embedding Error: {e}")
            return models.SparseVector(indices=[], values=[])
    
    def get_query_sparse_vector(self, query_text):
        """
        Creates sparse vector from query text for search.
        
        Args:
            query_text: Natural language query string
            
        Returns:
            models.SparseVector
        """
        try:
            tokens = self.tokenize(query_text)
            
            if not tokens:
                return models.SparseVector(indices=[], values=[])
            
            token_counts = Counter(tokens)
            
            indices = []
            values = []
            
            for token, count in token_counts.items():
                token_id = hash(token) % (10**6)
                # Query terms get uniform weight
                indices.append(token_id)
                values.append(float(count))
            
            return models.SparseVector(
                indices=indices,
                values=values
            )
            
        except Exception as e:
            print(f"Query Sparse Vector Error: {e}")
            return models.SparseVector(indices=[], values=[])

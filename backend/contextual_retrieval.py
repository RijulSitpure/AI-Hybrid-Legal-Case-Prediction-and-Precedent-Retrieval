# contextual_retrieval.py - FAISS with Contextual Embeddings
import numpy as np
import pickle
import faiss
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
import os

class ContextualRetrieval:
    """FAISS-based retrieval using contextual embeddings (Sentence-BERT)"""
    
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        self.index = None
        self.metadata = []
        self.model_name = model_name
        print(f"✓ Model loaded. Embedding dimension: {self.dimension}")
    
    def create_embeddings(self, texts, batch_size=32):
        print(f"Creating embeddings for {len(texts)} texts...")
        embeddings = []
        for i in tqdm(range(0, len(texts), batch_size)):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            embeddings.append(batch_embeddings)
        embeddings = np.vstack(embeddings).astype('float32')
        print(f"✓ Embeddings shape: {embeddings.shape}")
        return embeddings
    
    def build_index(self, texts, metadata):
        print("\n" + "="*60)
        print("Building FAISS Index with Contextual Embeddings")
        print("="*60)
        embeddings = self.create_embeddings(texts)
        print(f"Embeddings dtype: {embeddings.dtype}, contiguous: {embeddings.flags.c_contiguous}")
        if np.any(np.isnan(embeddings)) or np.any(np.isinf(embeddings)):
            print("Warning: NaN or inf in embeddings, replacing with 0")
            embeddings = np.nan_to_num(embeddings, nan=0.0, posinf=1.0, neginf=-1.0)
        embeddings = np.ascontiguousarray(embeddings)
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        print(f"Min norm: {norms.min():.6f}, zero norms: {np.sum(norms.flatten() == 0)}")
        norms = np.where(norms == 0, 1, norms)  # avoid division by zero
        embeddings /= norms
        print("Embeddings normalized manually.")
        print("Creating FAISS index...")
        self.index = faiss.IndexFlatIP(self.dimension)
        print("Adding embeddings to index...")
        self.index.add(embeddings)
        self.metadata = metadata
        print(f"✓ FAISS index built with {self.index.ntotal} vectors")
        return self.index
    
    def search(self, query_text, top_k=5):
        if self.index is None:
            raise ValueError("Index not built. Call build_index() or load_index() first.")
        query_embedding = self.model.encode([query_text]).astype('float32')
        faiss.normalize_L2(query_embedding)
        scores, indices = self.index.search(query_embedding, top_k)
        results = []
        for i, (idx, score) in enumerate(zip(indices[0], scores[0])):
            if idx < len(self.metadata):
                results.append({
                    'rank': i+1,
                    'metadata': self.metadata[idx],
                    'similarity_score': float(score),
                    'index': int(idx)
                })
        return results
    
    def save_index(self, filepath='faiss_legal_index.bin'):
        if self.index is None:
            raise ValueError("No index to save")
        faiss.write_index(self.index, filepath)
        with open(filepath.replace('.bin', '_metadata.pkl'), 'wb') as f:
            pickle.dump(self.metadata, f)
        print(f"✓ FAISS index saved to {filepath}")
    
    def load_index(self, filepath='faiss_indian_index.bin'):
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Index file {filepath} not found. Please run build_faiss_index.py first.")
        self.index = faiss.read_index(filepath)
        meta_path = filepath.replace('.bin', '_metadata.pkl')
        with open(meta_path, 'rb') as f:
            self.metadata = pickle.load(f)
        print(f"✓ FAISS index loaded from {filepath} ({self.index.ntotal} vectors)")
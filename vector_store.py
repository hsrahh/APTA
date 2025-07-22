import faiss
import openai
import os
import json
from sentence_transformers import SentenceTransformer
import numpy as np

# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Build the index and save to disk
def build_index(text_chunks, save_path="vector.index"):
    vectors = model.encode(text_chunks, show_progress_bar=True)
    index = faiss.IndexFlatL2(vectors.shape[1])
    index.add(np.array(vectors, dtype='float32'))
    faiss.write_index(index, save_path)
    with open("chunks.json", "w", encoding="utf-8") as f:
        json.dump(text_chunks, f)

# Search for relevant chunks
def query_index(query, k=3, index_path="vector.index"):
    index = faiss.read_index(index_path)
    with open("chunks.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    query_vec = model.encode([query])
    _, indices = index.search(np.array(query_vec, dtype='float32'), k)
    return [chunks[i] for i in indices[0]]

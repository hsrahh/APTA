from vector_store import build_index

# Load your notes from knowledge_base.txt
with open("data/knowledge_base.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Split into chunks (each block separated by a blank line)
chunks = [chunk.strip() for chunk in text.split("\n\n") if chunk.strip()]

# Build and save index
build_index(chunks, save_path="data/vector.index")

print("✅ Vector index built successfully!")

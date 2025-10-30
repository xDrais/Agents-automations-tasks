# ingest.py
import os, json, uuid
import requests
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
COLLECTION = "kb"

def chunks(text, size=1000, overlap=150):
    words = text.split()
    i = 0
    while i < len(words):
        j = min(len(words), i + size)
        yield " ".join(words[i:j])
        i = j - overlap if j - overlap > i else j

def embed_batch(texts):
    resp = requests.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "input": texts},
        timeout=120,
    )
    resp.raise_for_status()
    return [v["embedding"] for v in resp.json()["data"]]

def ensure_collection(client, dim):
    try:
        client.get_collection(COLLECTION)
    except:
        client.recreate_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

def ingest_path(path):
    client = QdrantClient(url=QDRANT_URL)
    all_texts = []
    files = []
    for root, _, fns in os.walk(path):
        for fn in fns:
            if fn.lower().endswith((".txt", ".md")):
                p = os.path.join(root, fn)
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    t = f.read()
                for c in chunks(t, size=900, overlap=150):
                    all_texts.append(c)
                    files.append({"file": p})

    # first batch to get dimension
    first = embed_batch([all_texts[0]])
    dim = len(first[0])
    ensure_collection(client, dim)

    # upsert first
    points = [PointStruct(id=str(uuid.uuid4()), vector=first[0], payload={"text": all_texts[0], **files[0]})]
    client.upsert(collection_name=COLLECTION, points=points)

    # remaining in mini-batches
    B = 64
    for i in range(1, len(all_texts), B):
        batch = all_texts[i:i+B]
        vecs = embed_batch(batch)
        pts = [
            PointStruct(id=str(uuid.uuid4()), vector=v, payload={"text": txt, **files[i+k]})
            for k, (v, txt) in enumerate(zip(vecs, batch))
        ]
        client.upsert(collection_name=COLLECTION, points=pts)
    print(f"Ingested {len(all_texts)} chunks.")

if __name__ == "__main__":
    # put your docs under ./kb
    ingest_path("./kb")

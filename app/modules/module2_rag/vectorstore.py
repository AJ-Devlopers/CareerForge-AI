import chromadb
from chromadb.config import Settings
from app.modules.module2_rag.embeddings import get_embedding

client = chromadb.Client(Settings())
collection = client.get_or_create_collection(name="resume_data")


def store_resume_chunks(chunks):
    embeddings = [get_embedding(c) for c in chunks]

    collection.add(
        documents=chunks,
        embeddings=embeddings,
        ids=[str(i) for i in range(len(chunks))]
    )
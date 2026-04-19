from app.modules.module2_rag.vectorstore import collection
from app.modules.module2_rag.embeddings import get_embedding


def retrieve_context(query):
    query_embedding = get_embedding(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=3
    )

    return " ".join(results["documents"][0])
from langchain_openai import OpenAIEmbeddings
from app.core.config_loader import settings

_embeddings = None


def _get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
            api_key=settings.OPENAI_API_KEY,
        )
    return _embeddings


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts. Returns list of 1536-dim vectors."""
    if not texts:
        return []
    return _get_embeddings().embed_documents(texts)


def embed_in_batches(texts: list[str], batch_size: int = 96) -> list[list[float]]:
    """Embed texts in batches to avoid rate limits. Returns concatenated vectors."""
    all_vectors = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        vectors = _get_embeddings().embed_documents(batch)
        all_vectors.extend(vectors)
    return all_vectors

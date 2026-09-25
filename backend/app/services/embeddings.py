from functools import lru_cache

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(MODEL_NAME)


def generate_embedding(text: str) -> list[float]:
    if not text.strip():
        raise ValueError("Cannot generate an embedding from empty text.")

    model = get_embedding_model()

    embedding = model.encode(
        text,
        normalize_embeddings=True,
    )

    return embedding.tolist()
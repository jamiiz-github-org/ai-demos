"""
Pinecone service — one index, multiple namespaces.

One instance is created at startup and injected via FastAPI dependency.
"""
import logging
from functools import lru_cache

from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec

from app.core.config import get_settings

logger = logging.getLogger("jamiiz.pinecone")


class PineconeService:
    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings

        logger.info("Connecting to Pinecone index: %s", settings.pinecone_index_name)
        self._pc = Pinecone(api_key=settings.pinecone_api_key)
        self._ensure_index()

        self._embeddings = OpenAIEmbeddings(
            model=settings.openai_embedding_model,
            dimensions=settings.openai_embedding_dimensions,
            api_key=settings.openai_api_key,
        )

    # ── Index management ──────────────────────────────────────────────

    def _ensure_index(self) -> None:
        """Create the index if it doesn't exist yet."""
        name = self._settings.pinecone_index_name
        existing = [idx.name for idx in self._pc.list_indexes()]
        if name not in existing:
            logger.info("Creating Pinecone index: %s", name)
            self._pc.create_index(
                name=name,
                dimension=self._settings.openai_embedding_dimensions,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
        else:
            logger.info("Pinecone index already exists: %s", name)

    # ── Vector store factory ──────────────────────────────────────────

    def vector_store(self, namespace: str) -> PineconeVectorStore:
        """Return a LangChain VectorStore scoped to a namespace."""
        return PineconeVectorStore(
            index=self._pc.Index(self._settings.pinecone_index_name),
            embedding=self._embeddings,
            namespace=namespace,
        )

    def retriever(self, namespace: str, k: int = 5):
        """Convenience: return a retriever for a namespace."""
        return self.vector_store(namespace).as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )

    def upsert_texts(
        self,
        texts: list[str],
        metadatas: list[dict],
        namespace: str,
    ) -> list[str]:
        """Embed and upsert a list of text chunks into a namespace."""
        store = self.vector_store(namespace)
        ids = store.add_texts(texts=texts, metadatas=metadatas)
        logger.info("Upserted %d chunks → namespace=%s", len(ids), namespace)
        return ids

    def delete_namespace(self, namespace: str) -> None:
        """Delete all vectors in a namespace (useful for re-ingestion)."""
        index = self._pc.Index(self._settings.pinecone_index_name)
        index.delete(delete_all=True, namespace=namespace)
        logger.info("Deleted all vectors in namespace: %s", namespace)

    @property
    def embeddings(self) -> OpenAIEmbeddings:
        return self._embeddings


@lru_cache
def get_pinecone_service() -> PineconeService:
    return PineconeService()

"""
RAG service — retrieves relevant chunks from Pinecone and formats them
as context for the LLM.
"""
import logging

from langchain_core.documents import Document

from app.services.pinecone_service import get_pinecone_service

logger = logging.getLogger("jamiiz.rag")


class RAGService:
    def __init__(self) -> None:
        self._pinecone = get_pinecone_service()

    def retrieve(
        self,
        query: str,
        namespace: str,
        k: int = 5,
    ) -> list[Document]:
        """Retrieve top-k relevant chunks for a query."""
        retriever = self._pinecone.retriever(namespace, k=k)
        docs = retriever.invoke(query)
        logger.debug(
            "Retrieved %d chunks for query=%r from namespace=%s",
            len(docs), query[:60], namespace,
        )
        return docs

    def format_context(self, docs: list[Document]) -> str:
        """
        Format retrieved documents into a single context string for the LLM.
        Includes source labels so the model can reference them.
        """
        if not docs:
            return ""

        parts = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "unknown")
            parts.append(f"[{i}] Source: {source}\n{doc.page_content.strip()}")

        return "\n\n".join(parts)

    def retrieve_and_format(
        self,
        query: str,
        namespace: str,
        k: int = 5,
    ) -> tuple[list[Document], str]:
        """Retrieve chunks and return both the raw docs and formatted context string."""
        docs = self.retrieve(query, namespace, k)
        context = self.format_context(docs)
        return docs, context

    def has_content(self, namespace: str) -> bool:
        """Check if a namespace has any vectors (useful for validation)."""
        try:
            from app.core.config import get_settings
            pc = self._pinecone._pc
            index = pc.Index(get_settings().pinecone_index_name)
            stats = index.describe_index_stats()
            ns_stats = stats.get("namespaces", {}).get(namespace, {})
            return ns_stats.get("vector_count", 0) > 0
        except Exception as exc:
            logger.warning("Could not check namespace stats: %s", exc)
            return True  # assume content exists if check fails


_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service

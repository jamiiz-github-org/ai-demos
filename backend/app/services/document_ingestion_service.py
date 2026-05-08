"""
Document ingestion pipeline:
  File (PDF / DOCX / TXT / MD)
    → extract text
    → split into chunks
    → embed
    → upsert to Pinecone namespace
"""
import hashlib
import logging
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
)
from langchain_core.documents import Document

from app.core.config import get_settings
from app.services.pinecone_service import get_pinecone_service

logger = logging.getLogger("jamiiz.ingestion")

SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

# Chunk settings — tuned for Q&A retrieval
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


class DocumentIngestionService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._pinecone = get_pinecone_service()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    # ── Public API ────────────────────────────────────────────────────

    def ingest_file(
        self,
        file_path: Path,
        namespace: str,
        source_label: str | None = None,
        extra_metadata: dict | None = None,
    ) -> dict:
        """
        Ingest a single file into a Pinecone namespace.

        Returns a summary dict with chunk count and vector IDs.
        """
        suffix = file_path.suffix.lower()
        if suffix not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Unsupported file type: {suffix!r}. "
                f"Supported: {sorted(SUPPORTED_EXTENSIONS)}"
            )

        logger.info("Ingesting file: %s → namespace=%s", file_path.name, namespace)
        docs = self._load(file_path)
        chunks = self._split(docs)

        source = source_label or file_path.name
        texts, metadatas = self._prepare(chunks, source, extra_metadata or {})

        ids = self._pinecone.upsert_texts(texts, metadatas, namespace)
        logger.info("Ingested %d chunks from %s", len(ids), file_path.name)

        return {
            "filename": file_path.name,
            "namespace": namespace,
            "chunks": len(ids),
            "vector_ids": ids,
        }

    def ingest_text(
        self,
        text: str,
        namespace: str,
        source_label: str = "manual-input",
        extra_metadata: dict | None = None,
    ) -> dict:
        """Ingest raw text directly (useful for website/property content)."""
        doc = Document(page_content=text, metadata={"source": source_label})
        chunks = self._splitter.split_documents([doc])
        texts, metadatas = self._prepare(chunks, source_label, extra_metadata or {})
        ids = self._pinecone.upsert_texts(texts, metadatas, namespace)
        logger.info("Ingested %d chunks of raw text → %s", len(ids), namespace)
        return {"source": source_label, "namespace": namespace, "chunks": len(ids)}

    def ingest_directory(
        self,
        directory: Path,
        namespace: str,
        glob: str = "**/*",
    ) -> list[dict]:
        """Batch ingest all supported files in a directory."""
        results = []
        for path in sorted(directory.glob(glob)):
            if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
                try:
                    result = self.ingest_file(path, namespace)
                    results.append(result)
                except Exception as exc:
                    logger.warning("Skipping %s: %s", path.name, exc)
        return results

    # ── Internal helpers ──────────────────────────────────────────────

    def _load(self, path: Path) -> list[Document]:
        suffix = path.suffix.lower()
        loader_map = {
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".txt": TextLoader,
            ".md": TextLoader,
        }
        loader_cls = loader_map[suffix]

        # TextLoader needs explicit encoding
        if suffix in (".txt", ".md"):
            loader = loader_cls(str(path), encoding="utf-8")
        else:
            loader = loader_cls(str(path))

        docs = loader.load()
        logger.debug("Loaded %d page(s) from %s", len(docs), path.name)
        return docs

    def _split(self, docs: list[Document]) -> list[Document]:
        chunks = self._splitter.split_documents(docs)
        logger.debug("Split into %d chunks", len(chunks))
        return chunks

    def _prepare(
        self,
        chunks: list[Document],
        source: str,
        extra: dict,
    ) -> tuple[list[str], list[dict]]:
        texts = []
        metadatas = []
        for i, chunk in enumerate(chunks):
            texts.append(chunk.page_content)
            # Deterministic ID: same file + same chunk index = same vector ID
            # This means re-running ingest overwrites rather than duplicates
            chunk_id = hashlib.md5(f"{source}::{i}".encode()).hexdigest()
            meta = {
                **chunk.metadata,
                **extra,
                "source": source,
                "chunk_index": i,
                "chunk_id": chunk_id,
            }
            metadatas.append(meta)
        return texts, metadatas


_ingestion_service: DocumentIngestionService | None = None


def get_ingestion_service() -> DocumentIngestionService:
    global _ingestion_service
    if _ingestion_service is None:
        _ingestion_service = DocumentIngestionService()
    return _ingestion_service

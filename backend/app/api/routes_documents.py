"""
Document ingestion routes.
  POST /documents/upload   — upload a file (PDF/DOCX/TXT/MD)
  POST /documents/text     — ingest raw text
  GET  /documents/status   — check if a namespace has content
"""
import logging
import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.core.config import get_settings
from app.schemas.documents import IngestionResponse, NamespaceStatsResponse, TextIngestionRequest
from app.services.document_ingestion_service import SUPPORTED_EXTENSIONS, get_ingestion_service
from app.services.rag_service import get_rag_service

logger = logging.getLogger("jamiiz.routes.documents")
router = APIRouter(prefix="/documents", tags=["documents"])

MAX_FILE_SIZE_MB = 20


@router.post("/upload", response_model=IngestionResponse)
async def upload_document(
    file: UploadFile = File(...),
    namespace: str = Form(default="document-demo"),
) -> IngestionResponse:
    """
    Upload and ingest a document into the specified Pinecone namespace.
    Supports PDF, DOCX, TXT, MD — max 20 MB.
    """
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {suffix!r}. Supported: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    # Stream to a temp file (avoids loading entire file into memory)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        shutil.copyfileobj(file.file, tmp)

    # Check size
    size_mb = tmp_path.stat().st_size / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {size_mb:.1f} MB (max {MAX_FILE_SIZE_MB} MB)",
        )

    try:
        ingestion = get_ingestion_service()
        result = ingestion.ingest_file(
            file_path=tmp_path,
            namespace=namespace,
            source_label=file.filename,
        )
        logger.info("Uploaded and ingested: %s → %s (%d chunks)", file.filename, namespace, result["chunks"])
        return IngestionResponse(**result)
    except Exception as exc:
        logger.exception("Ingestion failed for %s", file.filename)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        tmp_path.unlink(missing_ok=True)


@router.post("/text", response_model=IngestionResponse)
async def ingest_text(body: TextIngestionRequest) -> IngestionResponse:
    """Ingest raw text directly — useful for website/property content."""
    try:
        ingestion = get_ingestion_service()
        result = ingestion.ingest_text(
            text=body.text,
            namespace=body.namespace,
            source_label=body.source_label,
        )
        return IngestionResponse(
            filename=body.source_label,
            namespace=result["namespace"],
            chunks=result["chunks"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/status/{namespace}", response_model=NamespaceStatsResponse)
async def namespace_status(namespace: str) -> NamespaceStatsResponse:
    """Check if a namespace has content ready for querying."""
    rag = get_rag_service()
    has_content = rag.has_content(namespace)
    return NamespaceStatsResponse(namespace=namespace, has_content=has_content)

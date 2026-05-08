"""
Knowledge base ingestion script.

Usage:
    uv run python3 ingest.py              # ingest all three namespaces
    uv run python3 ingest.py --jamiiz     # ingest Jamiiz website only
    uv run python3 ingest.py --property   # ingest property only
    uv run python3 ingest.py --nonprofit  # ingest nonprofit only
    uv run python3 ingest.py --clear      # wipe all namespaces before ingesting
"""
import argparse
import logging
import sys
from pathlib import Path

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("ingest")

# ── Knowledge base paths (relative to this script) ──────────────────────────
BASE = Path(__file__).parent.parent / "knowledge"

SOURCES = {
    "jamiiz":    BASE / "jamiiz",
    "property":  BASE / "property",
    "nonprofit": BASE / "nonprofit",
}


def ingest(namespaces: list[str], clear: bool = False) -> None:
    from app.core.config import get_settings
    from app.services.document_ingestion_service import get_ingestion_service
    from app.services.pinecone_service import get_pinecone_service

    settings = get_settings()
    ingestion = get_ingestion_service()
    pinecone  = get_pinecone_service()

    ns_map = {
        "jamiiz":    settings.pinecone_ns_website,
        "property":  settings.pinecone_ns_property,
        "nonprofit": settings.pinecone_ns_document,
    }

    for key in namespaces:
        folder    = SOURCES[key]
        namespace = ns_map[key]

        if clear:
            logger.info("Clearing namespace: %s", namespace)
            pinecone.delete_namespace(namespace)

        logger.info("──────────────────────────────────────────")
        logger.info("Ingesting %-12s → namespace: %s", key, namespace)
        logger.info("Folder: %s", folder)

        if not folder.exists():
            logger.warning("Folder not found, skipping: %s", folder)
            continue

        results = ingestion.ingest_directory(folder, namespace)

        if results:
            total_chunks = sum(r["chunks"] for r in results)
            logger.info(
                "✓ %s: %d file(s), %d chunks ingested",
                key, len(results), total_chunks,
            )
            for r in results:
                logger.info("    %-40s %d chunks", r["filename"], r["chunks"])
        else:
            logger.warning("No files ingested for %s — check the folder path", key)

    logger.info("──────────────────────────────────────────")
    logger.info("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest knowledge bases into Pinecone")
    parser.add_argument("--jamiiz",    action="store_true", help="Ingest Jamiiz website knowledge base")
    parser.add_argument("--property",  action="store_true", help="Ingest Asante Stays property knowledge base")
    parser.add_argument("--nonprofit", action="store_true", help="Ingest Smile Again nonprofit knowledge base")
    parser.add_argument("--clear",     action="store_true", help="Clear existing vectors before ingesting")
    args = parser.parse_args()

    # If no specific flag, ingest all
    selected = [k for k in ("jamiiz", "property", "nonprofit") if getattr(args, k)]
    if not selected:
        selected = list(SOURCES.keys())

    logger.info("Starting ingestion: %s", ", ".join(selected))
    if args.clear:
        logger.warning("--clear flag set: existing vectors will be deleted first")

    ingest(selected, clear=args.clear)


if __name__ == "__main__":
    main()

import asyncio

from app.config import settings
from app.logging import configure_logging, get_logger
from services.embeddings import EmbeddingService
from services.vector_store import QdrantStore

log = get_logger(__name__)


async def main() -> None:
    configure_logging()
    embedder = EmbeddingService()
    probe = await embedder.embed_one("probe")
    store = QdrantStore()
    await store.ensure_collection(dim=len(probe))
    log.info("migrate_done", collection=settings.qdrant_collection, dim=len(probe))
    await store.aclose()


if __name__ == "__main__":
    asyncio.run(main())

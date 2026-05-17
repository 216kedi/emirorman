import asyncio
import uuid

from qdrant_client.http.models import PointStruct

from app.config import settings
from app.logging import configure_logging, get_logger
from services.embeddings import EmbeddingService
from services.vector_store import QdrantStore

log = get_logger(__name__)

DOCS = [
    {"text": "FastAPI is a modern Python web framework for building APIs.", "source": "docs/intro.md"},
    {"text": "Qdrant is a high-performance vector similarity search engine.", "source": "docs/qdrant.md"},
    {"text": "Anthropic prompt caching reduces input token cost by up to 90%.", "source": "docs/caching.md"},
    {"text": "Hybrid retrieval combines dense vector search with sparse BM25.", "source": "docs/retrieval.md"},
    {"text": "MCP (Model Context Protocol) standardizes tool integration for AI clients.", "source": "docs/mcp.md"},
]


async def main() -> None:
    configure_logging()
    embedder = EmbeddingService()
    store = QdrantStore()

    vectors = await embedder.embed([d["text"] for d in DOCS])
    await store.ensure_collection(dim=len(vectors[0]))

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vec,
            payload={"text": doc["text"], "source": doc["source"]},
        )
        for doc, vec in zip(DOCS, vectors, strict=True)
    ]
    await store.upsert(points)
    log.info("seed_done", count=len(points), collection=settings.qdrant_collection)
    await store.aclose()


if __name__ == "__main__":
    asyncio.run(main())

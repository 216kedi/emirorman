from dataclasses import dataclass

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.models import Distance, PointStruct, VectorParams

from app.config import settings
from app.errors import RetrievalError
from app.logging import get_logger

log = get_logger(__name__)


@dataclass
class VectorHit:
    doc_id: str
    score: float
    text: str
    source: str
    payload: dict


class QdrantStore:
    def __init__(self, url: str | None = None, api_key: str | None = None, collection: str | None = None) -> None:
        self.client = AsyncQdrantClient(
            url=url or settings.qdrant_url,
            api_key=api_key or settings.qdrant_api_key or None,
        )
        self.collection = collection or settings.qdrant_collection

    async def ensure_collection(self, dim: int) -> None:
        try:
            await self.client.get_collection(self.collection)
        except Exception:
            await self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
            log.info("qdrant_collection_created", collection=self.collection, dim=dim)

    async def upsert(self, points: list[PointStruct]) -> None:
        try:
            await self.client.upsert(collection_name=self.collection, points=points)
        except Exception as e:
            raise RetrievalError(f"Qdrant upsert failed: {e}") from e

    async def search(self, vector: list[float], top_k: int = 20, filters: dict | None = None) -> list[VectorHit]:
        try:
            results = await self.client.search(
                collection_name=self.collection,
                query_vector=vector,
                limit=top_k,
                query_filter=filters,
                with_payload=True,
            )
        except Exception as e:
            raise RetrievalError(f"Qdrant search failed: {e}") from e

        hits: list[VectorHit] = []
        for r in results:
            payload = r.payload or {}
            hits.append(
                VectorHit(
                    doc_id=str(r.id),
                    score=float(r.score),
                    text=payload.get("text", ""),
                    source=payload.get("source", ""),
                    payload=payload,
                )
            )
        return hits

    async def aclose(self) -> None:
        await self.client.close()

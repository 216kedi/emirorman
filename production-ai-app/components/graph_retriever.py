"""GraphRAG: knowledge-graph augmented retrieval.

Dense/sparse retrieval finds relevant passages; graph traversal then
expands coverage to related entities and passages that pure vector search
would miss (e.g. "what connects A to B?" questions).

Graph is stored in Redis as adjacency sets so it survives restarts.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field

import redis.asyncio as aioredis

from app.config import settings
from app.logging import get_logger
from components.hybrid_retriever import HybridRetriever, RetrievedChunk
from services.embeddings import EmbeddingService

log = get_logger(__name__)

_NODE_KEY = "graph:node:{}"       # hash  → {text, source, ...}
_EDGE_KEY = "graph:edges:{}"      # set   → neighbour doc_ids
_ENTITY_KEY = "graph:entity:{}"   # set   → doc_ids mentioning entity


@dataclass
class GraphNode:
    doc_id: str
    text: str
    source: str
    entities: list[str] = field(default_factory=list)


class KnowledgeGraph:
    def __init__(self, url: str | None = None) -> None:
        self.redis = aioredis.from_url(url or settings.redis_url, decode_responses=True)

    async def add_node(self, node: GraphNode) -> None:
        await self.redis.hset(
            _NODE_KEY.format(node.doc_id),
            mapping={"text": node.text, "source": node.source, "entities": json.dumps(node.entities)},
        )
        for entity in node.entities:
            await self.redis.sadd(_ENTITY_KEY.format(entity.lower()), node.doc_id)

    async def add_edge(self, src: str, dst: str) -> None:
        await self.redis.sadd(_EDGE_KEY.format(src), dst)
        await self.redis.sadd(_EDGE_KEY.format(dst), src)

    async def neighbours(self, doc_id: str, depth: int = 1) -> set[str]:
        visited: set[str] = {doc_id}
        frontier = {doc_id}
        for _ in range(depth):
            next_frontier: set[str] = set()
            for node in frontier:
                nbrs = await self.redis.smembers(_EDGE_KEY.format(node))
                next_frontier |= nbrs - visited
            visited |= next_frontier
            frontier = next_frontier
        visited.discard(doc_id)
        return visited

    async def get_node(self, doc_id: str) -> GraphNode | None:
        data = await self.redis.hgetall(_NODE_KEY.format(doc_id))
        if not data:
            return None
        return GraphNode(
            doc_id=doc_id,
            text=data.get("text", ""),
            source=data.get("source", ""),
            entities=json.loads(data.get("entities", "[]")),
        )

    async def docs_by_entity(self, entity: str) -> set[str]:
        return await self.redis.smembers(_ENTITY_KEY.format(entity.lower()))

    async def aclose(self) -> None:
        await self.redis.aclose()


class GraphRetriever:
    def __init__(
        self,
        base_retriever: HybridRetriever,
        graph: KnowledgeGraph,
        embedder: EmbeddingService,
        expand_depth: int = 1,
        max_graph_expansion: int = 5,
    ) -> None:
        self.base = base_retriever
        self.graph = graph
        self.embedder = embedder
        self.expand_depth = expand_depth
        self.max_graph_expansion = max_graph_expansion

    async def retrieve(self, query: str, top_k: int = 20) -> list[RetrievedChunk]:
        base_hits = await self.base.retrieve(query, top_k=top_k)
        seen_ids = {h.doc_id for h in base_hits}

        expansion_ids: set[str] = set()
        for hit in base_hits[:5]:
            nbrs = await self.graph.neighbours(hit.doc_id, depth=self.expand_depth)
            expansion_ids |= nbrs - seen_ids

        expansion_ids = set(list(expansion_ids)[: self.max_graph_expansion])

        if not expansion_ids:
            return base_hits

        query_vec = await self.embedder.embed_one(query)
        extra_chunks: list[RetrievedChunk] = []
        for doc_id in expansion_ids:
            node = await self.graph.get_node(doc_id)
            if node is None:
                continue
            extra_chunks.append(
                RetrievedChunk(
                    doc_id=doc_id,
                    text=node.text,
                    score=0.3,
                    source=node.source,
                )
            )

        combined = base_hits + extra_chunks
        log.info(
            "graph_retrieve",
            base=len(base_hits),
            expanded=len(extra_chunks),
            total=len(combined),
        )
        return combined[:top_k]

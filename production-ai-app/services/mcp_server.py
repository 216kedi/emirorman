"""Expose the RAG pipeline as a Model Context Protocol server.

Run as a standalone process so other MCP-aware clients (Claude Desktop,
Cursor, etc.) can call into this app's retrieval and answer endpoints.
"""
from mcp.server.fastmcp import FastMCP

from app.dependencies import get_pipeline
from app.models import QueryRequest

mcp = FastMCP("production-ai-app")


@mcp.tool()
async def rag_query(query: str, conversation_id: str | None = None) -> dict:
    pipeline = get_pipeline()
    result = await pipeline.run(
        QueryRequest(query=query, conversation_id=conversation_id),
        trace_id="mcp",
    )
    return {
        "answer": result.answer,
        "citations": [c.model_dump() for c in result.citations],
        "cached": result.cached,
    }


@mcp.tool()
async def search_knowledge_base(query: str, top_k: int = 5) -> list[dict]:
    from app.dependencies import _embedder, _vector_store

    embedder = _embedder()
    store = _vector_store()
    vector = await embedder.embed_one(query)
    hits = await store.search(vector, top_k=top_k)
    return [
        {"doc_id": h.doc_id, "score": h.score, "text": h.text, "source": h.source}
        for h in hits
    ]


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()

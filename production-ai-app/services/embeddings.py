from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings
from app.errors import UpstreamError
from app.logging import get_logger

log = get_logger(__name__)


class EmbeddingService:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)
        self.model = model or settings.default_embedding_model

    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            resp = await self.client.embeddings.create(model=self.model, input=texts)
        except Exception as e:
            raise UpstreamError(f"Embedding call failed: {e}") from e
        return [item.embedding for item in resp.data]

    async def embed_one(self, text: str) -> list[float]:
        result = await self.embed([text])
        return result[0]

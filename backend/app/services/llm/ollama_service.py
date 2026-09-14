from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logging import logger
from app.services.llm.base import BaseLLMService


class OllamaService(BaseLLMService):
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.default_model = settings.OLLAMA_MODEL
        self.embedding_model = settings.OLLAMA_EMBEDDING_MODEL

    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> str:
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("message", {}).get("content", "")
                else:
                    logger.error(f"Ollama error {res.status_code}: {res.text}")
                    raise RuntimeError(f"Ollama server returned {res.status_code}: {res.text}")
        except httpx.ConnectError:
            return (
                f"⚠️ **Cannot connect to local Ollama server at `{self.base_url}`.**\n\n"
                "Please make sure Ollama is installed and running (`ollama serve`), and that "
                f"you have pulled the model (`ollama pull {target_model}`)."
            )
        except Exception as e:
            logger.error(f"Ollama service exception: {e}")
            raise RuntimeError(f"Ollama request failed: {str(e)}")

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings: List[List[float]] = []
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                for text in texts:
                    res = await client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.embedding_model, "prompt": text},
                    )
                    if res.status_code == 200:
                        embeddings.append(res.json().get("embedding", []))
                    else:
                        logger.warning(f"Ollama embedding fallback: {res.text}")
                        embeddings.append([0.01 * j for j in range(384)])
            return embeddings
        except Exception as e:
            logger.warning(f"Ollama embedding failure, returning fallback: {e}")
            return [[0.01 * j for j in range(384)] for _ in texts]

    async def health_check(self) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                if res.status_code == 200:
                    models = [m.get("name") for m in res.json().get("models", [])]
                    return {
                        "provider": "ollama",
                        "status": "ready",
                        "base_url": self.base_url,
                        "default_model": self.default_model,
                        "available_models": models,
                    }
        except Exception as e:
            return {
                "provider": "ollama",
                "status": "unreachable",
                "base_url": self.base_url,
                "error": str(e),
            }
        return {"provider": "ollama", "status": "unknown"}

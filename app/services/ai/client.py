import json
from typing import AsyncIterator, Dict, List, Optional

import httpx

from app.log import logger
from app.settings.config import settings

TIMEOUT = 60.0
MAX_TOKENS = 4096


class AiClient:

    @staticmethod
    def _sanitize_key(api_key: str) -> str:
        if len(api_key) <= 8:
            return "****"
        return f"{api_key[:4]}...{api_key[-4:]}"

    @staticmethod
    def _headers(api_key: str) -> Dict[str, str]:
        return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    @staticmethod
    async def chat(
        messages: List[Dict[str, str]],
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict:
        url = (base_url or settings.AI_DEFAULT_BASE_URL).rstrip("/") + "/v1/chat/completions"
        model = model or settings.AI_DEFAULT_MODEL
        payload = {"model": model, "messages": messages, "max_tokens": MAX_TOKENS, "stream": False}
        logger.info(f"AI request: model={model}, key={AiClient._sanitize_key(api_key)}")
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            response = await client.post(url, headers=AiClient._headers(api_key), json=payload)
            result = response.json()
            if response.status_code != 200:
                error_msg = result.get("error", {}).get("message", response.text)
                raise AiClient._map_error(response.status_code, error_msg)
            return {"content": result["choices"][0]["message"]["content"]}

    @staticmethod
    async def chat_stream(
        messages: List[Dict[str, str]],
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> AsyncIterator[str]:
        url = (base_url or settings.AI_DEFAULT_BASE_URL).rstrip("/") + "/v1/chat/completions"
        model = model or settings.AI_DEFAULT_MODEL
        payload = {"model": model, "messages": messages, "max_tokens": MAX_TOKENS, "stream": True}
        logger.info(f"AI stream: model={model}, key={AiClient._sanitize_key(api_key)}")
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            async with client.stream(
                "POST", url, headers=AiClient._headers(api_key), json=payload
            ) as resp:
                if resp.status_code != 200:
                    body = await resp.aread()
                    raise AiClient._map_error(resp.status_code, body.decode())
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            token = data["choices"][0].get("delta", {}).get("content", "")
                            if token:
                                yield token
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

    @staticmethod
    async def test_connection(
        api_key: str,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict:
        url = (base_url or settings.AI_DEFAULT_BASE_URL).rstrip("/") + "/v1/chat/completions"
        model = model or settings.AI_DEFAULT_MODEL
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hi"}],
            "max_tokens": 5,
            "stream": False,
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(url, headers=AiClient._headers(api_key), json=payload)
            if resp.status_code == 200:
                return {"status": "ok", "model": model}
            err = resp.json().get("error", {}).get("message", "Unknown error")
            raise AiClient._map_error(resp.status_code, err)

    @staticmethod
    def _map_error(status_code: int, message: str) -> Exception:
        from app.core.exceptions import CustomException

        if status_code == 401:
            return CustomException(message="API Key 无效，请检查后重试", code=401)
        elif status_code == 404:
            return CustomException(message="模型不可用，请检查模型名称", code=404)
        elif status_code == 429:
            return CustomException(message="请求过于频繁，请稍后重试", code=429)
        elif status_code >= 500:
            return CustomException(message=f"AI 服务暂时不可用: {message}", code=502)
        return CustomException(message=f"AI 请求失败: {message}", code=400)


ai_client = AiClient()

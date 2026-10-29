import httpx


class VLLMClient:
    """vLLM 은 OpenAI 호환 API 라서 base url 만 바꾸면 OpenAI 로도 붙일 수 있음"""

    def __init__(self, url, model, timeout=60):
        self.url = url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def is_ready(self):
        try:
            async with httpx.AsyncClient(timeout=2) as client:
                r = await client.get(f"{self.url}/health")
            return r.status_code == 200
        except httpx.HTTPError:
            return False

    async def chat(self, messages, temperature=0.7, max_tokens=300):
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(f"{self.url}/v1/chat/completions", json=body)
            r.raise_for_status()
        data = r.json()
        choice = data["choices"][0]
        return {
            "content": choice["message"]["content"].strip(),
            "finish_reason": choice.get("finish_reason"),
            "usage": data.get("usage") or {},
        }

import json
import os
import urllib.request

class OllamaClient:
    def __init__(self, base_url="http://localhost:11434", model=None, timeout=120):
        self.base_url = base_url.rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
        self.timeout = timeout

    def generate(self, prompt):
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode()
        request = urllib.request.Request(
            f"{self.base_url}/api/generate", data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            data = json.load(response)
        return data["response"]

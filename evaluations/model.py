import os
import time
import asyncio
from dotenv import load_dotenv
from deepeval.models import GeminiModel

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if api_key:
    api_key = api_key.strip().strip('"').strip("'")

class RobustGeminiModel(GeminiModel):
    """GeminiModel with automated retry and backoff on Google Free Tier 429/quota errors."""

    def generate(self, *args, **kwargs):
        for attempt in range(5):
            try:
                return super().generate(*args, **kwargs)
            except Exception as e:
                err_str = str(e).lower()
                if any(x in err_str for x in ["429", "503", "resource_exhausted", "unavailable", "quota", "rate", "demand"]):
                    wait_time = 15 + attempt * 10
                    print(f"\n[RobustGeminiModel] API retryable error ({err_str[:40]}...) in generate. Waiting {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
        return super().generate(*args, **kwargs)

    async def a_generate(self, *args, **kwargs):
        for attempt in range(5):
            try:
                return await super().a_generate(*args, **kwargs)
            except Exception as e:
                err_str = str(e).lower()
                if any(x in err_str for x in ["429", "503", "resource_exhausted", "unavailable", "quota", "rate", "demand"]):
                    wait_time = 15 + attempt * 10
                    print(f"\n[RobustGeminiModel] API retryable error ({err_str[:40]}...) in a_generate. Waiting {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise
        return await super().a_generate(*args, **kwargs)

eval_model = RobustGeminiModel(
    model="gemini-3.5-flash-lite",
    api_key=api_key,
    http_options={"api_version": "v1beta"},
)

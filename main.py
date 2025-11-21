import json
import logging
import os
import time
from typing import Any, Dict, Optional

import redis.asyncio as redis
import uvicorn
import yaml
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

from safety import SafetyPipeline


def load_policy() -> Dict[str, Any]:
    policy_path = os.environ.get("POLICY_PATH", "config/policy.yaml")
    with open(policy_path, "r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


policy = load_policy()
logging.basicConfig(level=getattr(logging, policy.get("logging", {}).get("level", "INFO")))
audit_logger = logging.getLogger(policy.get("logging", {}).get("audit_channel", "audit"))


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, api_policy: Dict[str, Any]):
        super().__init__(app)
        self.requests = api_policy.get("rate_limit", {}).get("requests", 60)
        self.window = api_policy.get("rate_limit", {}).get("window_seconds", 60)
        redis_url = api_policy.get("redis_url") or os.environ.get("REDIS_URL")
        self.redis: Optional[redis.Redis] = None
        if redis_url:
            try:
                self.redis = redis.from_url(redis_url)
            except Exception:
                self.redis = None
        self._local_counters: Dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        identifier = request.headers.get("x-api-key") or request.client.host
        if self.redis:
            try:
                key = f"rate:{identifier}"
                current = await self.redis.incr(key)
                if current == 1:
                    await self.redis.expire(key, self.window)
                if current > self.requests:
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"},
                    )
            except redis.ConnectionError:
                pass

        now = time.time()
        window_start = now - self.window
        counter = self._local_counters.setdefault(identifier, [])
        counter[:] = [ts for ts in counter if ts > window_start]
        if len(counter) >= self.requests:
            return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})
        counter.append(now)

        response = await call_next(request)
        return response


async def verify_api_key(x_api_key: str = Header(None)):
    allowed_keys = policy.get("api", {}).get("allowed_api_keys", [])
    if x_api_key not in allowed_keys:
        audit_logger.warning(json.dumps({"event": "auth_failure", "api_key": x_api_key}))
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


class SafetyRequest(BaseModel):
    text: str


class SafetyResponse(BaseModel):
    sanitized_text: str
    redacted_text: str
    final_output: str
    flagged: bool
    reasons: list[str]


app = FastAPI(title="Safety Gateway")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, api_policy=policy.get("api", {}))
pipeline = SafetyPipeline(policy)


@app.post("/analyze", response_model=SafetyResponse)
async def analyze(request: SafetyRequest, api_key: str = Depends(verify_api_key)):
    audit_context = {
        "event": "request",
        "api_key": api_key,
        "text_length": len(request.text),
    }
    finding = pipeline.run(request.text)
    audit_context.update({
        "flagged": finding.flagged,
        "reasons": finding.reasons,
    })
    audit_logger.info(json.dumps(audit_context))
    if finding.flagged:
        return JSONResponse(
            status_code=400,
            content={
                "sanitized_text": finding.sanitized_text,
                "redacted_text": finding.redacted_text,
                "final_output": finding.final_output,
                "flagged": finding.flagged,
                "reasons": finding.reasons,
            },
        )
    return SafetyResponse(
        sanitized_text=finding.sanitized_text,
        redacted_text=finding.redacted_text,
        final_output=finding.final_output,
        flagged=finding.flagged,
        reasons=finding.reasons,
    )


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

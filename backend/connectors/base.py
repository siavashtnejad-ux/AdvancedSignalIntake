from __future__ import annotations
from abc import ABC, abstractmethod
import httpx
from backend.models import ConnectorResult, ScanRequest
from backend.config import settings

class BaseConnector(ABC):
    code: str = "base"

    def __init__(self):
        self.timeout = settings.request_timeout

    @abstractmethod
    async def search(self, request: ScanRequest) -> ConnectorResult:
        raise NotImplementedError

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": "EthicalHorizon/3.0 research-horizon-scanning"},
            follow_redirects=True,
        )

from __future__ import annotations

import httpx

from ai_reviewer.models import CaseDetail, Page


class CaseQueueClient:
    def __init__(self, base_url: str, actor_id: str, actor_role: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {
            "X-Actor-Id": actor_id,
            "X-Actor-Role": actor_role,
            "Content-Type": "application/json",
        }

    async def fetch_pending_cases(self, page_size: int = 10) -> Page:
        async with httpx.AsyncClient() as http:
            resp = await http.get(
                f"{self._base_url}/cases",
                params={"status": "pending", "page_size": page_size, "page": 1},
                headers=self._headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return Page.model_validate(resp.json())

    async def fetch_case_detail(self, case_id: str) -> CaseDetail:
        async with httpx.AsyncClient() as http:
            resp = await http.get(
                f"{self._base_url}/cases/{case_id}",
                headers=self._headers,
                timeout=10.0,
            )
            resp.raise_for_status()
            return CaseDetail.model_validate(resp.json())

    async def post_decision(self, case_id: str, action: str, notes: str) -> None:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                f"{self._base_url}/cases/{case_id}/decisions",
                json={"action": action, "notes": notes},
                headers=self._headers,
                timeout=10.0,
            )
            resp.raise_for_status()

"""Local skill registry with optional ClawHub sync."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from clawbridge.core.skill import ClawSkill
from clawbridge.skills.loader import SkillLoader


class SkillRegistry:
    """
    A registry that combines local skills with optional
    remote ClawHub discovery.
    """

    CLAWHUB_API = "https://clawhub.openclaw.ai/api/v1"

    def __init__(
        self,
        local_paths: list[Path] | None = None,
        enable_clawhub: bool = False,
    ):
        self._loader = SkillLoader(local_paths)
        self._enable_clawhub = enable_clawhub
        self._cache: dict[str, ClawSkill] = {}

    def load_local(self) -> dict[str, ClawSkill]:
        """Load and cache all local skills."""
        for skill in self._loader.load_all():
            self._cache[skill.name] = skill
        return self._cache

    async def search_clawhub(self, query: str) -> list[dict[str, Any]]:
        """Search ClawHub for skills (if enabled)."""
        if not self._enable_clawhub:
            return []
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.CLAWHUB_API}/skills/search",
                params={"q": query},
            )
            resp.raise_for_status()
            return resp.json().get("results", [])

    def get(self, name: str) -> ClawSkill | None:
        if not self._cache:
            self.load_local()
        return self._cache.get(name)

    def list_all(self) -> list[ClawSkill]:
        if not self._cache:
            self.load_local()
        return list(self._cache.values())
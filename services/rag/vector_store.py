"""
Vector Store Abstraction — MousaviTax AI Platform
==================================================

Pluggable vector DB backend supporting three providers:
  * json      — file-based (development only, no scale)
  * qdrant    — Qdrant (recommended for production, self-hosted or cloud)
  * pgvector  — Supabase Postgres + pgvector extension

Switch via VECTOR_DB_PROVIDER env var. Default: qdrant in production,
json in development (when QDRANT_URL is not set).

@package services.rag.vector_store
"""

from __future__ import annotations

import json
import os
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable

from pydantic import BaseModel, Field


class VectorPoint(BaseModel):
    """Single record to upsert into the vector store."""
    id: str
    vector: list[float]
    payload: dict[str, Any] = Field(default_factory=dict)


class SearchHit(BaseModel):
    id: str
    score: float
    payload: dict[str, Any] = Field(default_factory=dict)


class VectorStore(ABC):
    """Abstract vector store interface — implement per backend."""

    @abstractmethod
    async def upsert(self, collection: str, points: Iterable[VectorPoint]) -> int:
        """Insert or update points. Returns count of upserted points."""

    @abstractmethod
    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchHit]:
        """Semantic search — return top-K hits sorted by relevance."""

    @abstractmethod
    async def delete(self, collection: str, ids: list[str]) -> int:
        """Delete points by id. Returns count deleted."""

    @abstractmethod
    async def count(self, collection: str) -> int:
        """Return total point count in the collection."""


# ---------------------------------------------------------------------------
# JSON-backed store (development only)
# ---------------------------------------------------------------------------

class JSONVectorStore(VectorStore):
    """
    File-backed vector store. Linear scan — works for <50k embeddings.
    Uses a per-collection lock to avoid concurrent-write corruption.
    """

    def __init__(self, base_path: str = "data") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self._locks: dict[str, threading.Lock] = {}

    def _file_for(self, collection: str) -> Path:
        safe = collection.replace("/", "_")
        return self.base_path / f"{safe}.vectors.json"

    def _lock_for(self, collection: str) -> threading.Lock:
        if collection not in self._locks:
            self._locks[collection] = threading.Lock()
        return self._locks[collection]

    def _load(self, collection: str) -> dict[str, VectorPoint]:
        f = self._file_for(collection)
        if not f.exists():
            return {}
        try:
            with f.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
            return {k: VectorPoint(**v) for k, v in data.items()}
        except (json.JSONDecodeError, ValueError):
            return {}

    def _save(self, collection: str, points: dict[str, VectorPoint]) -> None:
        f = self._file_for(collection)
        with f.open("w", encoding="utf-8") as fh:
            json.dump({k: v.model_dump() for k, v in points.items()}, fh, ensure_ascii=False)

    async def upsert(self, collection: str, points: Iterable[VectorPoint]) -> int:
        with self._lock_for(collection):
            current = self._load(collection)
            count = 0
            for p in points:
                current[p.id] = p
                count += 1
            self._save(collection, current)
        return count

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchHit]:
        import math
        all_points = list(self._load(collection).values())

        # Apply metadata filters first
        if filters:
            all_points = [
                p for p in all_points
                if all(p.payload.get(k) == v for k, v in filters.items())
            ]

        # Cosine similarity (manual — works without numpy for MVP)
        def cosine(a: list[float], b: list[float]) -> float:
            if len(a) != len(b):
                return 0.0
            dot = sum(x * y for x, y in zip(a, b))
            na = math.sqrt(sum(x * x for x in a))
            nb = math.sqrt(sum(y * y for y in b))
            if na == 0 or nb == 0:
                return 0.0
            return dot / (na * nb)

        scored = [
            SearchHit(id=p.id, score=cosine(query_vector, p.vector), payload=p.payload)
            for p in all_points
        ]
        scored.sort(key=lambda h: h.score, reverse=True)

        if score_threshold is not None:
            scored = [h for h in scored if h.score >= score_threshold]

        return scored[:limit]

    async def delete(self, collection: str, ids: list[str]) -> int:
        with self._lock_for(collection):
            current = self._load(collection)
            deleted = sum(1 for i in ids if current.pop(i, None) is not None)
            self._save(collection, current)
        return deleted

    async def count(self, collection: str) -> int:
        return len(self._load(collection))


# ---------------------------------------------------------------------------
# Qdrant-backed store (production-recommended)
# ---------------------------------------------------------------------------

class QdrantVectorStore(VectorStore):
    """
    Qdrant vector DB client. Requires `qdrant-client` package.

    Install: pip install qdrant-client>=1.7.0
    """

    def __init__(self, url: str, api_key: str | None = None) -> None:
        try:
            from qdrant_client import AsyncQdrantClient
        except ImportError as e:
            raise RuntimeError(
                "qdrant-client is not installed. Run: pip install qdrant-client>=1.7.0"
            ) from e

        self._client = AsyncQdrantClient(url=url, api_key=api_key)

    async def _ensure_collection(self, collection: str, dim: int) -> None:
        from qdrant_client.models import Distance, VectorParams
        from qdrant_client.http.exceptions import UnexpectedResponse

        try:
            await self._client.create_collection(
                collection_name=collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )
        except UnexpectedResponse as e:
            # Already exists — that's fine.
            if e.status_code != 409:
                raise

    async def upsert(self, collection: str, points: Iterable[VectorPoint]) -> int:
        from qdrant_client.models import PointStruct

        point_list = list(points)
        if not point_list:
            return 0

        dim = len(point_list[0].vector)
        await self._ensure_collection(collection, dim)

        await self._client.upsert(
            collection_name=collection,
            points=[
                PointStruct(id=p.id, vector=p.vector, payload=p.payload)
                for p in point_list
            ],
            wait=True,
        )
        return len(point_list)

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchHit]:
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        must = None
        if filters:
            must = [
                FieldCondition(key=k, match=MatchValue(value=v))
                for k, v in filters.items()
            ]

        results = await self._client.search(
            collection_name=collection,
            query_vector=query_vector,
            limit=limit,
            score_threshold=score_threshold,
            query_filter=Filter(must=must) if must else None,
        )
        return [
            SearchHit(id=str(r.id), score=r.score, payload=r.payload or {})
            for r in results
        ]

    async def delete(self, collection: str, ids: list[str]) -> int:
        from qdrant_client.http.exceptions import UnexpectedResponse
        try:
            await self._client.delete(
                collection_name=collection,
                points_selector=ids,
                wait=True,
            )
            return len(ids)
        except UnexpectedResponse as e:
            if e.status_code == 404:
                return 0
            raise

    async def count(self, collection: str) -> int:
        result = await self._client.count(collection_name=collection, exact=True)
        return result.count


# ---------------------------------------------------------------------------
# pgvector-backed store (Supabase)
# ---------------------------------------------------------------------------

class PgVectorStore(VectorStore):
    """
    Vector store backed by Supabase Postgres + pgvector extension.
    Reuses the existing Postgres connection — no separate service needed.

    Requires the `vector` extension enabled in Supabase and a table:
        CREATE TABLE embeddings (
            id TEXT PRIMARY KEY,
            collection TEXT NOT NULL,
            embedding VECTOR(1536),
            payload JSONB DEFAULT '{}',
            created_at TIMESTAMPTZ DEFAULT NOW()
        );
        CREATE INDEX ON embeddings USING ivfflat (embedding vector_cosine_ops);
    """

    def __init__(self, supabase_url: str, service_role_key: str) -> None:
        self._url = supabase_url.rstrip("/")
        self._key = service_role_key

    async def _rpc(self, function: str, params: dict) -> Any:
        res = await self._call(f"/rest/v1/rpc/{function}", method="POST", body=params)
        return res

    async def _call(
        self,
        path: str,
        method: str = "POST",
        body: dict | None = None,
    ) -> Any:
        import httpx
        headers = {
            "apikey": self._key,
            "Authorization": f"Bearer {self._key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.request(
                method, f"{self._url}{path}", headers=headers, json=body
            )
            res.raise_for_status()
            if not res.text:
                return None
            return res.json()

    async def upsert(self, collection: str, points: Iterable[VectorPoint]) -> int:
        point_list = list(points)
        if not point_list:
            return 0
        # Format embedding as a Postgres array literal
        body = {
            "collection": collection,
            "points": [
                {
                    "id": p.id,
                    "embedding": p.vector,
                    "payload": p.payload,
                }
                for p in point_list
            ],
        }
        await self._rpc("upsert_embeddings", body)
        return len(point_list)

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        limit: int = 5,
        score_threshold: float | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchHit]:
        body = {
            "collection": collection,
            "query_vector": query_vector,
            "limit": limit,
            "score_threshold": score_threshold,
            "filters": filters or {},
        }
        result = await self._rpc("search_embeddings", body) or []
        return [
            SearchHit(
                id=str(r.get("id")),
                score=float(r.get("score", 0.0)),
                payload=r.get("payload") or {},
            )
            for r in result
        ]

    async def delete(self, collection: str, ids: list[str]) -> int:
        await self._rpc("delete_embeddings", {"collection": collection, "ids": ids})
        return len(ids)

    async def count(self, collection: str) -> int:
        result = await self._rpc("count_embeddings", {"collection": collection})
        return int(result) if result else 0


# ---------------------------------------------------------------------------
# Factory — picks provider from env
# ---------------------------------------------------------------------------

_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Return the configured vector store singleton."""
    global _store
    if _store:
        return _store

    provider = os.getenv("VECTOR_DB_PROVIDER", "").lower()
    is_prod = os.getenv("NODE_ENV") == "production" or os.getenv("VERCEL_ENV") == "production"

    if not provider:
        # Auto-detect
        if is_prod:
            provider = "qdrant" if os.getenv("QDRANT_URL") else "pgvector"
        else:
            provider = "json"

    if provider == "json":
        path = os.getenv("VECTOR_DB_PATH", "data/iran_tax_vectors.json")
        _store = JSONVectorStore(base_path=str(Path(path).parent))
    elif provider == "qdrant":
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        key = os.getenv("QDRANT_API_KEY")
        _store = QdrantVectorStore(url=url, api_key=key)
    elif provider == "pgvector":
        url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError(
                "VECTOR_DB_PROVIDER=pgvector requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
            )
        _store = PgVectorStore(supabase_url=url, service_role_key=key)
    else:
        raise ValueError(f"Unknown VECTOR_DB_PROVIDER: {provider}")

    return _store


__all__ = [
    "VectorStore",
    "VectorPoint",
    "SearchHit",
    "JSONVectorStore",
    "QdrantVectorStore",
    "PgVectorStore",
    "get_vector_store",
]

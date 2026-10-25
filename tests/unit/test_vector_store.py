"""
Unit tests for the JSON-backed Vector Store.
"""

import asyncio
import math
import os
import tempfile
from pathlib import Path

import pytest

from services.rag.vector_store import (
    JSONVectorStore,
    SearchHit,
    VectorPoint,
    VectorStore,
)


@pytest.fixture
def store():
    with tempfile.TemporaryDirectory() as tmp:
        s = JSONVectorStore(base_path=tmp)
        yield s


def _vec(s: str) -> list[float]:
    """Hash a string to a fixed 8-dim vector for tests."""
    return [(float((hash(s) % (i + 7))) % 1000) / 1000.0 for i in range(8)]


@pytest.mark.unit
def test_upsert_and_count(store):
    asyncio.run(_test_upsert_and_count(store))


async def _test_upsert_and_count(store):
    points = [
        VectorPoint(id="p1", vector=_vec("alpha"), payload={"doc": "alpha"}),
        VectorPoint(id="p2", vector=_vec("beta"), payload={"doc": "beta"}),
    ]
    count = await store.upsert("test_collection", points)
    assert count == 2

    total = await store.count("test_collection")
    assert total == 2


@pytest.mark.unit
def test_search_returns_relevant_results(store):
    asyncio.run(_test_search(store))


async def _test_search(store):
    # Two points; query is identical to p1
    await store.upsert(
        "coll",
        [
            VectorPoint(id="p1", vector=[1.0, 0.0, 0.0], payload={"doc": "A"}),
            VectorPoint(id="p2", vector=[0.0, 1.0, 0.0], payload={"doc": "B"}),
        ],
    )

    hits = await store.search("coll", [1.0, 0.0, 0.0], limit=2)
    assert len(hits) == 2
    assert hits[0].id == "p1"
    assert hits[0].score == pytest.approx(1.0, abs=0.01)
    assert hits[1].id == "p2"


@pytest.mark.unit
def test_search_with_metadata_filter(store):
    asyncio.run(_test_search_with_filter(store))


async def _test_search_with_filter(store):
    await store.upsert(
        "coll",
        [
            VectorPoint(id="p1", vector=[1.0, 0.0], payload={"category": "tax_law"}),
            VectorPoint(id="p2", vector=[1.0, 0.0], payload={"category": "vat_law"}),
        ],
    )

    hits = await store.search(
        "coll", [1.0, 0.0], limit=10, filters={"category": "vat_law"}
    )
    assert len(hits) == 1
    assert hits[0].id == "p2"


@pytest.mark.unit
def test_search_with_score_threshold(store):
    asyncio.run(_test_search_with_threshold(store))


async def _test_search_with_threshold(store):
    await store.upsert(
        "coll",
        [
            VectorPoint(id="p1", vector=[1.0, 0.0]),
            VectorPoint(id="p2", vector=[0.0, 1.0]),
        ],
    )
    # Threshold 0.9 should drop the orthogonal point
    hits = await store.search("coll", [1.0, 0.0], limit=10, score_threshold=0.9)
    assert len(hits) == 1
    assert hits[0].id == "p1"


@pytest.mark.unit
def test_delete_removes_point(store):
    asyncio.run(_test_delete(store))


async def _test_delete(store):
    await store.upsert(
        "coll",
        [
            VectorPoint(id="p1", vector=[1.0, 0.0]),
            VectorPoint(id="p2", vector=[0.0, 1.0]),
        ],
    )
    deleted = await store.delete("coll", ["p1"])
    assert deleted == 1
    assert await store.count("coll") == 1


@pytest.mark.unit
def test_delete_nonexistent_id_is_safe(store):
    asyncio.run(_test_delete_nonexistent(store))


async def _test_delete_nonexistent(store):
    deleted = await store.delete("coll", ["nope"])
    assert deleted == 0


@pytest.mark.unit
def test_persistence_across_instances():
    """Same file path → same data across two store instances."""
    with tempfile.TemporaryDirectory() as tmp:
        s1 = JSONVectorStore(base_path=tmp)
        asyncio.run(
            s1.upsert(
                "coll",
                [VectorPoint(id="p1", vector=[1.0, 0.0], payload={"v": 1})],
            )
        )

        s2 = JSONVectorStore(base_path=tmp)
        count = asyncio.run(s2.count("coll"))
        assert count == 1

"""Tests for the geo module: Block dataclass + load_blocks + ee adapter."""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from mangoguard.geo import Block, block_to_ee_geometry, load_blocks

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURE_PATH = REPO_ROOT / "data" / "orchard_blocks.geojson"


def test_load_blocks_yields_two_blocks_from_fixture():
    blocks = load_blocks(FIXTURE_PATH)
    assert len(blocks) == 2
    assert all(isinstance(b, Block) for b in blocks)


def test_block_ids_are_unique_and_match_fixture():
    blocks = load_blocks(FIXTURE_PATH)
    ids = [b.id for b in blocks]
    assert ids == ["B1", "B2"]


def test_polygon_has_valid_geojson_structure():
    blocks = load_blocks(FIXTURE_PATH)
    for b in blocks:
        geom = b.polygon_geojson
        assert geom["type"] == "Polygon"
        assert isinstance(geom["coordinates"], list)
        assert len(geom["coordinates"]) >= 1
        ring = geom["coordinates"][0]
        assert len(ring) >= 4  # closed polygon: first == last, min 4 vertices
        for vertex in ring:
            assert len(vertex) == 2
            lon, lat = vertex
            assert -180.0 <= lon <= 180.0
            assert -90.0 <= lat <= 90.0


def test_block_is_frozen():
    blocks = load_blocks(FIXTURE_PATH)
    with pytest.raises((AttributeError, Exception)):
        blocks[0].id = "X"  # type: ignore[misc]


def test_load_blocks_rejects_non_feature_collection(tmp_path):
    bad = tmp_path / "bad.geojson"
    bad.write_text(json.dumps({"type": "Feature", "geometry": {}}), encoding="utf-8")
    with pytest.raises(ValueError, match="FeatureCollection"):
        load_blocks(bad)


def test_load_blocks_rejects_missing_id(tmp_path):
    bad = tmp_path / "no_id.geojson"
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
                },
            }
        ],
    }
    bad.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="properties.id"):
        load_blocks(bad)


def test_load_blocks_rejects_duplicate_ids(tmp_path):
    bad = tmp_path / "dup.geojson"
    ring = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": "B1"},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            },
            {
                "type": "Feature",
                "properties": {"id": "B1"},
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            },
        ],
    }
    bad.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        load_blocks(bad)


def test_load_blocks_rejects_non_polygon_geometry(tmp_path):
    bad = tmp_path / "point.geojson"
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": "B1"},
                "geometry": {"type": "Point", "coordinates": [0, 0]},
            }
        ],
    }
    bad.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="Polygon"):
        load_blocks(bad)


def test_load_blocks_rejects_empty_coordinates(tmp_path):
    bad = tmp_path / "empty.geojson"
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": "B1"},
                "geometry": {"type": "Polygon", "coordinates": []},
            }
        ],
    }
    bad.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="coordinates"):
        load_blocks(bad)


def test_block_to_ee_geometry_calls_polygon_constructor(monkeypatch):
    """Inject a fake `ee` module to verify the adapter wires coordinates through."""
    fake_ee = types.ModuleType("ee")
    fake_ee.Geometry = MagicMock()
    fake_ee.Geometry.Polygon = MagicMock(return_value="fake-ee-polygon")
    monkeypatch.setitem(sys.modules, "ee", fake_ee)

    blocks = load_blocks(FIXTURE_PATH)
    geom = block_to_ee_geometry(blocks[0])

    fake_ee.Geometry.Polygon.assert_called_once_with(blocks[0].polygon_geojson["coordinates"])
    assert geom == "fake-ee-polygon"


def test_block_to_ee_geometry_raises_clear_error_when_ee_missing(monkeypatch):
    monkeypatch.setitem(sys.modules, "ee", None)
    blocks = load_blocks(FIXTURE_PATH)
    with pytest.raises(RuntimeError, match="earthengine-api"):
        block_to_ee_geometry(blocks[0])

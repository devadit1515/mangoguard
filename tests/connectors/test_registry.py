"""Tests for the connector registry."""

from __future__ import annotations

import pytest

from mangoguard.connectors.agmarknet import AGMARKNETConnector
from mangoguard.connectors.base import ConnectorContext
from mangoguard.connectors.cropsap import CROPSAPConnector
from mangoguard.connectors.csv_fallback import CSVFallbackConnector
from mangoguard.connectors.dbskkv import DBSKKVConnector
from mangoguard.connectors.fasal import FasalConnector
from mangoguard.connectors.fyllo import FylloConnector
from mangoguard.connectors.imd import IMDConnector
from mangoguard.connectors.pessl import PesslConnector
from mangoguard.connectors.registry import (
    get_connector,
    get_connector_class,
    registered_sources,
)
from mangoguard.connectors.sentinel2 import Sentinel2Connector
from mangoguard.schema import ConnectorSource

_EXPECTED_MAP = {
    ConnectorSource.AGMARKNET: AGMARKNETConnector,
    ConnectorSource.IMD: IMDConnector,
    ConnectorSource.DBSKKV: DBSKKVConnector,
    ConnectorSource.CROPSAP: CROPSAPConnector,
    ConnectorSource.SENTINEL2: Sentinel2Connector,
    ConnectorSource.PESSL: PesslConnector,
    ConnectorSource.FYLLO: FylloConnector,
    ConnectorSource.FASAL: FasalConnector,
    ConnectorSource.CSV_FALLBACK: CSVFallbackConnector,
}


@pytest.mark.parametrize(("source", "expected_cls"), list(_EXPECTED_MAP.items()))
def test_get_connector_class_returns_correct_concrete_class(source, expected_cls):
    assert get_connector_class(source) is expected_cls


def test_plantix_raises_not_implemented():
    with pytest.raises(NotImplementedError, match="PLANTIX"):
        get_connector_class(ConnectorSource.PLANTIX)


def test_registered_sources_covers_all_live_connectors():
    assert registered_sources() == set(_EXPECTED_MAP.keys())


def test_registered_sources_excludes_plantix():
    assert ConnectorSource.PLANTIX not in registered_sources()


def test_get_connector_instantiates_with_context():
    """Smoke: AGMARKNET takes no extra kwargs beyond ctx."""
    ctx = ConnectorContext()
    conn = get_connector(ConnectorSource.AGMARKNET, ctx)
    assert isinstance(conn, AGMARKNETConnector)
    assert conn.ctx is ctx


def test_get_connector_forwards_kwargs_to_concrete_constructor(tmp_path):
    """Pessl takes station_id; the registry must forward it."""
    ctx = ConnectorContext()
    conn = get_connector(ConnectorSource.PESSL, ctx, station_id="ABCDEF12")
    assert isinstance(conn, PesslConnector)
    assert conn._station_id == "ABCDEF12"


def test_get_connector_propagates_plantix_not_implemented():
    """get_connector() must surface the PLANTIX raise, not silently swallow."""
    with pytest.raises(NotImplementedError, match="PLANTIX"):
        get_connector(ConnectorSource.PLANTIX, ConnectorContext())


def test_every_non_plantix_enum_value_has_a_registered_class():
    """Defensive coverage: if someone adds a new ConnectorSource enum
    value but forgets to register a class, this test fails loudly."""
    enum_minus_plantix = {s for s in ConnectorSource if s != ConnectorSource.PLANTIX}
    assert enum_minus_plantix == registered_sources()

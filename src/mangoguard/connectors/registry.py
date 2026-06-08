"""Connector registry: ``ConnectorSource`` -> concrete ``Connector`` class.

Single-source-of-truth lookup table so Plan 4's risk engine, Plan 6's
dashboard, and any future caller can spawn the right connector without
importing each one explicitly.

``get_connector(source, ctx, **kwargs)`` instantiates the class with the
caller-provided ``ConnectorContext`` and forwards any extra kwargs to
the concrete constructor (e.g., ``fixture_path=`` or ``blocks=``).

Note: ``ConnectorSource.PLANTIX`` is registered to raise
``NotImplementedError`` because the Plantix connector was deliberately
dropped from Plan 3 (per-leaf disease diagnosis is covered by Plan 5's
own MobileNetV3 detector + CROPSAP regional pressure). The enum value
stays in the schema so existing CHECK constraints and data files keep
working; the registry is the single chokepoint where this gap surfaces.
"""

from __future__ import annotations

from typing import Any

from mangoguard.connectors.agmarknet import AGMARKNETConnector
from mangoguard.connectors.base import Connector, ConnectorContext
from mangoguard.connectors.cropsap import CROPSAPConnector
from mangoguard.connectors.csv_fallback import CSVFallbackConnector
from mangoguard.connectors.dbskkv import DBSKKVConnector
from mangoguard.connectors.fasal import FasalConnector
from mangoguard.connectors.fyllo import FylloConnector
from mangoguard.connectors.imd import IMDConnector
from mangoguard.connectors.pessl import PesslConnector
from mangoguard.connectors.sentinel2 import Sentinel2Connector
from mangoguard.schema import ConnectorSource

_REGISTRY: dict[ConnectorSource, type[Connector]] = {
    ConnectorSource.AGMARKNET: AGMARKNETConnector,
    ConnectorSource.IMD: IMDConnector,
    ConnectorSource.DBSKKV: DBSKKVConnector,
    ConnectorSource.CROPSAP: CROPSAPConnector,
    ConnectorSource.SENTINEL2: Sentinel2Connector,
    ConnectorSource.PESSL: PesslConnector,
    ConnectorSource.FYLLO: FylloConnector,
    ConnectorSource.FASAL: FasalConnector,
    ConnectorSource.CSV_FALLBACK: CSVFallbackConnector,
    # ConnectorSource.PLANTIX intentionally absent -- see module docstring.
}


def get_connector_class(source: ConnectorSource) -> type[Connector]:
    """Return the concrete Connector class registered for ``source``.

    Raises ``NotImplementedError`` if no connector is registered (e.g.,
    Plantix). Raises ``KeyError`` if ``source`` is not a valid
    ``ConnectorSource`` member.
    """
    if source == ConnectorSource.PLANTIX:
        msg = (
            "ConnectorSource.PLANTIX has no registered connector "
            "(deliberately dropped from Plan 3; use Plan 5 disease "
            "detector + CROPSAP regional pressure instead)"
        )
        raise NotImplementedError(msg)
    try:
        return _REGISTRY[source]
    except KeyError as e:
        msg = f"no connector registered for {source!r}"
        raise KeyError(msg) from e


def get_connector(
    source: ConnectorSource,
    ctx: ConnectorContext,
    **kwargs: Any,
) -> Connector:
    """Instantiate the connector class registered for ``source``.

    Extra kwargs (``fixture_path=``, ``station_id=``, ``blocks=`` etc.)
    are forwarded to the concrete constructor. Each connector documents
    its own constructor arguments.
    """
    cls = get_connector_class(source)
    return cls(ctx, **kwargs)


def registered_sources() -> set[ConnectorSource]:
    """Return the set of ``ConnectorSource`` values with a live connector."""
    return set(_REGISTRY.keys())

"""Unified per-block-per-timestamp observation schema for all connectors.

Every connector — commercial (Fyllo, Fasal, Pessl, Plantix), institutional (IMD,
CROPSAP, DBSKKV), satellite (Sentinel-2 via GEE), or manual (CSV fallback) —
normalizes its native output into a stream of `BlockObservation` records.

The schema is intentionally sparse: most fields are optional because no single
connector populates everything. The disease-risk engine and the recommender
both query by `block_id + ts` window and fold whatever fields are present.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConnectorSource(str, Enum):  # noqa: UP042
    """Origin of a `BlockObservation`. One enum value per connector."""

    FYLLO = "fyllo"
    FASAL = "fasal"
    PESSL = "pessl"
    IMD = "imd"
    PLANTIX = "plantix"
    AGMARKNET = "agmarknet"
    DBSKKV = "dbskkv"
    CROPSAP = "cropsap"
    SENTINEL2 = "sentinel2"
    CSV_FALLBACK = "csv_fallback"


class BlockObservation(BaseModel):
    """A single observation about one orchard block at one timestamp."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    block_id: str = Field(..., min_length=1, max_length=32)
    ts: datetime
    source: ConnectorSource

    t_air_c: float | None = Field(None, ge=-50.0, le=70.0)
    rh_pct: float | None = Field(None, ge=0.0, le=100.0)
    leaf_wetness_hr: float | None = Field(None, ge=0.0, le=24.0)
    precip_mm: float | None = Field(None, ge=0.0)
    wind_speed_ms: float | None = Field(None, ge=0.0)
    solar_w_m2: float | None = Field(None, ge=0.0)
    soil_moisture_pct: float | None = Field(None, ge=0.0, le=100.0)

    ndvi: float | None = Field(None, ge=-1.0, le=1.0)
    ndre: float | None = Field(None, ge=-1.0, le=1.0)
    ndmi: float | None = Field(None, ge=-1.0, le=1.0)

    plantix_diagnosis_class: str | None = Field(None, max_length=64)
    cropsap_pest_pressure: float | None = Field(None, ge=0.0)

    mandi_modal_price_inr_per_quintal: float | None = Field(None, ge=0.0)

    notes: str | None = Field(None, max_length=512)

    @field_validator("ts")
    @classmethod
    def _ts_must_be_aware(cls, v: datetime) -> datetime:
        if v.tzinfo is None or v.tzinfo.utcoffset(v) is None:
            msg = "ts must be timezone-aware (got naive datetime)"
            raise ValueError(msg)
        return v

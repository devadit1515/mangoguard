"""Connector abstract base class + shared ConnectorContext."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Iterable

from mangoguard.schema import BlockObservation, ConnectorSource
from mangoguard.store import FeedStore


@dataclass(slots=True)
class ConnectorContext:
    """Shared state injected into every concrete connector."""

    store: FeedStore | None = None
    cache_dir: str | None = None
    secrets: dict[str, str] = field(default_factory=dict)

    def require_store(self) -> FeedStore:
        if self.store is None:
            msg = "ConnectorContext.store is required but was None"
            raise RuntimeError(msg)
        return self.store


class Connector(ABC):
    """Base class for all data-source connectors."""

    source: ClassVar[ConnectorSource]
    name: ClassVar[str]

    def __init__(self, ctx: ConnectorContext) -> None:
        cls = type(self)
        if (
            not hasattr(cls, "source")
            or "source" not in cls.__dict__
            and not any("source" in base.__dict__ for base in cls.__mro__ if base is not Connector)
        ):
            msg = f"{cls.__name__} must set class attr `source`"
            raise TypeError(msg)
        if not isinstance(getattr(cls, "source", None), ConnectorSource):
            msg = f"{cls.__name__}.source must be a ConnectorSource enum value"
            raise TypeError(msg)
        if not isinstance(getattr(cls, "name", None), str) or not cls.name:
            msg = f"{cls.__name__} must set class attr `name` (non-empty string)"
            raise TypeError(msg)
        self.ctx = ctx

    @abstractmethod
    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        """Yield normalized BlockObservation records for the given time window."""
        raise NotImplementedError

    def run(self, since: datetime, until: datetime) -> int:
        observations = list(self.fetch(since=since, until=until))
        for obs in observations:
            if obs.source != self.source:
                msg = (
                    f"source mismatch: connector {self.name} declared "
                    f"{self.source} but yielded {obs.source}"
                )
                raise ValueError(msg)
        store = self.ctx.require_store()
        store.insert_many(observations)
        return len(observations)

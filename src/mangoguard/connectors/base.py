"""Connector abstract base class + shared ConnectorContext."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import ClassVar

from mangoguard.schema import BlockObservation, ConnectorSource
from mangoguard.store import FeedStore

_INSERT_CHUNK_SIZE = 500


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
    """Base class for all data-source connectors.

    Concrete subclasses declare two ClassVars (``source`` and ``name``);
    ``__init_subclass__`` validates them at class-definition time so misuse
    surfaces immediately, not at first instantiation.
    """

    source: ClassVar[ConnectorSource]
    name: ClassVar[str]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        # Allow further abstract subclasses (those that don't override fetch).
        if getattr(cls, "__abstractmethods__", None):
            return
        source = cls.__dict__.get("source", getattr(cls, "source", None))
        if not isinstance(source, ConnectorSource):
            msg = f"{cls.__name__}.source must be a ConnectorSource enum value"
            raise TypeError(msg)
        name = cls.__dict__.get("name", getattr(cls, "name", None))
        if not isinstance(name, str) or not name:
            msg = f"{cls.__name__} must set class attr `name` (non-empty string)"
            raise TypeError(msg)

    def __init__(self, ctx: ConnectorContext) -> None:
        self.ctx = ctx

    @abstractmethod
    def fetch(self, since: datetime, until: datetime) -> Iterable[BlockObservation]:
        """Yield normalized BlockObservation records for the given time window.

        The window is **half-open**: ``[since, until)``. An observation whose
        ``ts`` equals ``since`` is included; one whose ``ts`` equals ``until``
        is NOT. This matches ``FeedStore.query``'s convention.
        """
        raise NotImplementedError

    def run(self, since: datetime, until: datetime) -> int:
        store = self.ctx.require_store()
        run_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        batch: list[BlockObservation] = []
        total = 0
        with store.transaction():
            for obs in self.fetch(since=since, until=until):
                if obs.source != self.source:
                    msg = (
                        f"source mismatch: connector {self.name} declared "
                        f"{self.source} but yielded {obs.source}"
                    )
                    raise ValueError(msg)
                stamped = obs.model_copy(update={"ingested_at": now, "connector_run_id": run_id})
                batch.append(stamped)
                if len(batch) >= _INSERT_CHUNK_SIZE:
                    store.insert_many(batch)
                    total += len(batch)
                    batch = []
            if batch:
                store.insert_many(batch)
                total += len(batch)
        return total

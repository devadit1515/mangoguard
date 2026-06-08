"""Connectors layer — one module per data source.

All concrete connectors subclass `Connector` (see `base.py`) and produce
streams of `BlockObservation` records that get written to the `FeedStore`.
"""

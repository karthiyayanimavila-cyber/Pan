"""Werkzeug-style health/keep-alive endpoint without a web-framework dependency."""

from .health import start_health_server

__all__ = ["start_health_server"]

"""App package initializer."""

# Keep the top-level `app` package lightweight. Service exports live under
# `app.services` to avoid import-time side-effects and circular imports.
__all__ = []
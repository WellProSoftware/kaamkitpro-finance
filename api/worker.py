"""Cloudflare Python Workers entry point for the existing FastAPI application."""

from workers import asgi

from app.main import app

# Cloudflare's ASGI adapter replaces a separately hosted Uvicorn server.
Default = asgi.entrypoint(app)

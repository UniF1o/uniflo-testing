"""Shared pytest fixtures: sys.path wiring, browser session, server helpers."""

import asyncio
import socket
import sys
from pathlib import Path

import pytest
from aiohttp import web
from playwright.async_api import Browser, async_playwright

# Expose uniflo-api to imports (adapter code lives there, not installed here).
_API_ROOT = Path(__file__).parent.parent / "uniflo-api"
if str(_API_ROOT) not in sys.path:
    sys.path.insert(0, str(_API_ROOT))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def start_server(app: web.Application) -> tuple[str, web.AppRunner]:
    """Start an aiohttp app on a free port; return (base_url, runner)."""
    runner = web.AppRunner(app)
    await runner.setup()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    site = web.TCPSite(runner, "127.0.0.1", port)
    await site.start()
    return f"http://127.0.0.1:{port}", runner


# ---------------------------------------------------------------------------
# Session-scoped browser (one Chromium instance for all tests)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
async def browser() -> Browser:
    async with async_playwright() as pw:
        b = await pw.chromium.launch(headless=True)
        yield b
        await b.close()

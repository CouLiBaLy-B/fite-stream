"""Tests for WebSocket ConnectionManager."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from fitstream.api.websocket import ConnectionManager, ws_manager


class TestConnectionManager:
    """WebSocket connection manager tests."""

    def test_init(self) -> None:
        cm = ConnectionManager()
        assert cm._connections == {}
        assert cm.active_connections == 0
        assert cm.watched_jobs == []

    def test_connect(self) -> None:
        async def _test():
            cm = ConnectionManager()
            ws = MagicMock()
            ws.accept = AsyncMock()
            await cm.connect(ws, "job-123")
            assert "job-123" in cm._connections
            assert ws in cm._connections["job-123"]
            ws.accept.assert_awaited_once()

        asyncio.run(_test())

    def test_disconnect(self) -> None:
        async def _test():
            cm = ConnectionManager()
            ws = MagicMock()
            ws.accept = AsyncMock()
            await cm.connect(ws, "job-456")
            cm.disconnect(ws, "job-456")
            assert "job-456" not in cm._connections
            assert cm.active_connections == 0

        asyncio.run(_test())

    def test_disconnect_one_of_many(self) -> None:
        async def _test():
            cm = ConnectionManager()
            ws1 = MagicMock()
            ws1.accept = AsyncMock()
            ws2 = MagicMock()
            ws2.accept = AsyncMock()
            await cm.connect(ws1, "job")
            await cm.connect(ws2, "job")
            assert cm.active_connections == 2
            cm.disconnect(ws1, "job")
            assert cm.active_connections == 1
            assert "job" in cm._connections
            assert ws2 in cm._connections["job"]

        asyncio.run(_test())

    def test_broadcast_to_job(self) -> None:
        async def _test():
            cm = ConnectionManager()
            ws1 = MagicMock()
            ws1.accept = AsyncMock()
            ws1.send_text = AsyncMock()
            ws2 = MagicMock()
            ws2.accept = AsyncMock()
            ws2.send_text = AsyncMock()
            await cm.connect(ws1, "job-x")
            await cm.connect(ws2, "job-x")
            await cm.broadcast_to_job("job-x", {"status": "done"})
            ws1.send_text.assert_awaited_once()
            ws2.send_text.assert_awaited_once()

        asyncio.run(_test())

    def test_broadcast_nonexistent_job(self) -> None:
        async def _test():
            cm = ConnectionManager()
            await cm.broadcast_to_job("no-such-job", {"test": True})

        asyncio.run(_test())

    def test_broadcast_handles_dead_connections(self) -> None:
        async def _test():
            cm = ConnectionManager()
            ws_good = MagicMock()
            ws_good.accept = AsyncMock()
            ws_good.send_text = AsyncMock()
            ws_dead = MagicMock()
            ws_dead.accept = AsyncMock()
            ws_dead.send_text = AsyncMock(side_effect=ConnectionError("dead"))
            await cm.connect(ws_good, "job")
            await cm.connect(ws_dead, "job")
            await cm.broadcast_to_job("job", {"status": "ok"})
            ws_good.send_text.assert_awaited_once()
            assert ws_dead not in cm._connections.get("job", set())

        asyncio.run(_test())

    def test_broadcast_progress(self) -> None:
        async def _test():
            cm = ConnectionManager()
            ws = MagicMock()
            ws.accept = AsyncMock()
            ws.send_text = AsyncMock()
            await cm.connect(ws, "job")
            await cm.broadcast_progress("job", "processing", 0.5, "Halfway")
            ws.send_text.assert_awaited_once()
            call_arg = ws.send_text.call_args[0][0]
            assert '"progress"' in call_arg
            assert '"processing"' in call_arg

        asyncio.run(_test())

    def test_broadcast_completion(self) -> None:
        async def _test():
            cm = ConnectionManager()
            ws = MagicMock()
            ws.accept = AsyncMock()
            ws.send_text = AsyncMock()
            await cm.connect(ws, "job")
            await cm.broadcast_completion("job", "/video.mp4", 10.0)
            ws.send_text.assert_awaited_once()
            call_arg = ws.send_text.call_args[0][0]
            assert '"completed"' in call_arg

        asyncio.run(_test())

    def test_broadcast_error(self) -> None:
        async def _test():
            cm = ConnectionManager()
            ws = MagicMock()
            ws.accept = AsyncMock()
            ws.send_text = AsyncMock()
            await cm.connect(ws, "job")
            await cm.broadcast_error("job", "GPU crashed")
            ws.send_text.assert_awaited_once()
            call_arg = ws.send_text.call_args[0][0]
            assert '"failed"' in call_arg

        asyncio.run(_test())

    def test_watched_jobs(self) -> None:
        async def _test():
            cm = ConnectionManager()
            ws = MagicMock()
            ws.accept = AsyncMock()
            await cm.connect(ws, "job-a")
            await cm.connect(ws, "job-b")
            return cm

        cm = asyncio.run(_test())
        assert set(cm.watched_jobs) == {"job-a", "job-b"}

    def test_global_ws_manager(self) -> None:
        assert isinstance(ws_manager, ConnectionManager)

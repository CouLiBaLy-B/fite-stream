"""
FitStream WebSocket — Real-time job progress streaming.

Allows the frontend to receive live progress updates instead of polling.

Usage (frontend):
    const ws = new WebSocket(`ws://localhost:8000/ws/jobs/${jobId}`);
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        // data = { status, progress, message, ... }
    };
"""

import asyncio
import json
import time
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger


class ConnectionManager:
    """Manages WebSocket connections grouped by job ID."""
    
    def __init__(self) -> None:
        self._connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, job_id: str) -> None:
        await websocket.accept()
        if job_id not in self._connections:
            self._connections[job_id] = set()
        self._connections[job_id].add(websocket)
        logger.debug(f"WS connected: job {job_id} ({len(self._connections[job_id])} clients)")
    
    def disconnect(self, websocket: WebSocket, job_id: str) -> None:
        """Remove a WebSocket connection from tracking."""
        if job_id in self._connections:
            self._connections[job_id].discard(websocket)
            if not self._connections[job_id]:
                del self._connections[job_id]
    
    async def broadcast_to_job(self, job_id: str, data: dict) -> None:
        """Send a message to all WebSocket clients watching a job."""
        if job_id not in self._connections:
            return
        
        message = json.dumps(data, default=str)
        dead_connections = set()
        
        for ws in self._connections[job_id]:
            try:
                await ws.send_text(message)
            except (ConnectionError, RuntimeError, OSError):
                dead_connections.add(ws)
        
        # Cleanup dead connections
        for ws in dead_connections:
            self._connections[job_id].discard(ws)
    
    async def broadcast_progress(
        self,
        job_id: str,
        status: str,
        progress: float,
        message: str = "",
        **extra,
    ) -> None:
        """Convenience method to broadcast a progress update."""
        await self.broadcast_to_job(job_id, {
            "type": "progress",
            "job_id": job_id,
            "status": status,
            "progress": progress,
            "message": message,
            "timestamp": time.time(),
            **extra,
        })
    
    async def broadcast_completion(
        self,
        job_id: str,
        video_url: str,
        generation_time: float,
        **metadata,
    ) -> None:
        """Broadcast job completion."""
        await self.broadcast_to_job(job_id, {
            "type": "completed",
            "job_id": job_id,
            "status": "completed",
            "progress": 1.0,
            "video_url": video_url,
            "generation_time": generation_time,
            "timestamp": time.time(),
            **metadata,
        })
    
    async def broadcast_error(self, job_id: str, error: str) -> None:
        await self.broadcast_to_job(job_id, {
            "type": "error",
            "job_id": job_id,
            "status": "failed",
            "error": error,
            "timestamp": time.time(),
        })
    
    @property
    def active_connections(self) -> int:
        """Total number of active WebSocket connections across all jobs."""
        return sum(len(conns) for conns in self._connections.values())
    
    @property
    def watched_jobs(self) -> list:
        """Watched jobs."""
        return list(self._connections.keys())


# Global instance
ws_manager = ConnectionManager()

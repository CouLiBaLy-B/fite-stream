"""
FitStream Python SDK
Client library for integrating FitStream into other applications.

Usage:
    from fitstream.sdk import FitStreamClient
    
    client = FitStreamClient("http://localhost:8000")
    
    # Generate an animation
    result = client.animate("person.jpg", "Walking in a garden")
    print(result.video_url)
    
    # Generate a story
    result = client.story("person.jpg", "Marie walks in Paris. She enters a café.")
    
    # Virtual try-on
    result = client.tryon("person.jpg", "dress.jpg", category="dress")
    
    # Download the video
    client.download(result.job_id, "output.mp4")
"""

import os
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from loguru import logger

try:
    import httpx
    HTTP_CLIENT = "httpx"
except ImportError:
    import urllib.request
    import urllib.parse
    import json as _json
    HTTP_CLIENT = "urllib"


@dataclass
class SDKResult:
    """Result from an SDK operation."""
    job_id: str
    status: str
    video_url: Optional[str] = None
    generation_time: Optional[float] = None
    error: Optional[str] = None
    raw: Optional[Dict[str, Any]] = None


class FitStreamClient:
    """
    Python SDK client for FitStream API.
    
    Provides a simple, synchronous interface for all generation endpoints.
    Handles file uploads, job polling, and video downloads.
    
    Usage:
        client = FitStreamClient("http://localhost:8000")
        
        # Quick generation (blocks until complete)
        result = client.animate("photo.jpg", "Person walks in a garden", wait=True)
        if result.status == "completed":
            client.download(result.job_id, "output.mp4")
        
        # Async (returns immediately, poll manually)
        result = client.animate("photo.jpg", "Person dances", wait=False)
        while True:
            status = client.job_status(result.job_id)
            if status["status"] in ("completed", "failed"):
                break
            time.sleep(2)
    """
    
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: Optional[str] = None,
        timeout: float = 600.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
    
    def _headers(self) -> dict:
        headers = {"User-Agent": "FitStream-SDK/0.1.0"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    def _post_multipart(self, endpoint: str, files: dict, data: dict) -> dict:
        url = f"{self.base_url}{endpoint}"
        
        if HTTP_CLIENT == "httpx":
            file_tuples = {}
            opened_files = []
            for key, path in files.items():
                f = open(path, "rb")
                opened_files.append(f)
                file_tuples[key] = (os.path.basename(path), f, "application/octet-stream")
            
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, files=file_tuples, data=data, headers=self._headers())
                    resp.raise_for_status()
                    return resp.json()
            finally:
                for f in opened_files:
                    f.close()
        else:
            # Fallback urllib (limited multipart support)
            import json
            # Simple JSON POST fallback (no file upload via urllib easily)
            req = urllib.request.Request(url, headers={**self._headers(), "Content-Type": "application/json"})
            req.data = json.dumps(data).encode()
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return _json.loads(resp.read())
    
    def _get(self, endpoint: str) -> dict:
        url = f"{self.base_url}{endpoint}"
        
        if HTTP_CLIENT == "httpx":
            with httpx.Client(timeout=30) as client:
                resp = client.get(url, headers=self._headers())
                resp.raise_for_status()
                return resp.json()
        else:
            req = urllib.request.Request(url, headers=self._headers())
            with urllib.request.urlopen(req, timeout=30) as resp:
                return _json.loads(resp.read())
    
    def _wait_for_job(self, job_id: str, poll_interval: float = 2.0) -> SDKResult:
        for _ in range(int(self.timeout / poll_interval)):
            status = self.job_status(job_id)
            
            if status.get("status") == "completed":
                return SDKResult(
                    job_id=job_id,
                    status="completed",
                    video_url=status.get("video_url"),
                    generation_time=status.get("generation_time"),
                    raw=status,
                )
            elif status.get("status") == "failed":
                return SDKResult(
                    job_id=job_id,
                    status="failed",
                    error=status.get("error", "Unknown error"),
                    raw=status,
                )
            
            time.sleep(poll_interval)
        
        return SDKResult(job_id=job_id, status="timeout", error="Generation timed out")
    
    # ========== Health ==========
    
    def health(self) -> dict:
        """Check API health and GPU status."""
        return self._get("/health")
    
    def gpu_status(self) -> dict:
        """Get GPU memory info."""
        return self._get("/gpu")
    
    # ========== Generation ==========
    
    def animate(
        self,
        image_path: str,
        prompt: str,
        style: str = "cinematic",
        preset: str = "standard",
        seed: int = -1,
        wait: bool = True,
    ) -> SDKResult:
        """Generate an animated video from a person photo + prompt."""
        data = self._post_multipart(
            "/api/v1/animate",
            files={"image": image_path},
            data={"prompt": prompt, "style": style, "preset": preset, "seed": str(seed)},
        )
        job_id = data.get("job_id", "")
        if wait:
            return self._wait_for_job(job_id)
        return SDKResult(job_id=job_id, status="queued", raw=data)
    
    def story(
        self,
        image_path: str,
        story_text: str,
        style: str = "cinematic",
        max_scenes: int = 5,
        wait: bool = True,
    ) -> SDKResult:
        """Generate a multi-scene story video."""
        data = self._post_multipart(
            "/api/v1/story",
            files={"image": image_path},
            data={"story": story_text, "style": style, "max_scenes": str(max_scenes)},
        )
        job_id = data.get("job_id", "")
        if wait:
            return self._wait_for_job(job_id)
        return SDKResult(job_id=job_id, status="queued", raw=data)
    
    def tryon(
        self,
        person_path: str,
        garment_path: str,
        prompt: str = "",
        category: str = "auto",
        wait: bool = True,
    ) -> SDKResult:
        """Virtual try-on: person + garment → video."""
        data = self._post_multipart(
            "/api/v1/tryon",
            files={"person_image": person_path, "garment_image": garment_path},
            data={"prompt": prompt, "category": category},
        )
        job_id = data.get("job_id", "")
        if wait:
            return self._wait_for_job(job_id)
        return SDKResult(job_id=job_id, status="queued", raw=data)
    
    def stylize(
        self,
        image_path: str,
        prompt: str,
        style: str = "ghibli",
        wait: bool = True,
    ) -> SDKResult:
        """Generate a stylized animation."""
        data = self._post_multipart(
            "/api/v1/style",
            files={"image": image_path},
            data={"prompt": prompt, "style": style},
        )
        job_id = data.get("job_id", "")
        if wait:
            return self._wait_for_job(job_id)
        return SDKResult(job_id=job_id, status="queued", raw=data)
    
    # ========== Jobs ==========
    
    def job_status(self, job_id: str) -> dict:
        return self._get(f"/api/v1/jobs/{job_id}")
    
    def list_jobs(self) -> dict:
        """Get job status."""
        """List all jobs."""
        return self._get("/api/v1/jobs")
    
    def download(self, job_id: str, output_path: str) -> str:
        url = f"{self.base_url}/api/v1/jobs/{job_id}/video"
        
        if HTTP_CLIENT == "httpx":
            with httpx.Client(timeout=60) as client:
                with client.stream("GET", url, headers=self._headers()) as resp:
                    resp.raise_for_status()
                    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                    with open(output_path, "wb") as f:
                        for chunk in resp.iter_bytes(chunk_size=8192):
                            f.write(chunk)
        else:
            urllib.request.urlretrieve(url, output_path)
        
        logger.info(f"📥 Downloaded: {output_path}")
        return output_path
    
    # ========== Gallery & Utils ==========
    
    def gallery(self, limit: int = 20) -> dict:
        return self._get(f"/api/v1/gallery?limit={limit}")
    
    def list_styles(self) -> dict:
        """Get the video gallery."""
        """List available style presets."""
        return self._get("/api/v1/styles")
    
    def list_templates(self, category: Optional[str] = None) -> dict:
        url = "/api/v1/templates"
        if category:
            url += f"?category={category}"
        return self._get(url)
    
    def analyze_image(self, image_path: str) -> dict:
        return self._post_multipart("/api/v1/analyze", files={"image": image_path}, data={})
    
    def metrics(self) -> dict:
        """Analyze image quality."""
        """Get API performance metrics."""
        return self._get("/api/v1/metrics")

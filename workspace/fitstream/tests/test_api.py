"""Integration tests for the FitStream API — uses the app factory."""

import io
import pytest
from PIL import Image

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient
from fitstream.api.app_factory import create_app


@pytest.fixture
def client():
    """Create a fresh app + client for each test with generous rate limits."""
    import fitstream.api.dependencies as deps
    deps._config = None
    deps._model_manager = None
    deps._job_queue = None
    
    # Increase rate limits for testing
    from fitstream.api.middleware import rate_limiter
    rate_limiter._requests.clear()
    rate_limiter._gen_requests.clear()
    rate_limiter.rpm = 1000
    rate_limiter.burst = 1000
    rate_limiter.gen_rpm = 100
    
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_image_bytes():
    img = Image.new("RGB", (400, 600), (128, 128, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


class TestHealthEndpoints:
    def test_root(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "FitStream" in r.json()["message"]

    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"
        assert "gpu" in r.json()

    def test_gpu_status(self, client):
        r = client.get("/gpu")
        assert r.status_code == 200
        assert "available" in r.json()


class TestJobEndpoints:
    def test_list_jobs(self, client):
        r = client.get("/api/v1/jobs")
        assert r.status_code == 200
        assert "jobs" in r.json()

    def test_get_nonexistent_job(self, client):
        r = client.get("/api/v1/jobs/nonexistent")
        assert r.status_code == 404


class TestAnimateEndpoint:
    def test_requires_image(self, client):
        r = client.post("/api/v1/animate", data={"prompt": "test"})
        assert r.status_code == 422

    def test_requires_prompt(self, client, sample_image_bytes):
        r = client.post("/api/v1/animate",
                        files={"image": ("test.jpg", sample_image_bytes, "image/jpeg")})
        assert r.status_code == 422

    def test_accepts_valid_request(self, client, sample_image_bytes):
        r = client.post("/api/v1/animate",
                        files={"image": ("test.jpg", sample_image_bytes, "image/jpeg")},
                        data={"prompt": "A person walking in a park"})
        assert r.status_code == 200
        assert "job_id" in r.json()
        assert r.json()["status"] == "queued"


class TestTryOnEndpoint:
    def test_requires_both_images(self, client, sample_image_bytes):
        r = client.post("/api/v1/tryon",
                        files={"person_image": ("p.jpg", sample_image_bytes, "image/jpeg")},
                        data={"prompt": "dress"})
        assert r.status_code == 422

    def test_accepts_valid_request(self, client, sample_image_bytes):
        g = io.BytesIO()
        Image.new("RGB", (400, 400), (200, 50, 50)).save(g, format="JPEG")
        g.seek(0)
        r = client.post("/api/v1/tryon",
                        files={
                            "person_image": ("p.jpg", sample_image_bytes, "image/jpeg"),
                            "garment_image": ("g.jpg", g, "image/jpeg"),
                        },
                        data={"prompt": "red dress", "category": "dress"})
        assert r.status_code == 200
        assert "job_id" in r.json()


class TestComposeEndpoint:
    def test_requires_min_2_images(self, client, sample_image_bytes):
        r = client.post("/api/v1/compose",
                        files=[("images", ("i1.jpg", sample_image_bytes, "image/jpeg"))],
                        data={"prompt": "test @Image 1"})
        assert r.status_code == 400

    def test_accepts_valid_request(self, client):
        bufs = []
        for i in range(3):
            b = io.BytesIO()
            Image.new("RGB", (200, 200), (i*80, 100, 150)).save(b, format="JPEG")
            b.seek(0)
            bufs.append(b)
        r = client.post("/api/v1/compose",
                        files=[("images", (f"i{i}.jpg", b, "image/jpeg")) for i, b in enumerate(bufs)],
                        data={"prompt": "Person (@Image 1) wearing (@Image 2) in (@Image 3)"})
        assert r.status_code == 200
        assert r.json()["num_reference_images"] == 3


class TestGallery:
    def test_gallery(self, client):
        r = client.get("/api/v1/gallery")
        assert r.status_code == 200
        assert "items" in r.json()
        assert "total" in r.json()


class TestAdminEndpoints:
    def test_metrics(self, client):
        r = client.get("/api/v1/metrics")
        assert r.status_code == 200

    def test_styles(self, client):
        r = client.get("/api/v1/styles")
        assert r.status_code == 200
        assert "styles" in r.json()

    def test_templates(self, client):
        r = client.get("/api/v1/templates")
        assert r.status_code == 200
        assert "templates" in r.json()

    def test_cache_stats(self, client):
        r = client.get("/api/v1/cache/stats")
        assert r.status_code == 200

    def test_plugins(self, client):
        r = client.get("/api/v1/plugins")
        assert r.status_code == 200

    def test_analytics(self, client):
        r = client.get("/api/v1/analytics")
        assert r.status_code == 200

    def test_i18n(self, client):
        r = client.get("/api/v1/i18n/fr")
        assert r.status_code == 200
        assert r.json()["language"] == "fr"


class TestFrontend:
    def test_app_page(self, client):
        r = client.get("/app")
        assert r.status_code in (200, 404)

    def test_monitor_page(self, client):
        r = client.get("/monitor")
        assert r.status_code in (200, 404)


class TestMobile:
    def test_mobile_status(self, client):
        r = client.get("/m/status")
        assert r.status_code == 200
        assert r.json()["ok"] is True

    def test_mobile_styles(self, client):
        r = client.get("/m/styles")
        assert r.status_code == 200
        assert len(r.json()) >= 10

    def test_mobile_gallery(self, client):
        r = client.get("/m/gallery")
        assert r.status_code == 200
        assert "items" in r.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""Tests for ExportPipeline."""
import tempfile, os, pytest
from PIL import Image
import numpy as np
from fitstream.core.export import ExportPipeline, ExportResult

class TestExportResult:
    def test_success(self):
        r = ExportResult(output_path="/out.gif", format="gif", file_size_mb=2.5, success=True)
        assert r.success is True
        assert r.output_path == "/out.gif"
        assert r.error is None
        assert r.format == "gif"
        assert r.file_size_mb == 2.5

    def test_failure(self):
        r = ExportResult(output_path="", format="gif", file_size_mb=0.0, success=False, error="codec missing")
        assert r.success is False
        assert r.error == "codec missing"

class TestExportPipeline:
    def test_init(self):
        ep = ExportPipeline()
        assert ep is not None

    def test_export_formats_known(self):
        ep = ExportPipeline()
        assert hasattr(ep, 'to_gif')
        assert hasattr(ep, 'to_webm')
        assert hasattr(ep, 'to_storyboard')
        assert hasattr(ep, 'to_social')

    def test_export_missing_file_returns_failure(self):
        ep = ExportPipeline()
        result = ep.to_gif("/nonexistent/video.mp4", "/tmp/out.gif")
        assert result.success is False

    def test_to_social_known_aspects(self):
        ep = ExportPipeline()
        result = ep.to_social("/nonexistent/v.mp4", "/tmp/out.mp4", aspect="9:16")
        assert isinstance(result, ExportResult)

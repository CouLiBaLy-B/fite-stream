"""Tests for export pipeline — tests that don't need ffmpeg/video files."""

import pytest
from fitstream.core.export import ExportPipeline


class TestExportPipeline:
    def test_init(self):
        exporter = ExportPipeline()
        assert exporter is not None
    
    def test_to_gif_missing_file(self):
        exporter = ExportPipeline()
        result = exporter.to_gif("/nonexistent/video.mp4", "/tmp/out.gif")
        assert result.success is False
        assert result.error is not None
    
    def test_to_webm_missing_file(self):
        exporter = ExportPipeline()
        result = exporter.to_webm("/nonexistent/video.mp4", "/tmp/out.webm")
        assert result.success is False
    
    def test_to_frames_missing_file(self):
        exporter = ExportPipeline()
        result = exporter.to_frames("/nonexistent/video.mp4", "/tmp/frames/")
        assert result.success is False
    
    def test_to_storyboard_missing_file(self):
        exporter = ExportPipeline()
        result = exporter.to_storyboard("/nonexistent/video.mp4", "/tmp/board.jpg")
        assert result.success is False
    
    def test_to_social_missing_file(self):
        exporter = ExportPipeline()
        result = exporter.to_social("/nonexistent/video.mp4", "/tmp/reel.mp4")
        assert result.success is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

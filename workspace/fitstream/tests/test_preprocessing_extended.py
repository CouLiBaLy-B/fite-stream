"""Tests for PreprocessingEngine."""
import tempfile, os, pytest
from PIL import Image
import numpy as np
from fitstream.core.preprocessing import PreprocessingEngine, ImageAnalysis

class TestImageAnalysis:
    def test_defaults(self):
        a = ImageAnalysis(width=640, height=480, aspect_ratio=1.33, is_portrait=False,
                          brightness=128.0, contrast=50.0, sharpness=100.0,
                          has_face=False, face_area_pct=0.0, quality_score=0.5,
                          issues=[], recommendations=[])
        assert a.width == 640
        assert a.quality_score == 0.5

class TestPreprocessingEngine:
    def test_analyze_image(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.jpg")
            img = Image.fromarray((np.random.rand(480, 640, 3)*255).astype(np.uint8))
            img.save(path)
            engine = PreprocessingEngine()
            analysis = engine.analyze_image(path)
            assert isinstance(analysis, ImageAnalysis)
            assert analysis.width == 640
            assert analysis.height == 480

    def test_quality_report(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.jpg")
            img = Image.fromarray((np.random.rand(480, 640, 3)*255).astype(np.uint8))
            img.save(path)
            engine = PreprocessingEngine()
            analysis = engine.analyze_image(path)
            report = engine.create_quality_report(analysis)
            assert isinstance(report, str)
            assert len(report) > 0

    def test_analyze_dark_image(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "dark.jpg")
            img = Image.fromarray((np.zeros((480, 640, 3))).astype(np.uint8))
            img.save(path)
            engine = PreprocessingEngine()
            analysis = engine.analyze_image(path)
            assert analysis.quality_score < 0.5

    def test_auto_crop_person(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "test.jpg")
            img = Image.fromarray((np.random.rand(800, 600, 3)*255).astype(np.uint8))
            img.save(path)
            engine = PreprocessingEngine()
            result = engine.auto_crop_person(path)
            assert result is not None

    def test_prepare_garment_image(self):
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "garment.jpg")
            img = Image.fromarray((np.random.rand(600, 800, 3)*255).astype(np.uint8))
            img.save(path)
            engine = PreprocessingEngine()
            result = engine.prepare_garment_image(path)
            assert result is not None

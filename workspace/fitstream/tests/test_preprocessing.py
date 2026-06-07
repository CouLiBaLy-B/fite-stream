"""Tests for the preprocessing engine — no GPU needed."""

import os
import tempfile
import pytest
from PIL import Image
import numpy as np

from fitstream.core.preprocessing import PreprocessingEngine, ImageAnalysis


@pytest.fixture
def engine():
    return PreprocessingEngine()


@pytest.fixture
def sample_image():
    """Create a sample person-like image for testing."""
    # Create a 800x1200 image with skin-colored region (simulating a person)
    img = np.zeros((1200, 800, 3), dtype=np.uint8)
    
    # Background (gray)
    img[:, :] = [128, 128, 128]
    
    # Skin-colored face area (top center)
    img[200:400, 300:500] = [200, 160, 130]  # skin tones
    
    # Clothing area (body center)
    img[400:900, 250:550] = [50, 50, 180]  # blue clothing
    
    pil_img = Image.fromarray(img)
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        pil_img.save(f.name)
        yield f.name
    
    os.unlink(f.name)


@pytest.fixture
def dark_image():
    """Create a dark image for testing."""
    img = np.full((400, 600, 3), 20, dtype=np.uint8)
    pil_img = Image.fromarray(img)
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        pil_img.save(f.name)
        yield f.name
    
    os.unlink(f.name)


@pytest.fixture
def small_image():
    """Create a tiny image for testing."""
    img = np.full((100, 100, 3), 128, dtype=np.uint8)
    pil_img = Image.fromarray(img)
    
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        pil_img.save(f.name)
        yield f.name
    
    os.unlink(f.name)


class TestAnalyzeImage:
    def test_basic_analysis(self, engine, sample_image):
        analysis = engine.analyze_image(sample_image)
        assert isinstance(analysis, ImageAnalysis)
        assert analysis.width == 800
        assert analysis.height == 1200
        assert analysis.is_portrait == True
        assert 0 <= analysis.quality_score <= 1
    
    def test_dark_image_detected(self, engine, dark_image):
        analysis = engine.analyze_image(dark_image)
        assert analysis.brightness < 50
        assert any("dark" in issue.lower() for issue in analysis.issues)
    
    def test_small_image_detected(self, engine, small_image):
        analysis = engine.analyze_image(small_image)
        assert any("resolution" in issue.lower() for issue in analysis.issues)
    
    def test_nonexistent_file(self, engine):
        with pytest.raises(FileNotFoundError):
            engine.analyze_image("/nonexistent/path.jpg")
    
    def test_aspect_ratio(self, engine, sample_image):
        analysis = engine.analyze_image(sample_image)
        assert abs(analysis.aspect_ratio - 800/1200) < 0.01


class TestAutoCrop:
    def test_crop_to_target(self, engine, sample_image):
        result = engine.auto_crop_person(sample_image, 832, 480)
        assert result.size == (832, 480)
    
    def test_portrait_to_landscape(self, engine, sample_image):
        """Portrait image should be cropped to landscape."""
        result = engine.auto_crop_person(sample_image, 832, 480)
        assert result.size[0] > result.size[1]  # landscape


class TestPrepareGarment:
    def test_prepare_garment(self, engine):
        """Test garment preparation with a simple image."""
        img = Image.new("RGB", (500, 700), (255, 255, 255))
        
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            img.save(f.name)
            result = engine.prepare_garment_image(f.name, 832, 480)
            os.unlink(f.name)
        
        assert result.size == (832, 480)


class TestQualityReport:
    def test_report_format(self, engine, sample_image):
        analysis = engine.analyze_image(sample_image)
        report = engine.create_quality_report(analysis)
        assert isinstance(report, str)
        assert "Quality" in report
        assert "Resolution" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

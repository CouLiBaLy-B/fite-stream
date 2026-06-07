"""Tests for the LoomVideo pipeline utilities — no GPU needed."""

import pytest
from fitstream.core.pipelines.loom import (
    validate_image_references,
    build_multi_image_prompt,
    LoomPipeline,
)


class TestValidateReferences:
    def test_valid_references(self):
        warnings = validate_image_references(
            "The woman (@Image 1) wearing a dress (@Image 2)",
            num_images=2,
        )
        assert len(warnings) == 0
    
    def test_missing_reference_in_prompt(self):
        warnings = validate_image_references(
            "A beautiful scene with nature",
            num_images=2,
        )
        assert any("No @Image references" in w for w in warnings)
    
    def test_out_of_range_reference(self):
        warnings = validate_image_references(
            "The person (@Image 1) in the garden (@Image 5)",
            num_images=2,
        )
        assert any("@Image 5" in w for w in warnings)
    
    def test_unreferenced_image(self):
        warnings = validate_image_references(
            "The person (@Image 1) walking",
            num_images=3,
        )
        # Image 2 and 3 are not referenced
        assert any("Image 2" in w for w in warnings)
        assert any("Image 3" in w for w in warnings)
    
    def test_case_insensitive(self):
        warnings = validate_image_references(
            "The person (@image 1) with (@IMAGE 2)",
            num_images=2,
        )
        assert len(warnings) == 0


class TestBuildMultiImagePrompt:
    def test_basic(self):
        result = build_multi_image_prompt(
            {1: "the woman", 2: "the red dress"},
            action="walks down the street",
        )
        assert "@Image 1" in result
        assert "@Image 2" in result
        assert "walks down the street" in result
    
    def test_ordering(self):
        result = build_multi_image_prompt(
            {3: "garden", 1: "woman", 2: "dress"},
        )
        # Should be ordered: 1, 2, 3
        pos1 = result.find("@Image 1")
        pos2 = result.find("@Image 2")
        pos3 = result.find("@Image 3")
        assert pos1 < pos2 < pos3


class TestLoomPipeline:
    def test_supported_tasks(self):
        assert "mi2v" in LoomPipeline.SUPPORTED_TASKS
        assert "t2v" in LoomPipeline.SUPPORTED_TASKS
        assert "edit" in LoomPipeline.SUPPORTED_TASKS
        assert "ref_edit" in LoomPipeline.SUPPORTED_TASKS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

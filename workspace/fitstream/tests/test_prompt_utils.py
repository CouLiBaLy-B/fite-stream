"""Tests for prompt utilities — can run without GPU."""

import pytest

from fitstream.core.utils.prompt_utils import (
    Scene,
    create_story_summary,
    enhance_prompt,
    split_story_to_scenes,
)


class TestEnhancePrompt:
    def test_basic_enhancement(self):
        result = enhance_prompt("A woman walks in the park", style="cinematic")
        assert "Cinematic" in result
        assert "woman walks" in result
        assert "high quality" in result

    def test_empty_prompt(self):
        result = enhance_prompt("", style="cinematic")
        assert result == ""

    def test_no_duplicate_quality(self):
        """Should not add quality tags if already present."""
        result = enhance_prompt("A beautiful 4k scene", style="cinematic")
        assert result.count("4k") == 1

    def test_different_styles(self):
        for style in ["cinematic", "photorealistic", "anime", "dreamy"]:
            result = enhance_prompt("A person smiling", style=style)
            assert len(result) > len("A person smiling")


class TestSplitStory:
    def test_simple_story(self):
        story = "Marie walks in Paris. She enters a bakery. She buys a croissant."
        scenes = split_story_to_scenes(story, max_scenes=5)

        assert len(scenes) == 3
        assert all(isinstance(s, Scene) for s in scenes)
        assert scenes[0].index == 0
        assert scenes[1].index == 1

    def test_max_scenes_limit(self):
        story = ". ".join([f"Scene {i} happens" for i in range(20)])
        scenes = split_story_to_scenes(story, max_scenes=5)

        assert len(scenes) <= 5

    def test_structured_format(self):
        story = """
---
SCENE 1: A woman stands on a bridge at sunset
CAMERA: wide shot
MOOD: romantic
DURATION: long
---
SCENE 2: She turns and smiles at the camera
CAMERA: close-up
MOOD: happy
DURATION: short
---
"""
        scenes = split_story_to_scenes(story, max_scenes=5)

        assert len(scenes) == 2
        assert scenes[0].duration_hint == "long"
        assert scenes[1].duration_hint == "short"

    def test_mood_inference(self):
        scenes = split_story_to_scenes(
            "She smiles happily. Dark clouds gather ominously.",
            auto_enhance=False,
        )

        assert scenes[0].mood == "happy"

    def test_camera_inference(self):
        scenes = split_story_to_scenes(
            "She walks down a long street. Close view of her eyes.",
            auto_enhance=False,
        )

        assert scenes[0].camera == "wide shot"
        assert scenes[1].camera == "close-up"


class TestCreateStorySummary:
    def test_summary_format(self):
        scenes = [
            Scene(0, "Scene one", "medium", "medium shot", "happy"),
            Scene(1, "Scene two", "long", "wide shot", "dramatic"),
        ]
        summary = create_story_summary(scenes)

        assert "2 scenes" in summary
        assert "Scene 1" in summary
        assert "Scene 2" in summary


class TestScene:
    def test_frame_counts(self):
        assert Scene(0, "test", "short").get_num_frames() == 33
        assert Scene(0, "test", "medium").get_num_frames() == 49
        assert Scene(0, "test", "long").get_num_frames() == 81


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

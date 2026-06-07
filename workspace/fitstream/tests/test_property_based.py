"""
Property-Based Tests using Hypothesis.
These tests verify invariants that must hold for ALL inputs,
not just specific examples.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from fitstream.core.utils.prompt_utils import enhance_prompt, split_story_to_scenes
from fitstream.core.pipelines.tryon import detect_garment_category, build_tryon_prompt
from fitstream.core.pipelines.loom import validate_image_references
from fitstream.core.pipelines.style_transfer import get_style_prompt, STYLE_PRESETS
from fitstream.core.interfaces import (
    validate_image_upload, validate_prompt, validate_generation_params,
    GenerationRequest, GenerationResult,
)
from fitstream.core.errors import (
    FitStreamError, UserError, GPUError, PipelineError,
)
from fitstream.core.i18n import I18n, translate_prompt, SUPPORTED_LANGUAGES
from fitstream.core.cache import GenerationCache


class TestPromptEnhancement:
    """Properties of prompt enhancement."""
    
    @given(prompt=st.text(min_size=1, max_size=200))
    @settings(max_examples=50)
    def test_enhanced_prompt_is_never_empty(self, prompt: str) -> None:
        """Enhancement should never produce an empty string from non-empty input."""
        assume(prompt.strip())
        result = enhance_prompt(prompt, style="cinematic")
        assert len(result) > 0
    
    @given(prompt=st.text(min_size=5, max_size=100))
    @settings(max_examples=50)
    def test_enhanced_prompt_contains_original_content(self, prompt: str) -> None:
        """The original prompt content should be present in the enhanced version."""
        assume(prompt.strip() and len(prompt.strip()) >= 5)
        result = enhance_prompt(prompt.strip(), style="cinematic", quality_suffix=False)
        # At least some words from original should appear
        original_words = set(prompt.strip().lower().split()[:3])
        result_lower = result.lower()
        found = sum(1 for w in original_words if w in result_lower)
        assert found > 0 or len(original_words) == 0
    
    @given(style=st.sampled_from(["cinematic", "photorealistic", "anime", "dreamy", "warm"]))
    def test_style_prefix_always_added(self, style: str) -> None:
        """Every style should add some prefix to the prompt."""
        result = enhance_prompt("test prompt", style=style)
        assert result != "test prompt"


class TestStoryParsing:
    """Properties of story → scene splitting."""
    
    @given(num_sentences=st.integers(min_value=1, max_value=10))
    @settings(max_examples=20)
    def test_scene_count_bounded_by_max(self, num_sentences: int) -> None:
        """Number of scenes should never exceed max_scenes."""
        story = ". ".join([f"Scene {i} happens" for i in range(num_sentences)])
        scenes = split_story_to_scenes(story, max_scenes=5, auto_enhance=False)
        assert len(scenes) <= 5
    
    @given(num_sentences=st.integers(min_value=1, max_value=20))
    @settings(max_examples=20)
    def test_scenes_always_have_prompts(self, num_sentences: int) -> None:
        """Every scene must have a non-empty prompt."""
        story = ". ".join([f"Character does thing number {i}" for i in range(num_sentences)])
        scenes = split_story_to_scenes(story, max_scenes=8, auto_enhance=False)
        for scene in scenes:
            assert len(scene.prompt.strip()) > 0


class TestInputValidation:
    """Properties of input validation functions."""
    
    @given(size=st.integers(min_value=0, max_value=200_000_000))
    @settings(max_examples=50)
    def test_validation_never_crashes(self, size: int) -> None:
        """Validation should never raise an exception."""
        errors = validate_image_upload("test.jpg", size)
        assert isinstance(errors, list)
    
    @given(prompt=st.text(min_size=0, max_size=5000))
    @settings(max_examples=50)
    def test_prompt_validation_never_crashes(self, prompt: str) -> None:
        """Prompt validation should never raise."""
        errors = validate_prompt(prompt)
        assert isinstance(errors, list)
    
    @given(
        width=st.integers(min_value=-100, max_value=100000),
        height=st.integers(min_value=-100, max_value=100000),
    )
    @settings(max_examples=50)
    def test_param_validation_catches_extremes(self, width: int, height: int) -> None:
        """Extreme parameters should always produce validation errors."""
        errors = validate_generation_params(width=width, height=height)
        if width < 64 or width > 8192 or height < 64 or height > 8192:
            assert len(errors) > 0


class TestErrorHierarchy:
    """Properties of the error type system."""
    
    @given(message=st.text(min_size=1, max_size=200))
    @settings(max_examples=30)
    def test_all_errors_serialize_cleanly(self, message: str) -> None:
        """Every error type must produce a valid dict."""
        for cls in [UserError, GPUError, PipelineError]:
            err = cls(message)
            d = err.to_dict()
            assert isinstance(d, dict)
            assert "error" in d
            assert "message" in d
            assert d["message"] == message
    
    @given(message=st.text(min_size=1, max_size=100))
    def test_pipeline_error_always_retryable(self, message: str) -> None:
        """Pipeline errors should always be marked retryable."""
        err = PipelineError(message, pipeline="test")
        assert err.retryable is True


class TestI18n:
    """Properties of internationalization."""
    
    @given(lang=st.sampled_from(SUPPORTED_LANGUAGES))
    def test_all_languages_have_generate_button(self, lang: str) -> None:
        """Every language must have a translation for btn.generate."""
        i18n = I18n(lang)
        result = i18n.t("btn.generate")
        assert result != "btn.generate"  # Not the fallback key
    
    @given(lang=st.text(min_size=1, max_size=5))
    @settings(max_examples=20)
    def test_unsupported_language_falls_back(self, lang: str) -> None:
        """Unsupported languages should fall back to English without crashing."""
        i18n = I18n(lang)
        result = i18n.t("status.processing")
        assert isinstance(result, str)
        assert len(result) > 0


class TestImageReferences:
    """Properties of @Image N validation."""
    
    @given(
        num_images=st.integers(min_value=1, max_value=10),
        num_refs=st.integers(min_value=0, max_value=15),
    )
    @settings(max_examples=30)
    def test_valid_refs_produce_no_warnings(self, num_images: int, num_refs: int) -> None:
        """When all refs are valid and all images referenced, no warnings."""
        refs = " ".join(f"(@Image {i})" for i in range(1, min(num_refs, num_images) + 1))
        prompt = f"Scene with {refs}"
        warnings = validate_image_references(prompt, num_images)
        # Only valid if num_refs == num_images and all in range
        if num_refs == num_images and num_refs > 0:
            assert len(warnings) == 0


class TestStylePresets:
    """Properties of style system."""
    
    @given(style=st.sampled_from(list(STYLE_PRESETS.keys())))
    def test_every_preset_produces_longer_prompt(self, style: str) -> None:
        """Applying any style preset must make the prompt longer."""
        original = "simple test"
        result = get_style_prompt(original, style)
        assert len(result) > len(original)


class TestGenerationDataTypes:
    """Properties of request/result data types."""
    
    @given(
        seed=st.integers(min_value=-1, max_value=2**32),
        width=st.integers(min_value=64, max_value=4096),
        height=st.integers(min_value=64, max_value=4096),
    )
    @settings(max_examples=20)
    def test_request_stores_params(self, seed: int, width: int, height: int) -> None:
        """GenerationRequest must preserve all parameters."""
        req = GenerationRequest(seed=seed, width=width, height=height)
        assert req.seed == seed
        assert req.width == width
        assert req.height == height
    
    @given(success=st.booleans())
    def test_result_success_flag(self, success: bool) -> None:
        """Result success flag must round-trip correctly."""
        r = GenerationResult(success=success)
        assert r.success is success


class TestCacheKeys:
    """Properties of cache key generation."""
    
    @given(
        prompt1=st.text(min_size=1, max_size=50),
        prompt2=st.text(min_size=1, max_size=50),
    )
    @settings(max_examples=30)
    def test_different_prompts_different_keys(self, prompt1: str, prompt2: str) -> None:
        """Different prompts must produce different cache keys."""
        assume(prompt1 != prompt2)
        import tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"fake image data")
            img_path = f.name
        
        try:
            k1 = GenerationCache.make_key(img_path, prompt1)
            k2 = GenerationCache.make_key(img_path, prompt2)
            assert k1 != k2
        finally:
            os.unlink(img_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

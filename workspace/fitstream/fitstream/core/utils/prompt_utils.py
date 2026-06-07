"""
Prompt utilities for FitStream.
Handles prompt enhancement, story splitting, and narrative structuring.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from loguru import logger


@dataclass
class Scene:
    """A single scene in a story."""
    index: int
    prompt: str
    duration_hint: str = "medium"  # short (2s), medium (3s), long (5s)
    camera: str = "medium shot"
    mood: str = "neutral"
    transition_to_next: str = "cut"  # cut, crossfade, match_cut
    
    def get_num_frames(self, fps: int = 16) -> int:
        durations = {"short": 33, "medium": 49, "long": 81}
        return durations.get(self.duration_hint, 49)


def enhance_prompt(
    prompt: str,
    style: str = "cinematic",
    quality_suffix: bool = True,
) -> str:
    """
    Enhance a basic prompt with quality and style modifiers.
    Keeps the original intent but adds generation-friendly details.
    """
    # Clean up the prompt
    prompt = prompt.strip()
    if not prompt:
        return prompt
    
    # Style prefixes
    style_prefixes = {
        "cinematic": "Cinematic shot,",
        "photorealistic": "Photorealistic,",
        "anime": "Anime style,",
        "artistic": "Artistic, painterly style,",
        "documentary": "Documentary style,",
        "dreamy": "Dreamy, ethereal atmosphere,",
        "noir": "Film noir style, dramatic lighting,",
        "warm": "Warm, golden hour lighting,",
    }
    
    # Quality suffixes
    quality_tags = {
        "cinematic": "high quality, smooth motion, natural lighting, 4k",
        "photorealistic": "ultra realistic, detailed, high resolution",
        "anime": "detailed anime, smooth animation, vibrant colors",
        "artistic": "beautiful composition, artistic, masterpiece",
        "documentary": "natural, authentic, handheld camera feel",
        "dreamy": "soft focus, lens flare, ethereal glow",
        "noir": "high contrast, deep shadows, moody",
        "warm": "golden light, warm tones, cozy atmosphere",
    }
    
    parts = []
    
    # Add style prefix
    if style in style_prefixes:
        parts.append(style_prefixes[style])
    
    # Add the main prompt
    parts.append(prompt)
    
    # Add quality suffix
    if quality_suffix and style in quality_tags:
        # Don't add if prompt already has quality words
        quality_words = ["4k", "high quality", "detailed", "realistic"]
        if not any(w in prompt.lower() for w in quality_words):
            parts.append(quality_tags[style])
    
    enhanced = " ".join(parts)
    
    # Clean up double spaces and punctuation
    enhanced = re.sub(r'\s+', ' ', enhanced)
    enhanced = re.sub(r',\s*,', ',', enhanced)
    
    logger.debug(f"Enhanced prompt: '{prompt[:50]}...' → '{enhanced[:80]}...'")
    return enhanced


def split_story_to_scenes(
    story_text: str,
    max_scenes: int = 8,
    auto_enhance: bool = True,
    style: str = "cinematic",
) -> List[Scene]:
    """
    Split a story text into individual scenes for video generation.
    
    Supports two formats:
    1. Free-form text (sentences become scenes)
    2. Structured format with scene markers:
       ---
       SCENE 1: Description of scene
       CAMERA: wide shot
       MOOD: happy
       DURATION: long
       ---
    """
    story_text = story_text.strip()
    
    # Check for structured format
    if "SCENE" in story_text.upper() and "---" in story_text:
        return _parse_structured_story(story_text, max_scenes, auto_enhance, style)
    
    # Free-form: split by sentences/paragraphs
    return _parse_freeform_story(story_text, max_scenes, auto_enhance, style)


def _parse_freeform_story(
    text: str,
    max_scenes: int,
    auto_enhance: bool,
    style: str,
) -> List[Scene]:
    """Parse free-form text into scenes."""
    # Split by periods, but keep meaningful sentences
    # Also split on newlines
    raw_sentences = re.split(r'(?<=[.!?])\s+|\n\n+', text)
    
    # Filter out very short fragments
    sentences = [s.strip() for s in raw_sentences if len(s.strip()) > 10]
    
    # Limit to max_scenes
    if len(sentences) > max_scenes:
        # Merge some sentences to fit within limit
        merged = []
        per_scene = len(sentences) / max_scenes
        idx = 0.0
        while idx < len(sentences) and len(merged) < max_scenes:
            end = min(int(idx + per_scene), len(sentences))
            chunk = " ".join(sentences[int(idx):end])
            merged.append(chunk)
            idx = end
        sentences = merged
    
    scenes = []
    for i, sentence in enumerate(sentences):
        prompt = sentence.strip().rstrip('.')
        
        if auto_enhance:
            prompt = enhance_prompt(prompt, style=style)
        
        # Infer duration from sentence complexity
        word_count = len(prompt.split())
        if word_count < 8:
            duration = "short"
        elif word_count > 25:
            duration = "long"
        else:
            duration = "medium"
        
        # Infer camera from keywords
        camera = _infer_camera(prompt)
        mood = _infer_mood(prompt)
        
        # Last scene has no transition
        transition = "crossfade" if i < len(sentences) - 1 else "cut"
        
        scenes.append(Scene(
            index=i,
            prompt=prompt,
            duration_hint=duration,
            camera=camera,
            mood=mood,
            transition_to_next=transition,
        ))
    
    logger.info(f"Story split into {len(scenes)} scenes")
    return scenes


def _parse_structured_story(
    text: str,
    max_scenes: int,
    auto_enhance: bool,
    style: str,
) -> List[Scene]:
    """Parse structured scene format."""
    blocks = text.split("---")
    scenes = []
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        lines = block.split("\n")
        scene_data = {}
        
        for line in lines:
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                scene_data[key.strip().upper()] = value.strip()
        
        # Extract scene prompt
        prompt = ""
        for key in scene_data:
            if "SCENE" in key:
                prompt = scene_data[key]
                break
        
        if not prompt:
            continue
        
        if auto_enhance:
            prompt = enhance_prompt(prompt, style=style)
        
        scenes.append(Scene(
            index=len(scenes),
            prompt=prompt,
            duration_hint=scene_data.get("DURATION", "medium").lower(),
            camera=scene_data.get("CAMERA", _infer_camera(prompt)),
            mood=scene_data.get("MOOD", _infer_mood(prompt)),
            transition_to_next=scene_data.get("TRANSITION", "crossfade").lower(),
        ))
        
        if len(scenes) >= max_scenes:
            break
    
    logger.info(f"Structured story parsed: {len(scenes)} scenes")
    return scenes


def _infer_camera(prompt: str) -> str:
    prompt_lower = prompt.lower()
    
    if any(w in prompt_lower for w in ["close", "face", "eyes", "smile", "expression"]):
        return "close-up"
    elif any(w in prompt_lower for w in ["walk", "run", "street", "city", "landscape", "panorama"]):
        return "wide shot"
    elif any(w in prompt_lower for w in ["stand", "pose", "portrait"]):
        return "medium shot"
    elif any(w in prompt_lower for w in ["aerial", "drone", "bird", "above"]):
        return "aerial shot"
    
    return "medium shot"


def _infer_mood(prompt: str) -> str:
    prompt_lower = prompt.lower()
    
    mood_keywords = {
        "happy": ["smile", "laugh", "joy", "happy", "cheerful", "sunny", "bright"],
        "sad": ["cry", "tear", "sad", "melancholy", "rain", "dark", "alone"],
        "romantic": ["love", "kiss", "romantic", "sunset", "together", "couple"],
        "dramatic": ["dramatic", "intense", "storm", "fight", "conflict"],
        "peaceful": ["calm", "serene", "peaceful", "quiet", "nature", "gentle"],
        "mysterious": ["mystery", "shadow", "fog", "mist", "enigmatic", "secret"],
        "energetic": ["dance", "run", "jump", "energy", "fast", "action", "exciting"],
    }
    
    for mood, keywords in mood_keywords.items():
        if any(w in prompt_lower for w in keywords):
            return mood
    
    return "neutral"


def create_story_summary(scenes: List[Scene]) -> str:
    lines = [f"📖 Story: {len(scenes)} scenes\n"]
    
    for scene in scenes:
        emoji = {
            "happy": "😊", "sad": "😢", "romantic": "💕",
            "dramatic": "🎭", "peaceful": "🌿", "mysterious": "🌫️",
            "energetic": "⚡", "neutral": "🎬"
        }.get(scene.mood, "🎬")
        
        lines.append(
            f"  {emoji} Scene {scene.index + 1} [{scene.duration_hint}] "
            f"({scene.camera}): {scene.prompt[:80]}..."
    """Create a human-readable summary of the story scenes."""
            f" → {scene.transition_to_next}"
        )
    
    return "\n".join(lines)

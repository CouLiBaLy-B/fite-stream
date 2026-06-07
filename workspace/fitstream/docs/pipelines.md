# 🏗️ Pipelines

FitStream includes 5 generation pipelines, each specialized for a different use case.

## 1. Animate Pipeline (`animate.py`)

**Input:** Person image + text prompt  
**Output:** Animated video (3–5 seconds)

```python
from fitstream.core.pipelines.animate import AnimatePipeline

pipeline = AnimatePipeline()
result = pipeline.generate(
    image_path="person.jpg",
    prompt="A person walks through a sunny garden",
    preset="standard",    # draft | standard | high
    style="cinematic",    # cinematic | photorealistic | anime | dreamy | warm | noir
    seed=42,
)
print(result.video_path)  # outputs/animate_1234_42.mp4
```

### How it works
1. Load and resize the reference image to target resolution
2. Enhance prompt with style-specific quality tags
3. Load Wan VACE model (lazy, with VRAM optimization)
4. Generate frames using the diffusion pipeline
5. Save frames as MP4 video

### Quality Presets
| Preset | Resolution | Frames | Steps | ~Time (RTX 4090) |
|--------|-----------|--------|-------|------------------|
| `draft` | 480×320 | 33 | 15 | ~15s |
| `standard` | 832×480 | 49 | 30 | ~45s |
| `high` | 832×480 | 81 | 50 | ~2min |

---

## 2. Story Pipeline (`story.py`)

**Input:** Person image + story text  
**Output:** Multi-scene video with transitions

```python
from fitstream.core.pipelines.story import StoryPipeline

pipeline = StoryPipeline()
result = pipeline.generate(
    image_path="person.jpg",
    story="Marie walks in Paris. She enters a bakery. She watches the sunset.",
    max_scenes=5,
    transition="crossfade",
)
print(f"Scenes: {result.num_scenes_completed}/{len(result.scenes)}")
print(f"Video: {result.final_video_path}")
```

### How it works
1. **Parse** story text into individual scenes (by sentences or structured format)
2. For each scene, **infer** camera angle, mood, and duration
3. **Enhance** each scene prompt with style tags
4. **Generate** each scene as a separate video clip
5. **Concatenate** all clips with transitions (crossfade or cut)

### Structured Scene Format
```
---
SCENE 1: A woman stands on a bridge at sunset
CAMERA: wide shot
MOOD: romantic
DURATION: long
---
SCENE 2: She turns and smiles
CAMERA: close-up
MOOD: happy
DURATION: short
---
```

### Auto-Inferred Properties
| Property | How it's detected |
|----------|-------------------|
| **Camera** | Keywords: "walk/street" → wide, "face/eyes" → close-up, "aerial/drone" → aerial |
| **Mood** | Keywords: "smile/happy" → happy, "rain/dark" → sad, "sunset/love" → romantic |
| **Duration** | Word count: <8 words → short, 8–25 → medium, >25 → long |
| **Transition** | Crossfade between scenes, cut at the end |

---

## 3. Try-On Pipeline (`tryon.py`)

**Input:** Person image + garment image  
**Output:** Video of person wearing the garment

```python
from fitstream.core.pipelines.tryon import TryOnPipeline

pipeline = TryOnPipeline()
result = pipeline.generate(
    person_image="person.jpg",
    garment_image="red_dress.jpg",
    prompt="an elegant red evening dress with lace details",
    category="dress",         # auto | upper | lower | dress | shoes | accessories
    action="walking on a runway, fashion show",
)
```

### Garment Categories
| Category | Keywords | Example |
|----------|----------|---------|
| `upper` | shirt, blouse, jacket, sweater, hoodie | T-shirt, blazer |
| `lower` | pants, jeans, shorts, skirt | Denim jeans |
| `dress` | dress, gown, jumpsuit | Evening gown |
| `shoes` | shoes, boots, sneakers, heels | White sneakers |
| `accessories` | hat, bag, necklace, watch, glasses | Straw hat |

### Multi-Garment Outfit
```python
result = pipeline.generate_outfit(
    person_image="person.jpg",
    garment_images=["jacket.jpg", "jeans.jpg", "sneakers.jpg"],
    garment_descriptions=["leather jacket", "blue jeans", "white sneakers"],
    action="walking confidently in the city",
)
```

---

## 4. Loom Pipeline (`loom.py`)

**Input:** 2–8 reference images + prompt with `@Image N`  
**Output:** Composed video combining all references

```python
from fitstream.core.pipelines.loom import LoomPipeline

pipeline = LoomPipeline()
result = pipeline.generate(
    images=["person.jpg", "dress.jpg", "cafe.jpg"],
    prompt="The woman (@Image 1) wearing the red dress (@Image 2) "
           "sits at the Parisian café (@Image 3), sipping coffee",
    task="mi2v",  # mi2v | t2v | edit | ref_edit
)
```

### Supported Tasks
| Task | Input | Description |
|------|-------|-------------|
| `t2v` | Text only | Text-to-video (no images) |
| `mi2v` | Images + text | Multi-image-to-video (main use case) |
| `edit` | Video + text | Instruction-based video editing |
| `ref_edit` | Video + images + text | Reference-guided editing |

### Reference Validation
The pipeline validates `@Image N` references:
- Warns if images are provided but not referenced
- Warns if references exceed the number of images
- Case-insensitive matching (`@Image`, `@image`, `@IMAGE`)

---

## 5. Extend Pipeline (`extend.py`)

**Input:** Short video + prompt  
**Output:** Longer video (temporal continuation)

```python
from fitstream.core.pipelines.extend import ExtendPipeline

pipeline = ExtendPipeline()
result = pipeline.extend(
    video_path="short_clip.mp4",
    prompt="Continue the scene naturally with smooth motion",
    target_duration=15.0,   # seconds
    overlap_frames=8,       # frames of overlap between chunks
)
print(f"Extended: {result.original_duration:.1f}s → {result.final_duration:.1f}s")
```

### How it works
1. Extract the last frame from the current video
2. Generate a new chunk of frames conditioned on the last frame
3. Skip overlap frames (for smooth transition)
4. Concatenate the new chunk to the video
5. Repeat until target duration is reached

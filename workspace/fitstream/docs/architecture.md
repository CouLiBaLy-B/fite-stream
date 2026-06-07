# 🏗️ Architecture

## Overview

FitStream is organized in four layers: **Frontend → API → Core Engine → AI Models**.

```
User (Browser / CLI / Mobile)
        │
        ▼
┌─── FRONTEND ──────────────────────────────────────────┐
│  index.html — Single-page app with 5 tabs             │
│  Communicates via REST (fetch) + WebSocket (ws://)     │
└───────────────────────┬───────────────────────────────┘
                        │
┌─── API LAYER ─────────▼───────────────────────────────┐
│  FastAPI + Uvicorn                                     │
│                                                        │
│  REST endpoints:                                       │
│    POST /api/v1/animate    (image + prompt → job)      │
│    POST /api/v1/story      (image + story → job)       │
│    POST /api/v1/tryon      (person + garment → job)    │
│    POST /api/v1/compose    (images + prompt → job)     │
│    POST /api/v1/batch/animate (image + N prompts)      │
│    POST /api/v1/analyze    (image → quality report)    │
│    GET  /api/v1/gallery    (paginated completed jobs)  │
│    GET  /api/v1/jobs/{id}  (job status)                │
│    GET  /api/v1/jobs/{id}/video (download mp4)         │
│                                                        │
│  WebSocket:                                            │
│    WS /ws/jobs/{id}        (real-time progress)        │
│                                                        │
│  Background tasks via FastAPI BackgroundTasks           │
└───────────────────────┬───────────────────────────────┘
                        │
┌─── CORE ENGINE ───────▼───────────────────────────────┐
│                                                        │
│  ┌─ Pipelines ─────────────────────────────────────┐   │
│  │  AnimatePipeline   → single-scene video          │   │
│  │  StoryPipeline     → multi-scene + concat        │   │
│  │  TryOnPipeline     → garment swap video          │   │
│  │  LoomPipeline      → multi-image composition     │   │
│  │  ExtendPipeline    → temporal video extension     │   │
│  └──────────────────────────────────────────────────┘   │
│                                                        │
│  ┌─ Supporting Systems ─────────────────────────────┐   │
│  │  ModelManager      → lazy-load, VRAM management  │   │
│  │  JobQueue          → persistent, thread-safe     │   │
│  │  PreprocessingEngine → image analysis, crop      │   │
│  │  PromptUtils       → enhance, split, validate    │   │
│  │  VideoUtils        → save, concat, ffmpeg        │   │
│  │  ImageUtils        → load, resize, grid          │   │
│  └──────────────────────────────────────────────────┘   │
│                                                        │
│  ┌─ AI Models ──────────────────────────────────────┐   │
│  │  Wan VACE 1.3B / 14B  (via HuggingFace Diffusers)│   │
│  │  LoomVideo 5B         (via accelerate CLI)       │   │
│  │  LTX-Video 13B        (via Diffusers)            │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

## Data Flow — Animate Pipeline

```
1. User uploads image + prompt via REST or frontend
2. API saves image to ./uploads/, creates Job in JobQueue
3. BackgroundTask starts AnimatePipeline.generate()
4. Pipeline calls ModelManager.load_vace_diffusers()
   → Lazy-loads model, applies VRAM optimizations
5. Image preprocessed: resize, crop to target resolution
6. Prompt enhanced with style/quality tags
7. Diffusion model generates N frames
8. Frames saved as MP4 via imageio/ffmpeg
9. Job marked completed, video_path stored
10. Frontend polls /jobs/{id} or receives WebSocket push
11. User watches/downloads the generated video
```

## Data Flow — Story Pipeline

```
1. Story text split into scenes by PromptUtils
2. Each scene gets: prompt, duration, camera, mood, transition
3. AnimatePipeline called for each scene sequentially
4. All scene clips concatenated via ffmpeg (with crossfades)
5. Final video saved as single MP4
```

## Memory Management (RTX 4090 — 24GB)

The ModelManager applies these optimizations:
- **CPU Offload**: Model weights moved to CPU when not in use
- **VAE Slicing**: Process VAE in slices to reduce peak VRAM
- **VAE Tiling**: Tile-based VAE decoding for large resolutions
- **T5 on CPU**: Text encoder kept on CPU (saves ~4GB)
- **Single model**: Only one model loaded at a time
- **Aggressive GC**: `torch.cuda.empty_cache()` after each generation

## File Structure

```
fitstream/
├── fitstream/           # Python package
│   ├── __init__.py
│   ├── config.py        # Configuration management
│   ├── cli.py           # CLI entry point
│   ├── api/             # REST API + WebSocket
│   └── core/            # Core logic
│       ├── models/      # Model loading
│       ├── pipelines/   # Generation pipelines
│       ├── utils/       # Shared utilities
│       ├── job_queue.py # Job management
│       └── preprocessing.py
├── frontend/            # Web UI
├── config/              # YAML configs
├── scripts/             # Setup & download scripts
├── tests/               # Test suite
├── docs/                # Documentation
├── models/              # Downloaded model weights (gitignored)
├── outputs/             # Generated videos (gitignored)
└── uploads/             # User uploads (gitignored)
```

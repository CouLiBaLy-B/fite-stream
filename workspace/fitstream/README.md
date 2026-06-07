# 🎬 FitStream

**Transform photos of people into fluid animated stories with AI.**

[![Tests](https://img.shields.io/badge/tests-290%20passed-brightgreen)](#-tests)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](Dockerfile)
[![GPU](https://img.shields.io/badge/GPU-RTX%204090%2B-76B900?logo=nvidia)](docs/deployment.md)
[![API](https://img.shields.io/badge/API-35%2B%20endpoints-orange)](#-api-reference)
[![LOC](https://img.shields.io/badge/LOC-12K%2B-informational)](#)

FitStream takes a **photo of a person** and a **text prompt**, and generates **fluid video animations** — stories, try-on, style transfers, and more. Built on [Wan VACE](https://github.com/ali-vilab/VACE), [LoomVideo](https://github.com/MSALab-PKU/LoomVideo), and state-of-the-art diffusion video models.

---

## ✨ Features

| Category | Features |
|----------|----------|
| **🎬 Generation** | Animate · Story · Try-On · Compose · Extend · Style Transfer |
| **🎨 Styles** | 10 presets (Ghibli, Pixar, Comic, Noir, Cyberpunk, Ukiyo-e, Impressionist, Watercolor, Oil Painting, Vintage Film) + custom |
| **📝 Templates** | 25+ prompt templates in 6 categories (actions, locations, emotions, camera, fashion, story arcs) |
| **📦 Export** | MP4 · GIF · WebM · PNG frames · Storyboard grid · Social media (9:16, 1:1, 4:5) |
| **🎛️ Post-Processing** | Upscale · Stabilize · Color grade (8 presets) · Slow motion · Loop · Watermark · Trim · Chain operations |
| **🔬 A/B Testing** | Compare styles · Compare prompts · Explore seed variations |
| **📈 Analytics** | Trends · Top styles · Generation stats · Hourly distribution · Success rates |
| **📅 Scheduling** | One-shot · Recurring (daily/hourly) · Max runs · Executor callback |
| **🌍 i18n** | 8 languages: English, French, Chinese, Japanese, Spanish, Arabic, Korean, Portuguese |
| **🔧 Infrastructure** | REST API (35+) · WebSocket · Job queue · Gallery · Cache · Plugins · Webhooks · Metrics · Auth |
| **🖥️ Interfaces** | Web UI (4 pages) · Streamlit UI (4 pages) · Monitoring · CLI (7 cmds) · Python SDK · Mobile app · Docker |

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/yourname/fitstream.git && cd fitstream

# 2. Setup (creates venv, installs PyTorch + deps)
bash scripts/setup.sh

# 3. Download AI model (~5GB)
python scripts/download_models.py --model vace-1.3b

# 4. Run the demo (no GPU needed)
PYTHONPATH=. python scripts/demo.py

# 5. Start the server
PYTHONPATH=. python -m fitstream.api.server
# → Web UI:    http://localhost:8000/app
# → API docs:  http://localhost:8000/docs
```

### CLI Examples

```bash
# Animate a person
fitstream animate -i photo.jpg -p "Person walks through a sunlit garden"

# Tell a story
fitstream story -i photo.jpg -s "Marie walks in Paris. She enters a bakery. She watches the sunset."

# Virtual try-on
fitstream tryon -p person.jpg -g dress.jpg --category dress

# Multi-image composition
fitstream compose -i person.jpg -i dress.jpg -i cafe.jpg \
    -p "The woman (@Image 1) wearing (@Image 2) at the café (@Image 3)"

# Check system status
fitstream status
```

### Streamlit Frontend (alternative UI)

```bash
pip install streamlit requests

# Terminal 1: API server
PYTHONPATH=. python -m fitstream.api.server

# Terminal 2: Streamlit
streamlit run streamlit/app.py
# → http://localhost:8501
```

4 pages: Create (7 modes) · Gallery (search + filters) · Monitor (charts) · Settings (i18n, models, real-time status)

### Docker

```bash
docker compose up --build
# → Same URLs as above
```

---

## 🏗️ Architecture

```
User (Browser / CLI / SDK)
        │
        ▼
┌─── FRONTEND ──────────────────────────────────────────────────┐
│  5-tab Web UI (Animate/Story/Try-On/Compose/Gallery)          │
│  WebSocket real-time progress · Dark mode · Responsive        │
└───────────────────────────┬───────────────────────────────────┘
                            │
┌─── API LAYER ─────────────▼───────────────────────────────────┐
│  FastAPI · 25+ endpoints · WebSocket · Rate limiter · Auth    │
│  Request logging · Metrics (p50/p95) · CORS                   │
└───────────────────────────┬───────────────────────────────────┘
                            │
┌─── CORE ENGINE ───────────▼───────────────────────────────────┐
│                                                                │
│  Pipelines (6)          Systems (6)       Infra (5)            │
│  ├─ Animate             ├─ ModelManager   ├─ Plugins           │
│  ├─ Story               ├─ JobQueue       ├─ Webhooks          │
│  ├─ TryOn               ├─ Preprocessing  ├─ Export            │
│  ├─ Loom (multi-img)    ├─ Gallery        ├─ Middleware         │
│  ├─ Extend              ├─ Cache          └─ WebSocket         │
│  └─ StyleTransfer       └─ Templates                           │
│                                                                │
│  Models: Wan VACE 1.3B/14B · LoomVideo 5B · LTX-Video 13B    │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔌 API Reference

### Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/animate` | Photo + prompt → animated video |
| `POST` | `/api/v1/story` | Photo + story → multi-scene video |
| `POST` | `/api/v1/tryon` | Person + garment → try-on video |
| `POST` | `/api/v1/compose` | Multi-image + `@Image N` → composed video |
| `POST` | `/api/v1/style` | Photo + style preset → stylized video |
| `POST` | `/api/v1/batch/animate` | One photo + N prompts → batch videos |

### Utilities

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze` | Image quality analysis & recommendations |
| `POST` | `/api/v1/export/{id}` | Export video (GIF/WebM/storyboard/social) |
| `GET` | `/api/v1/styles` | List available style presets |
| `GET` | `/api/v1/templates` | Browse prompt template library |
| `POST` | `/api/v1/templates/fill` | Fill a template with variables |

### Jobs & Gallery

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/jobs/{id}` | Job status & metadata |
| `GET` | `/api/v1/jobs/{id}/video` | Download video |
| `GET` | `/api/v1/gallery` | Paginated gallery |
| `WS` | `/ws/jobs/{id}` | Real-time progress (WebSocket) |

### Analysis & Testing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/ab/styles` | A/B test: compare multiple styles |
| `GET` | `/api/v1/analytics` | Generation analytics report |
| `GET` | `/api/v1/analytics/top-styles` | Most popular styles |
| `POST` | `/api/v1/postprocess/{id}` | Post-process: upscale, color grade, slow-mo, watermark |
| `GET` | `/api/v1/postprocess/presets` | List color presets & operations |

### Infrastructure

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health + GPU status |
| `GET` | `/api/v1/metrics` | Performance metrics (p50/p95, error rates) |
| `GET` | `/api/v1/analytics` | Generation analytics |
| `POST/GET/DEL` | `/api/v1/webhooks` | Webhook management |
| `GET` | `/api/v1/cache/stats` | Cache hit-rate stats |
| `GET` | `/api/v1/plugins` | Registered plugins |
| `GET` | `/api/v1/schedules` | Scheduled/recurring jobs |
| `GET` | `/api/v1/i18n/{lang}` | UI translations (8 languages) |
| `GET` | `/monitor` | Live monitoring dashboard |

Full reference: [docs/api_reference.md](docs/api_reference.md)

---

## 🎨 Style Presets

| Style | Example Prompt Modifier |
|-------|-------------------------|
| 🏯 **Ghibli** | Studio Ghibli animation, soft pastels, Miyazaki |
| 🧊 **Pixar** | Pixar 3D, smooth render, expressive characters |
| 💥 **Comic** | Bold outlines, cel-shading, halftone dots |
| 🌑 **Noir** | High contrast B&W, dramatic shadows, 1940s |
| 🌆 **Cyberpunk** | Neon lights, rain-slicked streets, holographic |
| 🎌 **Ukiyo-e** | Japanese woodblock print, flat colors, Hokusai |
| 🌸 **Impressionist** | Dappled light, visible brushstrokes, Monet |
| 🎨 **Watercolor** | Soft washes, paper texture, translucent layers |
| 🖼️ **Oil Painting** | Impasto brushstrokes, rich tones, canvas texture |
| 📼 **Vintage Film** | Super 8 grain, warm cast, light leaks, 1970s |

---

## 📝 Prompt Templates

25+ templates in 6 categories — browse with `GET /api/v1/templates`:

```python
# Python usage
from fitstream.core.prompt_templates import PromptTemplateLibrary
lib = PromptTemplateLibrary()

# Fill a template
prompt = lib.get("fashion.runway", person="a model", garment="red gown")
# → "A model walks confidently down a high-fashion runway wearing a red gown..."

# Browse
lib.list_categories()   # ["actions", "camera", "emotions", "fashion", "locations", "story"]
lib.list_templates("camera")  # dolly_in, orbit, low_angle, tracking_walk
lib.search("sunset")    # matching templates
```

---

## 🤖 Supported Models

| Model | Params | VRAM | Quality | Speed | Use Case |
|-------|--------|------|---------|-------|----------|
| **Wan VACE 1.3B** | 1.3B | ~16GB | ★★★☆ | Fast | Default (RTX 4090) |
| **Wan VACE 14B** | 14B | ~48GB | ★★★★★ | Medium | Best quality (A100/H100) |
| **LoomVideo 5B** | 5B | ~40GB | ★★★★ | Medium | Multi-image, fashion |
| **LTX-Video 13B** | 13B | ~12GB | ★★★☆ | Very fast | Prototyping |

```bash
python scripts/download_models.py --model list    # Show all models
python scripts/download_models.py --model vace-1.3b  # Download default
```

---

## 🔌 Plugin System

Extend FitStream with custom pipelines, models, or exporters:

```python
from fitstream.core.plugins import PluginRegistry

@PluginRegistry.pipeline("my_custom_pipeline", description="My custom generation")
class MyPipeline:
    def generate(self, image, prompt, **kwargs):
        # Custom generation logic
        ...
```

Auto-discover plugins from `./plugins/` directory.

---

## 🔬 A/B Testing

Compare multiple variants side by side — styles, prompts, or seed variations:

```bash
# API
curl -X POST http://localhost:8000/api/v1/ab/styles \
  -F "image=@photo.jpg" \
  -F "prompt=Walking in a garden" \
  -F "styles=cinematic,ghibli,noir,cyberpunk"
```

```python
# Python
from fitstream.core.ab_testing import ABTestingPipeline
ab = ABTestingPipeline()
result = ab.explore_variations("photo.jpg", "Fashion walk", num_variations=4)
for v in result.variants:
    print(f"  {v.label}: {v.video_path} ({v.generation_time:.1f}s)")
```

---

## 🎛️ Post-Processing

Apply transformations after generation — chainable operations:

```python
from fitstream.core.postprocessing import PostProcessor
pp = PostProcessor()

# Single operation
pp.color_grade("input.mp4", "cinematic.mp4", preset="cinematic")
pp.upscale("input.mp4", "2x.mp4", factor=2)
pp.slow_motion("input.mp4", "slow.mp4", factor=2.0)

# Chain multiple operations
pp.chain("input.mp4", "final.mp4", [
    {"op": "color_grade", "preset": "cinematic"},
    {"op": "upscale", "factor": 2},
    {"op": "add_watermark", "text": "FitStream"},
])
```

**8 color presets**: warm · cool · vintage · cinematic · vibrant · desaturated · sepia · noir

---

## 📅 Scheduler

Automate recurring generation jobs:

```python
from fitstream.core.scheduler import Scheduler
from datetime import datetime, timedelta

scheduler = Scheduler()
scheduler.set_executor(my_generation_function)

# Daily fashion lookbook
scheduler.schedule_recurring(
    interval_hours=24,
    job_type="story",
    params={"image": "model.jpg", "story": "Today's outfit story..."},
    name="daily-lookbook",
    max_runs=30,
)

scheduler.start()  # Background thread
```

---

## 📈 Analytics

Built-in generation analytics — track trends, popular styles, and performance:

```python
from fitstream.core.analytics import analytics
report = analytics.get_report(hours=24)
# → total_generations, by_type, by_style, generation_time (avg/p50/p95),
#   hourly_distribution, success_rate, top_styles, etc.
```

```bash
# API
curl http://localhost:8000/api/v1/analytics?hours=24
curl http://localhost:8000/api/v1/analytics/top-styles
```

---

## 🌍 Internationalization

8 languages supported for UI messages and prompt translation:

```python
from fitstream.core.i18n import I18n, translate_prompt

# UI messages
i18n = I18n("fr")
print(i18n.t("status.processing"))  # "En cours de génération..."

# Prompt translation
en_prompt = translate_prompt("une femme marche dans une rue", "fr")
# → "A woman walks in a street"
```

Languages: 🇬🇧 EN · 🇫🇷 FR · 🇨🇳 ZH · 🇯🇵 JA · 🇪🇸 ES · 🇸🇦 AR · 🇰🇷 KO · 🇧🇷 PT

---

## 🎞️ Video-to-Video Restyling

Keep motion, change aesthetics — with strength control:

```python
from fitstream.core.pipelines.v2v_restyle import V2VRestylePipeline
pipeline = V2VRestylePipeline()
result = pipeline.restyle(
    video_path="original.mp4",
    style="ghibli",
    strength=0.7,        # 0=no change, 1=full restyle
    preserve_faces=True,
)
```

Recommended strengths: subtle (0.3-0.5) · moderate (0.5-0.7) · strong (0.6-0.8) · extreme (0.7-0.9)

---

## 🏋️ LoRA Fine-Tuning

Train custom adapters on your own person/style (5-50 images):

```python
from fitstream.core.lora_trainer import LoRATrainer
trainer = LoRATrainer()

config = trainer.create_config(
    name="my-person",
    trigger_word="ohwx person",
    training_images=["p1.jpg", "p2.jpg", "p3.jpg", "p4.jpg", "p5.jpg"],
    num_steps=1000,
    lora_rank=16,
)
result = trainer.train(config)
# → Generates training script + dataset in ./loras/my-person/
```

---

## 👤 Multi-User System

User accounts with API keys, quotas, and sharing:

```python
from fitstream.core.users import UserManager
users = UserManager()

# Register
user, api_key = users.register("alice", email="alice@test.com", daily_limit=50)
# → api_key = "fs_abc123..."

# Authenticate
user = users.authenticate(api_key)

# Check quota
users.check_quota(user.id)      # → True/False
users.get_remaining_quota(user.id)  # → {"daily_remaining": 48, ...}

# Share a video publicly
share = users.create_share(user.id, "job_abc", "/video.mp4", expires_hours=24)
# → share.share_url = "/shared/xyz..."
```

---

## 🛒 E-Commerce Integration

Auto-generate try-on videos for your product catalog:

```python
from fitstream.core.ecommerce import ECommerceConnector, ECommerceConfig

config = ECommerceConfig(
    platform="shopify",
    shop_url="myshop.myshopify.com",
    default_model_image="model.jpg",
)
connector = ECommerceConnector(config)

# Ingest a product (from webhook or API)
product = connector.ingest_product({
    "id": 12345, "title": "Blue Cotton T-Shirt",
    "product_type": "tops",
    "images": [{"src": "https://cdn.shopify.com/shirt.jpg"}],
})

# Generate try-on video for this product
connector.generate_product_video(product.id)

# Batch generate for entire catalog
connector.generate_catalog(model_image="model.jpg", max_products=50)
```

---

## 📱 Mobile API

Lightweight endpoints at `/m/` for mobile apps:

```bash
# Status (single call)
GET /m/status → {"ok": true, "gpu": true, "active_jobs": 1}

# Generate (supports base64 image upload)
POST /m/generate  image=@photo.jpg  prompt="Walking in Paris"  mode=animate

# Compact job status
GET /m/job/{id} → {"id": "m-abc", "status": "done", "video_url": "/api/v1/jobs/..."}

# Paginated gallery
GET /m/gallery?page=0&size=12

# Flat style list
GET /m/styles → [{"id": "ghibli", "name": "Studio Ghibli"}, ...]
```

---

## 📊 Monitoring Dashboard

Real-time monitoring at `/monitor` — auto-refreshes every 5 seconds:

- 🖥️ GPU memory (free/used/total)
- 📊 Request rates and error rates
- ⏱️ Latencies per endpoint (p50/p95)
- 📈 Generations by type (bar chart)
- 📦 Cache hit rate
- 📋 Recent jobs table

---

## 🧪 Tests

```bash
PYTHONPATH=. python -m pytest tests/ -v          # All 290 tests
PYTHONPATH=. python scripts/demo.py              # E2E demo (no GPU)
```

**290 tests** across 28 suites: API, config, export, gallery, job queue, multi-image, middleware, preprocessing, prompts, style transfer, try-on, plugins, templates, cache, webhooks, i18n, post-processing, SDK, scheduler, analytics, A/B testing, V2V restyling, LoRA trainer, multi-user accounts, e-commerce, LoomVideo native, mobile API.

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [Architecture](docs/architecture.md) | System design, data flow, memory management |
| [API Reference](docs/api_reference.md) | All endpoints with examples |
| [Pipelines](docs/pipelines.md) | How each generation pipeline works |
| [Models](docs/models.md) | Supported models, VRAM guide, download |
| [Deployment](docs/deployment.md) | Local / Docker / Cloud deployment |
| [Contributing](CONTRIBUTING.md) | How to contribute |
| [Changelog](CHANGELOG.md) | Version history |

---

## 🗺️ Roadmap

### ✅ Completed

- [x] 6 generation pipelines (animate, story, tryon, compose, extend, style transfer)
- [x] 35+ API endpoints (REST + WebSocket)
- [x] Web frontend (5 tabs) + monitoring dashboard
- [x] Docker + CI/CD (GitHub Actions — lint, test, build, release)
- [x] Job queue with disk persistence + scheduler (one-shot & recurring)
- [x] Gallery with auto-thumbnails, search, favorites, collections, tags
- [x] 10 artistic styles + 25+ prompt templates (6 categories)
- [x] Export pipeline (GIF, WebM, storyboard, social 9:16/1:1/4:5)
- [x] Plugin system (decorator registration + auto-discovery)
- [x] Webhooks (HMAC-signed, retry, async delivery)
- [x] Generation cache (LRU, persistent, TTL, hit-rate monitoring)
- [x] Rate limiting + API key auth + request logging middleware
- [x] Internationalization — 8 languages (EN/FR/ZH/JA/ES/AR/KO/PT)
- [x] Video post-processing (upscale, stabilize, color grade, slow-mo, loop, watermark, trim, chain)
- [x] Python SDK client library (sync, with polling + download)
- [x] Monitoring dashboard (auto-refresh, GPU/metrics/jobs/cache)
- [x] A/B testing (compare styles, prompts, seed variations)
- [x] Analytics engine (trends, top styles, generation stats, hourly distribution)
- [x] Scheduling (one-shot + recurring with max-runs + executor callback)
- [x] Image preprocessing (quality analysis, auto-crop, garment preparation)
- [x] 234 tests across 21 test suites

- [x] Video-to-video restyling with motion preservation (strength control, frame blending)
- [x] LoRA fine-tuning interface (config, dataset prep, training script generation)
- [x] Multi-user accounts (registration, API keys, quotas, sharing, persistence)
- [x] Native LoomVideo multi-image integration (3-tier: native → Diffusers → VACE fallback)
- [x] Mobile-optimized API (`/m/` — base64 upload, compact responses, pagination)
- [x] E-commerce connector (product ingestion, auto try-on, catalog batch, webhook verification)
- [x] FashionChameleon real-time interface (ready to activate when weights released, fallback mode active)
- [x] Mobile app (React Native / Expo — 3 screens, API client, glassmorphism design)
- [x] 290 tests across 28 test suites

### 🎯 Roadmap Status: ✅ COMPLETE

All planned features have been implemented. Remaining items depend on external factors:
- FashionChameleon weights: auto-activates when Alibaba publishes them (set `FITSTREAM_REALTIME_WEIGHTS_PATH`)
- Mobile deployment: run `cd mobile && npx expo start` to launch on device

---

## 📄 License

MIT — see [LICENSE](LICENSE).

## 🙏 Acknowledgments

Built on research from: [Wan VACE](https://github.com/ali-vilab/VACE) · [LoomVideo](https://github.com/MSALab-PKU/LoomVideo) · [Eevee](https://github.com/AMAP-ML/Eevee) · [OmniVTON](https://github.com/Jerome-Young/OmniVTON) · [iTryOn](https://zhengjun-ai.github.io/itryon-page/) · [TurboDiffusion](https://github.com/ShengShu-Tech/TurboDiffusion)

# 🔌 API Reference

Base URL: `http://localhost:8000`

## Health & Status

### `GET /health`
Health check with GPU information.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0",
  "gpu": {
    "available": true,
    "gpu_name": "NVIDIA GeForce RTX 4090",
    "total_gb": 24.0,
    "free_gb": 18.5,
    "used_gb": 5.5,
    "utilization_pct": 22.9
  }
}
```

### `GET /gpu`
GPU memory status only.

---

## Generation Endpoints

### `POST /api/v1/animate`
Generate an animated video from a person photo + text prompt.

**Form fields:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `image` | file | ✅ | — | Person image (JPG/PNG) |
| `prompt` | string | ✅ | — | Animation description |
| `style` | string | | `cinematic` | `cinematic`, `photorealistic`, `anime`, `dreamy`, `warm`, `noir` |
| `preset` | string | | `standard` | `draft` (~15s), `standard` (~45s), `high` (~2min) |
| `seed` | int | | `-1` | Random seed (`-1` = random) |
| `num_frames` | int | | `49` | Frames to generate (16–128) |
| `num_inference_steps` | int | | `30` | Denoising steps (5–100) |

**Response:**
```json
{
  "job_id": "a1b2c3d4",
  "status": "queued",
  "prompt_used": "Cinematic shot, A person walks..."
}
```

**cURL example:**
```bash
curl -X POST http://localhost:8000/api/v1/animate \
  -F "image=@photo.jpg" \
  -F "prompt=A person walks through a sunlit garden" \
  -F "style=cinematic" \
  -F "preset=standard"
```

---

### `POST /api/v1/story`
Generate a multi-scene story video.

**Form fields:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `image` | file | ✅ | — | Character image |
| `story` | string | ✅ | — | Story text (auto-split into scenes) |
| `style` | string | | `cinematic` | Visual style |
| `preset` | string | | `standard` | Quality preset |
| `max_scenes` | int | | `5` | Maximum scenes (1–8) |
| `transition` | string | | `crossfade` | `none` or `crossfade` |

The story text is automatically split into scenes using sentence boundaries. You can also use structured format:

```
---
SCENE 1: Description
CAMERA: wide shot
MOOD: romantic
DURATION: long
---
```

---

### `POST /api/v1/tryon`
Virtual try-on: generate a video of a person wearing a new garment.

**Form fields:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `person_image` | file | ✅ | — | Person photo |
| `garment_image` | file | ✅ | — | Garment/clothing photo |
| `prompt` | string | | `""` | Garment description (auto-detected if empty) |
| `category` | string | | `auto` | `auto`, `upper`, `lower`, `dress`, `shoes`, `accessories` |
| `action` | string | | `walking naturally...` | What the person does |
| `style` | string | | `cinematic` | Visual style |
| `preset` | string | | `standard` | Quality |

---

### `POST /api/v1/compose`
Multi-image composition using `@Image N` references.

**Form fields:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `images` | file[] | ✅ | — | 2–8 reference images |
| `prompt` | string | ✅ | — | Prompt with `@Image 1`, `@Image 2`, etc. |
| `style` | string | | `cinematic` | Visual style |
| `seed` | int | | `-1` | Random seed |
| `num_frames` | int | | `97` | Frames to generate |

**Example prompt:**
```
The woman (@Image 1) wearing the red dress (@Image 2) 
walks through the beautiful garden (@Image 3)
```

---

### `POST /api/v1/batch/animate`
Generate multiple videos from one image with different prompts.

**Form fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `image` | file | ✅ | Person image |
| `prompts` | string | ✅ | Prompts separated by `\|\|\|` |
| `style` | string | | Visual style |
| `preset` | string | | Quality (recommend `draft` for batch) |

**Example:**
```
Walking in the rain ||| Dancing in the sun ||| Reading a book
```

---

### `POST /api/v1/analyze`
Analyze image quality before generation.

**Response:**
```json
{
  "width": 800,
  "height": 1200,
  "brightness": 128.5,
  "contrast": 45.2,
  "sharpness": 350.0,
  "has_person": true,
  "quality_score": 0.85,
  "issues": [],
  "recommendations": [],
  "report": "🟢 Quality: Excellent (85%)..."
}
```

---

## Job Management

### `GET /api/v1/jobs/{job_id}`
Get job status and metadata.

### `GET /api/v1/jobs/{job_id}/video`
Download the generated video (MP4).

### `GET /api/v1/jobs`
List all jobs.

### `GET /api/v1/gallery?limit=20&offset=0`
Paginated gallery of completed jobs.

---

## WebSocket

### `WS /ws/jobs/{job_id}`
Real-time progress updates for a specific job.

**Messages received:**
```json
{"type": "progress", "status": "processing", "progress": 0.5, "message": "Generating frames..."}
{"type": "completed", "video_url": "/api/v1/jobs/abc123/video", "generation_time": 42.5}
{"type": "error", "error": "GPU out of memory"}
```

**JavaScript example:**
```javascript
const ws = new WebSocket(`ws://localhost:8000/ws/jobs/${jobId}`);
ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    if (data.type === 'completed') showVideo(data.video_url);
    if (data.type === 'progress') updateProgressBar(data.progress);
};
```

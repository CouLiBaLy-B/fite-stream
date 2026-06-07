# 🎬 FitStream — Streamlit Frontend

Full-featured Streamlit frontend for the FitStream AI video platform.

## Quick Start

```bash
# Install streamlit
pip install streamlit requests

# Start the FitStream API server (in another terminal)
cd fitstream
PYTHONPATH=. python -m fitstream.api.server

# Start the Streamlit frontend
streamlit run streamlit/app.py
```

Open `http://localhost:8501` in your browser.

## Pages

### 🎬 Create
- **7 generation modes**: Animate, Story, Try-On, Style Transfer, Multi-Image Compose, A/B Test, Real-Time
- Image upload with preview
- 25+ prompt templates (auto-loaded from API)
- 10 artistic style selectors
- Quality presets (draft / standard / high)
- Real-time job polling with progress bar
- Video playback + export options (GIF, WebM, storyboard, vertical)

### 🖼️ Gallery
- Browse all generated videos
- Filter by type (animate, story, tryon, style, compose)
- Search prompts
- Sort by newest/oldest
- Video player for each result

### 📊 Monitor
- GPU memory usage with progress bar
- Request metrics (total, error rate, avg gen time, uptime)
- Generations by type (bar chart)
- Endpoint latencies (bar chart)
- Cache stats (entries, hit rate, size)
- Recent jobs table
- Optional auto-refresh (5s)

### ⚙️ Settings
- Server URL configuration with connection test
- Language selector (8 languages)
- Model info (VRAM requirements)
- Real-time mode status (FashionChameleon)
- Available styles & templates overview
- About section

## Architecture

```
streamlit/
├── app.py                    # Main Streamlit application (single file)
├── .streamlit/
│   └── config.toml          # Theme config (dark glassmorphism)
└── README.md
```

The Streamlit app connects to the FitStream API server via HTTP.
All 46 endpoints are accessible through the interface.

## Configuration

The app reads the API server URL from session state.
Default: `http://localhost:8000`

Change it in the Settings page or pass as argument:
```bash
streamlit run streamlit/app.py
```

## Features vs HTML Frontend

| Feature | HTML Frontend | Streamlit Frontend |
|---------|:---:|:---:|
| Generation modes | 5 | 7 (+ A/B test, real-time) |
| Prompt templates | Manual select | Auto-loaded from API |
| Gallery search | Basic | Full-text + filters |
| Monitoring charts | JS bars | Streamlit native charts |
| Export | Buttons | Integrated |
| Settings | No | Full page |
| Mobile responsive | Yes | Limited |
| Requires install | No | `pip install streamlit` |

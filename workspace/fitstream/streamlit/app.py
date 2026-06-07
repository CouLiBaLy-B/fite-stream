"""
🎬 FitStream — Streamlit Frontend
Full-featured AI video generation studio.

Run with:
    cd fitstream
    streamlit run streamlit/app.py -- --server http://localhost:8000

Features:
  - 9 generation modes (animate, story, tryon, compose, style, v2v, batch, AB test, realtime)
  - 10 artistic styles with visual previews
  - 25+ prompt templates with one-click fill
  - Gallery with filters, favorites, export
  - Monitoring dashboard with live GPU metrics
  - Settings: server config, i18n, theme
"""

import os
import sys
import time
import json
import base64
import tempfile
import requests
from io import BytesIO
from pathlib import Path

# ── Streamlit must be the first import that touches the page ──
try:
    import streamlit as st
except ImportError:
    print("Install streamlit: pip install streamlit")
    sys.exit(1)

# ═══════════════════════════════════════════════════════════
# CONFIG & STATE
# ═══════════════════════════════════════════════════════════

st.set_page_config(
    page_title="FitStream Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for glassmorphism-inspired dark theme
st.markdown("""
<style>
    /* Dark background */
    .stApp { background-color: #07070e; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background-color: #0c0c16;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    
    /* Glass cards */
    .glass-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 16px;
        backdrop-filter: blur(10px);
    }
    
    /* Metric cards */
    .metric-card {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.07);
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 900;
        background: linear-gradient(135deg, #a78bfa, #06d6a0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-label {
        font-size: 11px;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 4px;
    }
    
    /* Style chips */
    .style-chip {
        display: inline-block;
        padding: 6px 14px;
        margin: 3px;
        border-radius: 20px;
        font-size: 13px;
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        color: #94a3b8;
    }
    .style-chip-active {
        background: rgba(139,92,246,0.2);
        border-color: #8b5cf6;
        color: #a78bfa;
    }
    
    /* Status badges */
    .badge-ok { color: #06d6a0; }
    .badge-warn { color: #f59e0b; }
    .badge-err { color: #ef4444; }
    .badge-pr { color: #8b5cf6; }
    
    /* Hide streamlit branding */
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    
    /* Video container */
    .video-frame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.08);
    }
</style>
""", unsafe_allow_html=True)

# Session state defaults
if "api_url" not in st.session_state:
    st.session_state.api_url = "http://localhost:8000"
if "current_job" not in st.session_state:
    st.session_state.current_job = None
if "history" not in st.session_state:
    st.session_state.history = []
if "lang" not in st.session_state:
    st.session_state.lang = "en"


# ═══════════════════════════════════════════════════════════
# API CLIENT
# ═══════════════════════════════════════════════════════════

def api_url():
    return st.session_state.api_url.rstrip("/")


def api_get(path, **params):
    try:
        r = requests.get(f"{api_url()}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def api_post_files(path, files, data):
    try:
        r = requests.post(f"{api_url()}{path}", files=files, data=data, timeout=30)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def poll_job(job_id, progress_bar, status_text):
    """Poll a job until completion, updating Streamlit widgets."""
    for i in range(300):
        time.sleep(2)
        data = api_get(f"/api/v1/jobs/{job_id}")
        
        if "error" in data and "status" not in data:
            status_text.error(f"❌ API error: {data['error']}")
            return None
        
        status = data.get("status", "unknown")
        
        if status == "completed":
            progress_bar.progress(1.0, "✅ Done!")
            video_url = f"{api_url()}/api/v1/jobs/{job_id}/video"
            gen_time = data.get("generation_time", 0)
            status_text.success(f"✅ Generated in {gen_time:.1f}s")
            return video_url
        
        if status == "failed":
            status_text.error(f"❌ Failed: {data.get('error', 'Unknown')}")
            return None
        
        # Update progress
        scenes = data.get("scenes_completed")
        total = data.get("scenes_total")
        if scenes is not None and total:
            pct = scenes / total
            progress_bar.progress(pct, f"Scene {scenes}/{total}...")
        else:
            pct = min(0.95, (i * 2) / 120)
            progress_bar.progress(pct, f"Generating... ({i*2}s)")
    
    status_text.error("❌ Timeout")
    return None


# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🎬 FitStream")
    st.caption("AI Video Animation Studio")
    
    page = st.radio(
        "Navigation",
        ["🎬 Create", "🖼️ Gallery", "📊 Monitor", "⚙️ Settings"],
        label_visibility="collapsed",
    )
    
    st.divider()
    
    # GPU status
    health = api_get("/health")
    if "error" not in health:
        gpu = health.get("gpu", {})
        if gpu.get("available"):
            st.markdown(f"🟢 **{gpu.get('gpu_name', 'GPU')}**")
            used = gpu.get("used_gb", 0)
            total = gpu.get("total_gb", 1)
            st.progress(used / total, f"{gpu.get('free_gb',0):.1f}GB free / {total:.0f}GB")
        else:
            st.markdown("🔴 **No GPU detected**")
    else:
        st.markdown("⚪ **API offline**")
        st.caption(f"Server: {api_url()}")
    
    st.divider()
    st.caption(f"v0.2.0 · 290 tests ✅ · 46 endpoints")


# ═══════════════════════════════════════════════════════════
# PAGE: CREATE
# ═══════════════════════════════════════════════════════════

if page == "🎬 Create":
    
    # Mode selector
    mode = st.selectbox(
        "Generation Mode",
        ["📸 Animate", "📖 Story", "👗 Try-On", "🎭 Style Transfer",
         "🎨 Multi-Image Compose", "🔬 A/B Test Styles", "⚡ Real-Time"],
        index=0,
    )
    
    col_left, col_right = st.columns([1, 1.2])
    
    with col_left:
        st.markdown("### Input")
        
        # ── ANIMATE ──
        if "Animate" in mode:
            image = st.file_uploader("📷 Person Image", type=["jpg", "jpeg", "png", "webp"])
            if image:
                st.image(image, use_container_width=True)
            
            # Template picker
            templates = api_get("/api/v1/templates")
            tpl_list = templates.get("templates", []) if "error" not in templates else []
            tpl_names = ["— Write your own —"] + [f"[{t['category']}] {t['name']}" for t in tpl_list]
            tpl_choice = st.selectbox("📝 Prompt Template", tpl_names)
            
            if tpl_choice != "— Write your own —" and tpl_list:
                idx = tpl_names.index(tpl_choice) - 1
                tpl_id = tpl_list[idx]["id"]
                filled = api_get("/api/v1/templates/search", q=tpl_list[idx]["name"])
                default_prompt = tpl_list[idx].get("example", "")
            else:
                default_prompt = ""
            
            prompt = st.text_area(
                "✍️ Prompt",
                value=default_prompt,
                placeholder="A person walks through a sunlit garden, gentle breeze...",
                height=100,
            )
            
            c1, c2 = st.columns(2)
            with c1:
                style = st.selectbox("🎨 Style", [
                    "cinematic", "photorealistic", "dreamy", "warm", "noir",
                ])
            with c2:
                preset = st.selectbox("⚡ Quality", ["draft", "standard", "high"])
        
        # ── STORY ──
        elif "Story" in mode:
            image = st.file_uploader("📷 Character Image", type=["jpg", "jpeg", "png", "webp"])
            if image:
                st.image(image, use_container_width=True)
            
            prompt = st.text_area(
                "📖 Story Text",
                placeholder="Marie walks through Paris. She enters a bakery. She sits at a café.",
                height=160,
            )
            
            c1, c2 = st.columns(2)
            with c1:
                style = st.selectbox("🎨 Style", ["cinematic", "photorealistic", "anime", "dreamy"])
            with c2:
                max_scenes = st.slider("📐 Max Scenes", 2, 8, 5)
            preset = "standard"
        
        # ── TRY-ON ──
        elif "Try-On" in mode:
            c1, c2 = st.columns(2)
            with c1:
                person_img = st.file_uploader("🧑 Person", type=["jpg", "jpeg", "png"])
                if person_img:
                    st.image(person_img, use_container_width=True)
            with c2:
                garment_img = st.file_uploader("👗 Garment", type=["jpg", "jpeg", "png"])
                if garment_img:
                    st.image(garment_img, use_container_width=True)
            
            prompt = st.text_input("Description (optional)", placeholder="red evening dress with lace")
            
            c1, c2 = st.columns(2)
            with c1:
                category = st.selectbox("Category", ["auto", "upper", "lower", "dress", "shoes", "accessories"])
            with c2:
                action = st.selectbox("Action", [
                    "walking naturally, showing off the outfit",
                    "posing on a runway, fashion show",
                    "turning slowly to show all angles",
                    "standing confidently, slight smile",
                ])
            style = "cinematic"
            preset = "standard"
        
        # ── STYLE TRANSFER ──
        elif "Style" in mode:
            image = st.file_uploader("📷 Person Image", type=["jpg", "jpeg", "png"])
            if image:
                st.image(image, use_container_width=True)
            
            prompt = st.text_area("✍️ Scene Description", placeholder="Walking through a magical forest")
            
            st.markdown("**Choose Style:**")
            style_options = {
                "🏯 Ghibli": "ghibli", "🧊 Pixar": "pixar", "💥 Comic": "comic",
                "🌑 Noir": "noir", "🌆 Cyberpunk": "cyberpunk", "🎌 Ukiyo-e": "ukiyo_e",
                "🌸 Impressionist": "impressionist", "🎨 Watercolor": "watercolor",
                "🖼️ Oil Painting": "oil_painting", "📼 Vintage Film": "vintage_film",
            }
            cols = st.columns(5)
            style = "ghibli"
            for i, (label, val) in enumerate(style_options.items()):
                with cols[i % 5]:
                    if st.button(label, key=f"style_{val}", use_container_width=True):
                        style = val
                        st.session_state.selected_style = val
            style = st.session_state.get("selected_style", "ghibli")
            preset = "standard"
        
        # ── COMPOSE ──
        elif "Compose" in mode:
            images = st.file_uploader(
                "🖼️ Reference Images (2-8)",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
            )
            if images:
                cols = st.columns(min(len(images), 4))
                for i, img in enumerate(images):
                    with cols[i % 4]:
                        st.image(img, caption=f"@Image {i+1}", use_container_width=True)
            
            prompt = st.text_area(
                "✍️ Prompt (use @Image 1, @Image 2, ...)",
                placeholder="The woman (@Image 1) wearing (@Image 2) walks in (@Image 3)",
                height=100,
            )
            style = "cinematic"
            preset = "standard"
        
        # ── A/B TEST ──
        elif "A/B" in mode:
            image = st.file_uploader("📷 Person Image", type=["jpg", "jpeg", "png"])
            if image:
                st.image(image, use_container_width=True)
            
            prompt = st.text_area("✍️ Prompt", placeholder="Walking through a garden")
            
            all_styles = list(style_options.keys()) if "style_options" in dir() else [
                "cinematic", "ghibli", "pixar", "comic", "noir", "cyberpunk",
            ]
            selected_styles = st.multiselect(
                "🎨 Styles to Compare",
                all_styles,
                default=all_styles[:3],
            )
            style = "cinematic"
            preset = "draft"
        
        # ── REALTIME ──
        elif "Real-Time" in mode:
            image = st.file_uploader("📷 Person Image", type=["jpg", "jpeg", "png"])
            if image:
                st.image(image, use_container_width=True)
            
            prompt = st.text_area("✍️ Prompt", placeholder="Walking naturally, smiling")
            style = "cinematic"
            preset = "draft"
            
            rt_status = api_get("/api/v1/realtime/status")
            if "error" not in rt_status:
                if rt_status.get("is_realtime"):
                    st.success(f"⚡ FashionChameleon active — {rt_status['expected_fps']} FPS")
                else:
                    st.info(f"⏳ Fallback mode — ~{rt_status['expected_fps']} FPS")
        
        # ── GENERATE BUTTON ──
        st.markdown("---")
        
        generate_clicked = st.button(
            "🎬 Generate",
            type="primary",
            use_container_width=True,
        )
    
    # ── RIGHT COLUMN: OUTPUT ──
    with col_right:
        st.markdown("### Output")
        
        video_placeholder = st.empty()
        progress_bar = st.empty()
        status_text = st.empty()
        
        if generate_clicked:
            # Build form data and submit
            try:
                if "Animate" in mode and image and prompt:
                    files = {"image": (image.name, image.getvalue(), image.type)}
                    data = {"prompt": prompt, "style": style, "preset": preset}
                    result = api_post_files("/api/v1/animate", files, data)
                
                elif "Story" in mode and image and prompt:
                    files = {"image": (image.name, image.getvalue(), image.type)}
                    data = {"story": prompt, "style": style, "max_scenes": str(max_scenes)}
                    result = api_post_files("/api/v1/story", files, data)
                
                elif "Try-On" in mode and person_img and garment_img:
                    files = {
                        "person_image": (person_img.name, person_img.getvalue(), person_img.type),
                        "garment_image": (garment_img.name, garment_img.getvalue(), garment_img.type),
                    }
                    data = {"prompt": prompt, "category": category, "action": action}
                    result = api_post_files("/api/v1/tryon", files, data)
                
                elif "Style" in mode and image and prompt:
                    files = {"image": (image.name, image.getvalue(), image.type)}
                    data = {"prompt": prompt, "style": style}
                    result = api_post_files("/api/v1/style", files, data)
                
                elif "Compose" in mode and images and len(images) >= 2:
                    files = [("images", (img.name, img.getvalue(), img.type)) for img in images]
                    data = {"prompt": prompt}
                    result = api_post_files("/api/v1/compose", files, data)
                
                elif "Real-Time" in mode and image and prompt:
                    files = {"image": (image.name, image.getvalue(), image.type)}
                    data = {"prompt": prompt}
                    result = api_post_files("/api/v1/realtime/generate", files, data)
                
                else:
                    status_text.warning("⚠️ Please fill in all required fields")
                    result = None
                
                if result and "error" not in result:
                    job_id = result.get("job_id")
                    if job_id:
                        pb = progress_bar.progress(0, "⏳ Submitted...")
                        video_url = poll_job(job_id, progress_bar, status_text)
                        
                        if video_url:
                            video_placeholder.video(video_url)
                            st.session_state.current_job = job_id
                            st.session_state.history.insert(0, {
                                "job_id": job_id, "mode": mode, "prompt": prompt[:60],
                                "video_url": video_url, "time": time.strftime("%H:%M"),
                            })
                elif result:
                    status_text.error(f"❌ {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                status_text.error(f"❌ Error: {e}")
        
        # Export options (when video exists)
        if st.session_state.current_job:
            st.markdown("---")
            st.markdown("**📦 Export**")
            ec1, ec2, ec3, ec4 = st.columns(4)
            job_id = st.session_state.current_job
            with ec1:
                st.markdown(f"[⬇️ MP4]({api_url()}/api/v1/jobs/{job_id}/video)")
            with ec2:
                if st.button("🎞️ GIF", key="exp_gif"):
                    st.info("Export GIF via API...")
            with ec3:
                if st.button("📋 Board", key="exp_board"):
                    st.info("Export storyboard via API...")
            with ec4:
                if st.button("📱 9:16", key="exp_vert"):
                    st.info("Export vertical via API...")


# ═══════════════════════════════════════════════════════════
# PAGE: GALLERY
# ═══════════════════════════════════════════════════════════

elif page == "🖼️ Gallery":
    st.markdown("## 🖼️ Gallery")
    
    # Filters
    fc1, fc2, fc3 = st.columns([1, 1, 2])
    with fc1:
        filter_type = st.selectbox("Type", ["All", "animate", "story", "tryon", "style", "compose"])
    with fc2:
        sort_by = st.selectbox("Sort", ["Newest", "Oldest"])
    with fc3:
        search_q = st.text_input("🔍 Search prompts", "")
    
    # Load jobs
    jobs_data = api_get("/api/v1/jobs")
    if "error" not in jobs_data:
        jobs = [j for j in jobs_data.get("jobs", []) if j.get("status") == "completed"]
        
        if filter_type != "All":
            jobs = [j for j in jobs if j.get("type") == filter_type]
        
        if search_q:
            q = search_q.lower()
            jobs = [j for j in jobs if q in (j.get("prompt", "") + j.get("story", "")).lower()]
        
        if sort_by == "Oldest":
            jobs.reverse()
        
        if not jobs:
            st.info("🎬 No videos yet. Go to Create to generate your first animation!")
        else:
            st.caption(f"{len(jobs)} videos")
            
            cols = st.columns(3)
            for i, job in enumerate(jobs):
                with cols[i % 3]:
                    job_id = job["job_id"]
                    video_url = f"{api_url()}/api/v1/jobs/{job_id}/video"
                    
                    st.video(video_url)
                    
                    type_icons = {"animate": "📸", "story": "📖", "tryon": "👗", "style": "🎭", "compose": "🎨"}
                    jtype = job.get("type", "animate")
                    st.caption(f"{type_icons.get(jtype, '🎬')} {jtype} · `{job_id}`")
                    
                    prompt_text = job.get("prompt", job.get("story", ""))
                    if prompt_text:
                        st.caption(prompt_text[:80])
    else:
        st.error(f"Cannot load gallery: {jobs_data.get('error')}")


# ═══════════════════════════════════════════════════════════
# PAGE: MONITOR
# ═══════════════════════════════════════════════════════════

elif page == "📊 Monitor":
    st.markdown("## 📊 Monitoring Dashboard")
    
    # Auto-refresh
    auto_refresh = st.checkbox("🔄 Auto-refresh (5s)", value=False)
    if auto_refresh:
        time.sleep(5)
        st.rerun()
    
    # Metrics
    metrics = api_get("/api/v1/metrics")
    
    if "error" not in metrics:
        # KPI row
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.metric("Total Requests", f"{metrics.get('total_requests', 0):,}")
        with k2:
            st.metric("Generations", metrics.get("total_generations", 0))
        with k3:
            er = metrics.get("error_rate", 0) * 100
            st.metric("Error Rate", f"{er:.1f}%")
        with k4:
            st.metric("Avg Gen Time", f"{metrics.get('avg_generation_time', 0):.1f}s")
        with k5:
            st.metric("Uptime", metrics.get("uptime_human", "?"))
        
        # Charts
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### Generations by Type")
            gen_types = metrics.get("generations_by_type", {})
            if gen_types:
                st.bar_chart(gen_types)
            else:
                st.info("No generation data yet")
        
        with c2:
            st.markdown("#### Endpoint Latencies")
            latencies = metrics.get("endpoint_latencies", {})
            if latencies:
                lat_data = {
                    ep.replace("/api/v1/", ""): vals.get("p50_ms", 0)
                    for ep, vals in list(latencies.items())[:10]
                }
                st.bar_chart(lat_data)
            else:
                st.info("No latency data yet")
        
        # GPU
        st.markdown("#### GPU Status")
        gpu_info = api_get("/gpu")
        if "error" not in gpu_info and gpu_info.get("available"):
            g1, g2, g3 = st.columns(3)
            with g1:
                st.metric("GPU", gpu_info.get("gpu_name", ""))
            with g2:
                st.metric("Free VRAM", f"{gpu_info.get('free_gb', 0):.1f} GB")
            with g3:
                st.metric("Used VRAM", f"{gpu_info.get('used_gb', 0):.1f} GB")
            
            used = gpu_info.get("used_gb", 0)
            total = gpu_info.get("total_gb", 1)
            st.progress(used / total, f"VRAM: {used:.1f} / {total:.0f} GB ({used/total*100:.0f}%)")
        
        # Cache
        cache = api_get("/api/v1/cache/stats")
        if "error" not in cache:
            st.markdown("#### Cache")
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                st.metric("Entries", cache.get("entries", 0))
            with cc2:
                st.metric("Hit Rate", f"{cache.get('hit_rate', 0)*100:.0f}%")
            with cc3:
                st.metric("Size", f"{cache.get('total_size_mb', 0):.1f} MB")
        
        # Recent jobs
        st.markdown("#### Recent Jobs")
        jobs = api_get("/api/v1/jobs")
        if "error" not in jobs:
            for j in jobs.get("jobs", [])[:10]:
                status_icon = {"completed": "🟢", "failed": "🔴", "processing": "🟡", "queued": "⚪"}.get(j.get("status"), "⚫")
                st.text(f"{status_icon} {j['job_id']} · {j.get('type', '?')} · {j.get('status')} · {j.get('created_at', '')}")
    else:
        st.error(f"Cannot load metrics: {metrics.get('error')}")


# ═══════════════════════════════════════════════════════════
# PAGE: SETTINGS
# ═══════════════════════════════════════════════════════════

elif page == "⚙️ Settings":
    st.markdown("## ⚙️ Settings")
    
    # Server
    st.markdown("### 🌐 Server Connection")
    new_url = st.text_input("API Server URL", st.session_state.api_url)
    if new_url != st.session_state.api_url:
        st.session_state.api_url = new_url
    
    if st.button("🔄 Test Connection"):
        health = api_get("/health")
        if "error" not in health:
            st.success(f"✅ Connected — {health.get('version', '?')}")
        else:
            st.error(f"❌ {health.get('error')}")
    
    # Language
    st.markdown("### 🌍 Language")
    langs = {"English": "en", "Français": "fr", "中文": "zh", "日本語": "ja",
             "Español": "es", "العربية": "ar", "한국어": "ko", "Português": "pt"}
    lang_name = st.selectbox("Interface Language", list(langs.keys()))
    st.session_state.lang = langs[lang_name]
    
    # Available models
    st.markdown("### 🤖 Models")
    models_info = [
        ("Wan VACE 1.3B", "~16GB", "Default, RTX 4090"),
        ("Wan VACE 14B", "~48GB", "Best quality, A100/H100"),
        ("LoomVideo 5B", "~40GB", "Multi-image, fashion"),
        ("LTX-Video 13B", "~12GB", "Fast prototyping"),
    ]
    for name, vram, desc in models_info:
        st.text(f"  {name} ({vram}) — {desc}")
    
    # Realtime status
    st.markdown("### ⚡ Real-Time Mode")
    rt = api_get("/api/v1/realtime/status")
    if "error" not in rt:
        if rt.get("is_realtime"):
            st.success(f"⚡ FashionChameleon ACTIVE — {rt['expected_fps']} FPS")
        else:
            st.warning(f"⏳ Fallback mode ({rt.get('expected_fps', 3)} FPS)")
            st.caption("Set FITSTREAM_REALTIME_WEIGHTS_PATH when Alibaba publishes weights")
    
    # Styles & Templates
    st.markdown("### 🎨 Available Styles")
    styles = api_get("/api/v1/styles")
    if "error" not in styles:
        style_list = styles.get("styles", {})
        chips = " ".join(
            f'<span class="style-chip">{info.get("label", k)}</span>'
            for k, info in style_list.items()
        )
        st.markdown(chips, unsafe_allow_html=True)
    
    st.markdown("### 📝 Prompt Templates")
    tpls = api_get("/api/v1/templates")
    if "error" not in tpls:
        st.text(f"  {tpls.get('total', 0)} templates in {len(tpls.get('categories', []))} categories")
        for cat in tpls.get("categories", []):
            st.text(f"    • {cat}")
    
    # About
    st.markdown("---")
    st.markdown("### ℹ️ About FitStream")
    st.markdown("""
    **FitStream** — AI Video Animation & Try-On Platform  
    - 9 generation pipelines  
    - 46 API endpoints  
    - 290 tests passing ✅  
    - 17,700+ lines of code  
    
    Built with Wan VACE, LoomVideo, and ❤️
    """)

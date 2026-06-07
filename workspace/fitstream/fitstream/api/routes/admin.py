"""Admin & utility endpoints — metrics, styles, templates, cache, plugins, i18n, export, postprocess."""

import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from fitstream.api.dependencies import (
    get_job_queue,
    require_rate_limit,
    save_upload,
)
from fitstream.api.middleware import metrics
from fitstream.core.job_queue import JobQueue

router = APIRouter(prefix="/api/v1", tags=["Admin"], dependencies=[Depends(require_rate_limit)])


# ═══════════ Metrics ═══════════


@router.get("/metrics", tags=["Monitoring"])
async def get_metrics():
    """📊 API performance metrics."""
    return metrics.get_summary()


# ═══════════ Styles ═══════════


@router.get("/styles", tags=["Style"])
async def list_styles() -> dict:
    """List available style presets."""
    from fitstream.core.pipelines.style_transfer import STYLE_PRESETS

    return {
        "styles": {
            k: {"label": v["label"], "description": v["suffix"][:80]}
            for k, v in STYLE_PRESETS.items()
        }
    }


# ═══════════ Templates ═══════════


@router.get("/templates", tags=["Templates"])
async def list_templates(category: str | None = None) -> dict:
    from fitstream.core.prompt_templates import PromptTemplateLibrary

    lib = PromptTemplateLibrary()
    return {
        "templates": lib.list_templates(category),
        "categories": lib.list_categories(),
        "total": lib.count(),
    }


@router.get("/templates/search", tags=["Templates"])
async def search_templates(q: str):
    from fitstream.core.prompt_templates import PromptTemplateLibrary

    return PromptTemplateLibrary().search(q)


@router.post("/templates/fill", tags=["Templates"])
async def fill_template(
    template_id: str = Form(...),
    person: str = Form("the person"),
    garment: str = Form(""),
    location: str = Form(""),
):
    """🔍 Search prompt templates."""
    from fitstream.core.prompt_templates import PromptTemplateLibrary

    result = PromptTemplateLibrary().get(
        template_id, person=person, garment=garment, location=location
    )
    if result is None:
        raise HTTPException(404, f"Template {template_id} not found")
    return {"template_id": template_id, "prompt": result}


# ═══════════ Export ═══════════


@router.post("/export/{job_id}", tags=["Export"])
async def export_video(
    job_id: str,
    format: str = Form("gif"),
    jobs: JobQueue = Depends(get_job_queue),
):
    """📦 Export a video in different formats (gif, webm, storyboard, 9:16, 1:1)."""
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    video_path = job.video_path
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(404, "Video not available")

    from fitstream.core.export import ExportPipeline

    exporter = ExportPipeline()
    base = os.path.splitext(video_path)[0]

    format_map = {
        "gif": lambda: exporter.to_gif(video_path, f"{base}.gif"),
        "webm": lambda: exporter.to_webm(video_path, f"{base}.webm"),
        "storyboard": lambda: exporter.to_storyboard(video_path, f"{base}_storyboard.jpg"),
    }

    if format in format_map:
        result = format_map[format]()
    elif format in ("9:16", "1:1", "4:5", "16:9"):
        result = exporter.to_social(
            video_path, f"{base}_{format.replace(':', 'x')}.mp4", aspect=format
        )
    else:
        raise HTTPException(400, f"Unknown format: {format}")

    if result.success:
        return FileResponse(result.output_path, filename=os.path.basename(result.output_path))
    raise HTTPException(500, f"Export failed: {result.error}")


# ═══════════ Post-Processing ═══════════


@router.get("/postprocess/presets", tags=["Post-Processing"])
async def list_postprocess_presets() -> dict:
    """List postprocess presets."""
    from fitstream.core.postprocessing import PostProcessor

    return {
        "color_presets": PostProcessor.list_color_presets(),
        "operations": [
            "upscale",
            "stabilize",
            "color_grade",
            "slow_motion",
            "loop",
            "add_watermark",
            "trim",
        ],
    }


@router.post("/postprocess/{job_id}", tags=["Post-Processing"])
async def postprocess_video(
    job_id: str,
    operation: str = Form(...),
    preset: str = Form("cinematic"),
    factor: float = Form(2.0),
    text: str = Form("FitStream"),
    jobs: JobQueue = Depends(get_job_queue),
):
    """🎛️ Apply post-processing to a generated video."""
    job = jobs.get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")

    video_path = job.video_path
    if not video_path or not os.path.exists(video_path):
        raise HTTPException(404, "Video not available")

    from fitstream.core.postprocessing import PostProcessor

    pp = PostProcessor()
    out = os.path.splitext(video_path)[0] + f"_{operation}.mp4"

    ops = {
        "upscale": lambda: pp.upscale(video_path, out, factor=int(factor)),
        "color_grade": lambda: pp.color_grade(video_path, out, preset=preset),
        "slow_motion": lambda: pp.slow_motion(video_path, out, factor=factor),
        "watermark": lambda: pp.add_watermark(video_path, out, text=text),
        "trim": lambda: pp.trim(video_path, out, start=0, duration=factor),
        "loop": lambda: pp.loop(video_path, out, count=int(factor)),
    }

    if operation not in ops:
        raise HTTPException(400, f"Unknown operation: {operation}")

    result = ops[operation]()
    if result.success:
        return FileResponse(result.output_path, filename=os.path.basename(result.output_path))
    raise HTTPException(500, f"Post-processing failed: {result.error}")


# ═══════════ Analyze ═══════════


@router.post("/analyze", tags=["Utils"])
async def analyze_image(image: UploadFile = File(...)) -> dict:
    image_path = await save_upload(image, prefix="analyze_", validate=False)

    try:
        from fitstream.core.preprocessing import PreprocessingEngine

        engine = PreprocessingEngine()
        analysis = engine.analyze_image(image_path)
        report = engine.create_quality_report(analysis)

        return {
            "width": analysis.width,
            "height": analysis.height,
            "quality_score": round(analysis.quality_score, 2),
            "has_person": analysis.has_face,
            "issues": analysis.issues,
            "recommendations": analysis.recommendations,
            "report": report,
        }
    finally:
        if os.path.exists(image_path):
            os.unlink(image_path)


# ═══════════ Cache ═══════════


@router.get("/cache/stats", tags=["Cache"])
async def cache_stats():
    """Cache stats."""
    from fitstream.core.cache import GenerationCache

    return GenerationCache().get_stats()


# ═══════════ Plugins ═══════════


@router.get("/plugins", tags=["Plugins"])
async def list_plugins():
    """List plugins."""
    from fitstream.core.plugins import PluginRegistry

    return PluginRegistry.list_all()


# ═══════════ i18n ═══════════


@router.get("/i18n/{lang}", tags=["i18n"])
async def get_translations(lang: str) -> dict:
    from fitstream.core.i18n import I18n

    i18n = I18n(lang)
    return {
        "language": i18n.lang,
        "supported": I18n.supported_languages(),
        "messages": i18n.get_all(),
    }


# ═══════════ Analytics ═══════════


@router.get("/analytics", tags=["Analytics"])
async def get_analytics(hours: float = 24):
    """Get translations."""
    from fitstream.core.analytics import analytics

    return analytics.get_report(hours=hours)


@router.get("/analytics/top-styles", tags=["Analytics"])
async def top_styles(limit: int = 10) -> dict:
    from fitstream.core.analytics import analytics

    return {"styles": analytics.get_top_styles(limit)}


@router.get("/analytics/top-types", tags=["Analytics"])
async def top_types(limit: int = 10) -> dict:
    from fitstream.core.analytics import analytics

    return {"types": analytics.get_top_types(limit)}


# ═══════════ Webhooks ═══════════


@router.post("/webhooks", tags=["Webhooks"])
async def register_webhook(
    url: str = Form(...), events: str = Form("completed,failed"), secret: str = Form("")
) -> dict:
    from fitstream.core.webhooks import webhook_manager

    eid = webhook_manager.register(
        url, events=[e.strip() for e in events.split(",") if e.strip()], secret=secret
    )
    return {"endpoint_id": eid, "url": url}


@router.get("/webhooks", tags=["Webhooks"])
async def list_webhooks() -> dict:
    """Register webhook."""
    """List webhooks."""
    from fitstream.core.webhooks import webhook_manager

    return {"endpoints": webhook_manager.list_endpoints()}


@router.delete("/webhooks/{endpoint_id}", tags=["Webhooks"])
async def delete_webhook(endpoint_id: str) -> dict:
    from fitstream.core.webhooks import webhook_manager

    if webhook_manager.unregister(endpoint_id):
        return {"status": "removed"}
    raise HTTPException(404, "Webhook not found")


# ═══════════ Schedules ═══════════


@router.get("/schedules", tags=["Scheduler"])
async def list_schedules(active_only: bool = False) -> dict:
    from fitstream.core.scheduler import Scheduler

    return {"schedules": Scheduler().list_schedules(active_only=active_only)}

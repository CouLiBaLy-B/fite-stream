"""
Generation endpoints — /api/v1/animate, /story, /tryon, /compose, /style, /realtime
Each handler: validate → save upload → create job → enqueue background task.
"""

import os
import shutil
from typing import Optional, List

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile, HTTPException
from loguru import logger

from fitstream.config import FitStreamConfig
from fitstream.core.models.model_manager import ModelManager
from fitstream.core.job_queue import JobQueue
from fitstream.core.interfaces import validate_prompt
from fitstream.api.dependencies import (
    get_app_config, get_model_manager, get_job_queue,
    require_generation_rate_limit, save_upload, get_upload_dir,
)
from fitstream.api.schemas import GenerationResponse, StoryResponse, TryOnResponse, LoomResponse

router = APIRouter(prefix="/api/v1", tags=["Generation"])


# ═══════════ Helpers ═══════════

def _validate_or_raise(prompt: str, field: str = "prompt") -> None:
    errors = validate_prompt(prompt, field)
    if errors:
        raise HTTPException(400, errors[0].message)


_PIPELINE_MAP = {
    "animate": ("animate", "AnimatePipeline"),
    "story": ("story", "StoryPipeline"),
    "tryon": ("tryon", "TryOnPipeline"),
    "loom": ("loom", "LoomPipeline"),
    "style_transfer": ("style_transfer", "StyleTransferPipeline"),
    "realtime": ("realtime", "RealTimePipeline"),
}


async def _run_pipeline(
    job_queue: JobQueue,
    config: FitStreamConfig,
    model_manager: ModelManager,
    job_id: str,
    pipeline_name: str,
    pipeline_method: str,
    kwargs: dict,
) -> None:
    """
    Generic background task runner for all generation pipelines.
    
    Uses structured error handling:
    - GPU OOM → GPUError (retryable)
    - Pipeline logic failure → PipelineError (retryable)
    - User input issues → logged with context
    - Unexpected errors → full traceback logged
    """
    from fitstream.core.errors import PipelineError, GPUError, ModelError
    import traceback
    
    job_queue.start_job(job_id)
    
    try:
        # Resolve pipeline class
        if pipeline_name not in _PIPELINE_MAP:
            job_queue.fail_job(job_id, f"Unknown pipeline: {pipeline_name}")
            return
        
        module_name, cls_name = _PIPELINE_MAP[pipeline_name]
        
        # Dynamic import (avoids loading torch at module import time)
        import importlib
        mod = importlib.import_module(f"fitstream.core.pipelines.{module_name}")
        pipeline_cls = getattr(mod, cls_name)
        pipeline = pipeline_cls(config, model_manager)
        method = getattr(pipeline, pipeline_method)
        
        # Run generation
        result = method(**kwargs)
        
        if result.success:
            job_queue.complete_job(job_id, video_path=result.video_path, metadata={
                "generation_time": getattr(result, "generation_time", 0),
                "num_frames": getattr(result, "num_frames", 0),
                "duration_seconds": getattr(result, "duration_seconds", 0),
                "resolution": getattr(result, "resolution", ""),
                "seed": getattr(result, "seed", 0),
                "prompt_used": getattr(result, "prompt_used", ""),
            })
        else:
            error_msg = getattr(result, "error", None) or "Unknown generation error"
            logger.warning(
                f"Pipeline {pipeline_name} returned failure for job {job_id}: {error_msg}"
            )
            job_queue.fail_job(job_id, error_msg)
    
    except MemoryError:
        logger.error(f"Job {job_id}: GPU/CPU out of memory during {pipeline_name}")
        job_queue.fail_job(job_id, "Out of memory. Try draft quality or lower resolution.")
    
    except FileNotFoundError as e:
        logger.error(f"Job {job_id}: File not found — {e}")
        job_queue.fail_job(job_id, f"Input file not found: {e.filename or str(e)}")
    
    except (PipelineError, GPUError, ModelError) as e:
        logger.error(f"Job {job_id}: {e.error_code} — {e.message}")
        job_queue.fail_job(job_id, e.message)
    
    except Exception as e:
        # Unexpected error — log full traceback for debugging
        tb = traceback.format_exc()
        logger.error(
            f"Job {job_id}: Unhandled exception in {pipeline_name}:\n"
            f"  Type: {type(e).__name__}\n"
            f"  Message: {e}\n"
            f"  Traceback:\n{tb}"
        )
        job_queue.fail_job(
            job_id,
            f"Internal error ({type(e).__name__}). This has been logged for investigation."
        )


# ═══════════ Animate ═══════════

@router.post("/animate", response_model=GenerationResponse,
             dependencies=[Depends(require_generation_rate_limit)])
async def animate(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="Reference person image"),
    prompt: str = Form(..., description="Animation prompt"),
    style: str = Form("cinematic"),
    preset: str = Form("standard"),
    seed: int = Form(-1),
    num_frames: Optional[int] = Form(None),
    num_inference_steps: Optional[int] = Form(None),
    config: FitStreamConfig = Depends(get_app_config),
    models: ModelManager = Depends(get_model_manager),
    jobs: JobQueue = Depends(get_job_queue),
) -> GenerationResponse:
    """🎬 Generate an animated video from a person's photo + text prompt."""
    _validate_or_raise(prompt)
    image_path = await save_upload(image, prefix="animate_")
    
    job = jobs.create_job("animate", prompt=prompt, image_paths=[image_path],
                          params={"style": style, "preset": preset, "seed": seed})
    
    background_tasks.add_task(
        _run_pipeline, jobs, config, models, job.id, "animate", "generate",
        {"image_path": image_path, "prompt": prompt, "style": style,
         "preset": preset, "seed": seed, "num_frames": num_frames,
         "num_inference_steps": num_inference_steps},
    )
    
    return GenerationResponse(job_id=job.id, status="queued", prompt_used=prompt)


# ═══════════ Story ═══════════

@router.post("/story", response_model=StoryResponse,
             dependencies=[Depends(require_generation_rate_limit)])
async def story(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    story: str = Form(..., description="Story text"),
    style: str = Form("cinematic"),
    preset: str = Form("standard"),
    max_scenes: int = Form(5),
    transition: str = Form("crossfade"),
    config: FitStreamConfig = Depends(get_app_config),
    models: ModelManager = Depends(get_model_manager),
    jobs: JobQueue = Depends(get_job_queue),
) -> StoryResponse:
    """📖 Generate a multi-scene story video."""
    _validate_or_raise(story, "story")
    image_path = await save_upload(image, prefix="story_")
    
    job = jobs.create_job("story", prompt=story, image_paths=[image_path],
                          params={"style": style, "max_scenes": max_scenes})
    
    background_tasks.add_task(
        _run_pipeline, jobs, config, models, job.id, "story", "generate",
        {"image_path": image_path, "story": story, "style": style,
         "preset": preset, "max_scenes": max_scenes, "transition": transition},
    )
    
    return StoryResponse(job_id=job.id, status="queued")


# ═══════════ Try-On ═══════════

@router.post("/tryon", response_model=TryOnResponse,
             dependencies=[Depends(require_generation_rate_limit)])
async def tryon(
    background_tasks: BackgroundTasks,
    person_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    prompt: str = Form(""),
    category: str = Form("auto"),
    action: str = Form("walking naturally, showing off the outfit"),
    style: str = Form("cinematic"),
    preset: str = Form("standard"),
    seed: int = Form(-1),
    config: FitStreamConfig = Depends(get_app_config),
    models: ModelManager = Depends(get_model_manager),
    jobs: JobQueue = Depends(get_job_queue),
) -> TryOnResponse:
    """👗 Virtual try-on: person + garment → dressed video."""
    person_path = await save_upload(person_image, prefix="tryon_person_")
    garment_path = await save_upload(garment_image, prefix="tryon_garment_")
    
    job = jobs.create_job("tryon", prompt=prompt or "try-on",
                          image_paths=[person_path, garment_path],
                          params={"category": category})
    
    background_tasks.add_task(
        _run_pipeline, jobs, config, models, job.id, "tryon", "generate",
        {"person_image": person_path, "garment_image": garment_path,
         "prompt": prompt or None, "category": category, "action": action,
         "style": style, "preset": preset, "seed": seed},
    )
    
    return TryOnResponse(job_id=job.id, status="queued")


# ═══════════ Style ═══════════

@router.post("/style", dependencies=[Depends(require_generation_rate_limit)])
async def style_transfer(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    prompt: str = Form(...),
    style: str = Form("ghibli"),
    custom_style: str = Form(""),
    preset: str = Form("standard"),
    seed: int = Form(-1),
    config: FitStreamConfig = Depends(get_app_config),
    models: ModelManager = Depends(get_model_manager),
    jobs: JobQueue = Depends(get_job_queue),
):
    """🎭 Generate a stylized animation."""
    _validate_or_raise(prompt)
    image_path = await save_upload(image, prefix="style_")
    
    job = jobs.create_job("style", prompt=prompt, image_paths=[image_path],
                          params={"style": style})
    
    background_tasks.add_task(
        _run_pipeline, jobs, config, models, job.id, "style_transfer", "generate_with_style",
        {"person_image": image_path, "prompt": prompt, "style": style,
         "custom_style": custom_style, "preset": preset, "seed": seed},
    )
    
    return {"job_id": job.id, "status": "queued", "style": style}


# ═══════════ Compose ═══════════

@router.post("/compose", response_model=LoomResponse,
             dependencies=[Depends(require_generation_rate_limit)])
async def compose(
    background_tasks: BackgroundTasks,
    images: List[UploadFile] = File(..., description="2-8 reference images"),
    prompt: str = Form(...),
    style: str = Form("cinematic"),
    seed: int = Form(-1),
    num_frames: int = Form(97),
    config: FitStreamConfig = Depends(get_app_config),
    models: ModelManager = Depends(get_model_manager),
    jobs: JobQueue = Depends(get_job_queue),
) -> LoomResponse:
    """🎨 Multi-image composition with @Image N references."""
    if len(images) < 2:
        raise HTTPException(400, "At least 2 images required")
    if len(images) > 8:
        raise HTTPException(400, "Maximum 8 images")
    _validate_or_raise(prompt)
    
    image_paths = [await save_upload(img, prefix="compose_") for img in images]
    
    job = jobs.create_job("compose", prompt=prompt, image_paths=image_paths,
                          params={"num_images": len(image_paths)})
    
    background_tasks.add_task(
        _run_pipeline, jobs, config, models, job.id, "loom", "generate",
        {"images": image_paths, "prompt": prompt, "style": style,
         "seed": seed, "num_frames": num_frames},
    )
    
    return LoomResponse(job_id=job.id, status="queued",
                        num_reference_images=len(image_paths), task="mi2v")


# ═══════════ Real-Time ═══════════

@router.post("/realtime/generate", dependencies=[Depends(require_generation_rate_limit)])
async def realtime_generate(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    prompt: str = Form(...),
    seed: int = Form(-1),
    config: FitStreamConfig = Depends(get_app_config),
    models: ModelManager = Depends(get_model_manager),
    jobs: JobQueue = Depends(get_job_queue),
):
    """⚡ Fast generation — FashionChameleon when available, fallback otherwise."""
    _validate_or_raise(prompt)
    image_path = await save_upload(image, prefix="rt_")
    
    job = jobs.create_job("realtime", prompt=prompt, image_paths=[image_path])
    
    background_tasks.add_task(
        _run_pipeline, jobs, config, models, job.id, "realtime", "generate_fast",
        {"image_path": image_path, "prompt": prompt, "seed": seed},
    )
    
    return {"job_id": job.id, "status": "queued", "mode": "realtime"}


@router.get("/realtime/status")
async def realtime_status(
    config: FitStreamConfig = Depends(get_app_config),
    models: ModelManager = Depends(get_model_manager),
):
    """⚡ Check real-time availability."""
    from fitstream.core.pipelines.realtime import RealTimePipeline
    return RealTimePipeline(config, models).get_status()

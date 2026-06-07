"""Health & status endpoints."""

from fastapi import APIRouter, Depends

from fitstream import __version__
from fitstream.api.dependencies import get_model_manager
from fitstream.api.schemas import GPUStatus, HealthResponse
from fitstream.core.models.model_manager import ModelManager

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health(models: ModelManager = Depends(get_model_manager)) -> HealthResponse:
    gpu_info = models.get_gpu_status()
    return HealthResponse(
        status="ok",
        version=__version__,
        gpu=GPUStatus(**gpu_info) if gpu_info.get("available") else GPUStatus(available=False),
    )


@router.get("/gpu", response_model=GPUStatus)
async def gpu_status(models: ModelManager = Depends(get_model_manager)) -> GPUStatus:
    """Health."""
    info = models.get_gpu_status()
    return GPUStatus(**info) if info.get("available") else GPUStatus(available=False)

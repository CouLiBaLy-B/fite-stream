"""
FitStream Base Pipeline
Abstract base class that all generation pipelines must follow.

Enforces:
  - Consistent constructor signature (config, model_manager)
  - generate() method with GenerationRequest → GenerationResult
  - Structured error handling with typed exceptions
  - Resource cleanup

All 9 pipelines (animate, story, tryon, loom, loom_native,
extend, style_transfer, v2v_restyle, realtime) inherit from this.
"""

from __future__ import annotations

import os
import random
import time
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger

from fitstream.config import FitStreamConfig, get_config
from fitstream.core.errors import GPUError, PipelineError
from fitstream.core.interfaces import GenerationRequest, GenerationResult
from fitstream.core.models.model_manager import ModelManager


class BasePipeline(ABC):
    """
    Abstract base class for all generation pipelines.

    Subclasses MUST implement:
      - pipeline_name (class attribute)
      - _execute(request) → GenerationResult

    The base class provides:
      - Consistent constructor
      - generate() with error handling wrapper
      - Seed resolution
      - Output path generation
      - Timing measurement
      - Structured logging
    """

    pipeline_name: str = "base"

    def __init__(
        self,
        config: FitStreamConfig | None = None,
        model_manager: ModelManager | None = None,
    ) -> None:
        self.config = config or get_config()
        self.model_manager = model_manager or ModelManager(self.config)

    def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Public entry point — wraps _execute() with error handling.

        Subclasses should NOT override this method.
        Override _execute() instead.
        """
        start_time = time.time()

        # Resolve seed
        seed = request.seed
        if seed < 0:
            seed = random.randint(0, 2**32 - 1)
        request.seed = seed
        request.pipeline = self.pipeline_name

        logger.info(
            f"🎬 [{self.pipeline_name}] Starting generation "
            f"(seed={seed}, {request.width}x{request.height}, "
            f"{request.num_frames}f, {request.num_inference_steps}steps)"
        )

        try:
            result = self._execute(request)
            result.pipeline = self.pipeline_name
            result.generation_time = time.time() - start_time
            result.seed = seed

            if result.success:
                logger.success(
                    f"✅ [{self.pipeline_name}] Completed in "
                    f"{result.generation_time:.1f}s → {result.video_path}"
                )
            else:
                logger.warning(f"⚠️ [{self.pipeline_name}] Returned failure: {result.error}")

            return result

        except MemoryError as e:
            gen_time = time.time() - start_time
            logger.error(f"❌ [{self.pipeline_name}] OOM after {gen_time:.1f}s")
            raise GPUError(
                "Out of memory. Try draft quality or lower resolution.",
                cause=e,
                details={"pipeline": self.pipeline_name, "seed": seed},
            )

        except FileNotFoundError as e:
            gen_time = time.time() - start_time
            logger.error(f"❌ [{self.pipeline_name}] File not found: {e}")
            return GenerationResult(
                success=False,
                error=f"Input file not found: {e.filename or e}",
                generation_time=gen_time,
                seed=seed,
                pipeline=self.pipeline_name,
            )

        except PipelineError:
            raise  # Already structured, let it propagate

        except Exception as e:
            gen_time = time.time() - start_time
            logger.exception(f"❌ [{self.pipeline_name}] Unexpected error")
            raise PipelineError(
                f"Unexpected error in {self.pipeline_name}: {type(e).__name__}",
                pipeline=self.pipeline_name,
                cause=e,
            )

    @abstractmethod
    def _execute(self, request: GenerationRequest) -> GenerationResult:
        """
        Subclass implementation of the generation logic.

        Must return GenerationResult. Must NOT catch broad exceptions —
        the base class handles that.
        """
        ...

    def _ensure_model(self) -> Any:
        """Load the generation model (lazy, cached)."""
        return self.model_manager.load_vace_diffusers()

    def _resolve_output_path(
        self,
        request: GenerationRequest,
        suffix: str = "",
    ) -> str:
        """Generate a unique output path for the video."""
        os.makedirs(self.config.output_dir, exist_ok=True)
        ts = int(time.time())
        name = f"{self.pipeline_name}{suffix}_{ts}_{request.seed}.mp4"
        return os.path.join(self.config.output_dir, name)

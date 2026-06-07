"""
FitStream CLI — Command-line interface for video generation.

Usage:
    fitstream animate --image photo.jpg --prompt "Person walks in Paris"
    fitstream story --image photo.jpg --story "A day in Paris..."
    fitstream status
    fitstream download --model vace-1.3b
"""

import os
import sys

import click
from loguru import logger
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Configure logging
logger.remove()
logger.add(
    sys.stderr, level="INFO", format="<green>{time:HH:mm:ss}</green> | <level>{message}</level>"
)

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="FitStream")
def main() -> None:
    """🎬 FitStream — Transform photos into animated stories with AI"""
    pass


@main.command()
@click.option("--image", "-i", required=True, help="Path to reference person image")
@click.option("--prompt", "-p", required=True, help="Text prompt for the animation")
@click.option("--output", "-o", default=None, help="Output video path")
@click.option("--preset", type=click.Choice(["draft", "standard", "high"]), default="standard")
@click.option(
    "--style", default="cinematic", help="Visual style (cinematic, photorealistic, anime, etc.)"
)
@click.option("--seed", type=int, default=-1, help="Random seed (-1 for random)")
@click.option("--steps", type=int, default=None, help="Number of inference steps")
@click.option("--frames", type=int, default=None, help="Number of frames to generate")
def animate(image, prompt, output, preset, style, seed, steps, frames) -> None:
    """📸 Generate an animated video from a person's photo + prompt."""

    console.print(
        Panel.fit(
            f"[bold blue]🎬 FitStream Animate[/bold blue]\n"
            f"Image: {image}\n"
            f"Prompt: {prompt[:80]}...\n"
            f"Preset: {preset} | Style: {style}",
            title="Animation Generation",
        )
    )

    from fitstream.config import get_config
    from fitstream.core.pipelines.animate import AnimatePipeline

    config = get_config()
    pipeline = AnimatePipeline(config)

    result = pipeline.generate(
        image_path=image,
        prompt=prompt,
        output_path=output,
        preset=preset,
        style=style,
        seed=seed,
        num_inference_steps=steps,
        num_frames=frames,
    )

    if result.success:
        console.print("\n[bold green]✅ Success![/bold green]")
        console.print(f"   Video: {result.video_path}")
        console.print(f"   Duration: {result.duration_seconds:.1f}s ({result.num_frames} frames)")
        console.print(f"   Generation time: {result.generation_time:.1f}s")
        console.print(f"   Seed: {result.seed}")
    else:
        console.print(f"\n[bold red]❌ Failed: {result.error}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--image", "-i", required=True, help="Path to reference person image")
@click.option("--story", "-s", required=True, help="Story text or path to .txt file")
@click.option("--output", "-o", default=None, help="Output video path")
@click.option("--preset", type=click.Choice(["draft", "standard", "high"]), default="standard")
@click.option("--style", default="cinematic", help="Visual style")
@click.option("--max-scenes", type=int, default=None, help="Maximum number of scenes")
@click.option("--transition", type=click.Choice(["none", "crossfade"]), default="crossfade")
def story(image, story, output, preset, style, max_scenes, transition) -> None:
    """📖 Generate a multi-scene story video."""

    # Check if story is a file path
    if os.path.isfile(story):
        with open(story) as f:
            story_text = f.read()
    else:
        story_text = story

    console.print(
        Panel.fit(
            f"[bold blue]📖 FitStream Story[/bold blue]\n"
            f"Image: {image}\n"
            f"Story: {story_text[:120]}...\n"
            f"Preset: {preset} | Style: {style}",
            title="Story Generation",
        )
    )

    from fitstream.config import get_config
    from fitstream.core.pipelines.story import StoryPipeline

    config = get_config()
    pipeline = StoryPipeline(config)

    result = pipeline.generate(
        image_path=image,
        story=story_text,
        output_path=output,
        preset=preset,
        style=style,
        max_scenes=max_scenes,
        transition=transition,
    )

    if result.success:
        console.print("\n[bold green]🎉 Story generated![/bold green]")
        console.print(f"   Final video: {result.final_video_path}")
        console.print(f"   Scenes: {result.num_scenes_completed}/{len(result.scenes)}")
        console.print(f"   Total duration: {result.total_duration:.1f}s")
        console.print(f"   Generation time: {result.total_generation_time:.1f}s")
    else:
        console.print(f"\n[bold red]❌ Failed: {result.error}[/bold red]")
        sys.exit(1)


@main.command()
@click.option("--person", "-p", required=True, help="Path to person image")
@click.option("--garment", "-g", required=True, help="Path to garment image")
@click.option("--prompt", default="", help="Garment description (auto-detected if empty)")
@click.option("--output", "-o", default=None, help="Output video path")
@click.option(
    "--category",
    type=click.Choice(["auto", "upper", "lower", "dress", "shoes", "accessories"]),
    default="auto",
)
@click.option("--action", default="walking naturally, showing off the outfit")
@click.option("--preset", type=click.Choice(["draft", "standard", "high"]), default="standard")
@click.option("--style", default="cinematic")
@click.option("--seed", type=int, default=-1)
def tryon(person, garment, prompt, output, category, action, preset, style, seed) -> None:
    """👗 Virtual try-on: Generate a video with a new outfit."""

    console.print(
        Panel.fit(
            f"[bold blue]👗 FitStream Try-On[/bold blue]\n"
            f"Person: {person}\n"
            f"Garment: {garment}\n"
            f"Category: {category} | Action: {action[:40]}",
            title="Virtual Try-On",
        )
    )

    from fitstream.config import get_config
    from fitstream.core.pipelines.tryon import TryOnPipeline

    config = get_config()
    pipeline = TryOnPipeline(config)

    result = pipeline.generate(
        person_image=person,
        garment_image=garment,
        prompt=prompt if prompt else None,
        output_path=output,
        category=category,
        action=action,
        preset=preset,
        style=style,
        seed=seed,
    )

    if result.success:
        console.print("\n[bold green]✅ Try-on complete![/bold green]")
        console.print(f"   Video: {result.video_path}")
        console.print(f"   Category: {result.garment_category}")
        console.print(f"   Duration: {result.duration_seconds:.1f}s")
        console.print(f"   Time: {result.generation_time:.1f}s")
    else:
        console.print(f"\n[bold red]❌ Failed: {result.error}[/bold red]")
        sys.exit(1)


@main.command()
@click.option(
    "--images", "-i", required=True, multiple=True, help="Reference images (use multiple -i)"
)
@click.option("--prompt", "-p", required=True, help="Prompt with @Image 1, @Image 2, etc.")
@click.option("--output", "-o", default=None, help="Output video path")
@click.option("--style", default="cinematic")
@click.option("--seed", type=int, default=-1)
def compose(images, prompt, output, style, seed) -> None:
    """🎨 Multi-image composition with LoomVideo."""

    console.print(
        Panel.fit(
            f"[bold blue]🎨 FitStream Compose[/bold blue]\n"
            f"Images: {len(images)}\n"
            f"Prompt: {prompt[:80]}...",
            title="Multi-Image Composition",
        )
    )

    from fitstream.config import get_config
    from fitstream.core.pipelines.loom import LoomPipeline

    config = get_config()
    pipeline = LoomPipeline(config)

    result = pipeline.generate(
        images=list(images),
        prompt=prompt,
        output_path=output,
        style=style,
        seed=seed,
    )

    if result.success:
        console.print("\n[bold green]✅ Composition complete![/bold green]")
        console.print(f"   Video: {result.video_path}")
        console.print(f"   Task: {result.task}")
        console.print(f"   Time: {result.generation_time:.1f}s")
    else:
        console.print(f"\n[bold red]❌ Failed: {result.error}[/bold red]")
        sys.exit(1)


@main.command()
def status() -> None:
    """📊 Show system status and GPU info."""

    from fitstream.config import get_config
    from fitstream.core.models.model_manager import ModelManager

    config = get_config()
    mm = ModelManager(config)
    gpu_info = mm.get_gpu_status()

    table = Table(title="🖥️ FitStream System Status")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Project", config.project_name)
    table.add_row("Version", config.version)
    table.add_row("GPU Available", "✅ Yes" if gpu_info.get("available") else "❌ No")

    if gpu_info.get("available"):
        table.add_row("GPU", gpu_info.get("gpu_name", "Unknown"))
        table.add_row("VRAM Total", f"{gpu_info.get('total_gb', 0):.1f} GB")
        table.add_row("VRAM Free", f"{gpu_info.get('free_gb', 0):.1f} GB")
        table.add_row("VRAM Used", f"{gpu_info.get('used_gb', 0):.1f} GB")

    table.add_row("Default Model", config.model.name)
    table.add_row("Output Dir", config.output_dir)

    # Check which packages are installed
    try:
        import torch

        table.add_row("PyTorch", torch.__version__)
    except ImportError:
        table.add_row("PyTorch", "❌ Not installed")

    try:
        import diffusers

        table.add_row("Diffusers", diffusers.__version__)
    except ImportError:
        table.add_row("Diffusers", "❌ Not installed")

    console.print(table)


@main.command()
@click.option(
    "--model",
    "-m",
    type=click.Choice(["vace-1.3b", "vace-14b", "loomvideo"]),
    default="vace-1.3b",
    help="Model to download",
)
def download(model) -> None:
    """📥 Download model weights from HuggingFace."""

    console.print(f"[bold blue]📥 Downloading model: {model}[/bold blue]")

    from fitstream.config import get_config
    from fitstream.core.models.model_manager import ModelManager

    config = get_config()
    mm = ModelManager(config)
    mm.download_model(model)  # type: ignore[attr-defined]

    console.print(f"[bold green]✅ Model {model} ready![/bold green]")


if __name__ == "__main__":
    main()

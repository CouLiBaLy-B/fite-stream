#!/usr/bin/env python3
"""
FitStream End-to-End Demo
=========================
Demonstrates the full pipeline WITHOUT requiring a GPU.
Uses mock generation to show the complete flow:
  1. Image analysis & preprocessing
  2. Story parsing → scene breakdown
  3. Try-on prompt construction
  4. Multi-image reference validation
  5. Job queue management

Run:
    cd fitstream
    PYTHONPATH=. python scripts/demo.py
"""

import sys
import os
import time
import tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import print as rprint

console = Console()


def create_demo_image(label: str, color: tuple, size=(800, 1200)) -> str:
    """Create a labeled demo image and save to temp file."""
    img = Image.new("RGB", size, color)
    draw = ImageDraw.Draw(img)
    
    # Add label text
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except (IOError, OSError):
        font = ImageFont.load_default()
    
    # Center text
    bbox = draw.textbbox((0, 0), label, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size[0] - tw) // 2
    y = (size[1] - th) // 2
    draw.text((x, y), label, fill="white", font=font)
    
    # Add border
    draw.rectangle([5, 5, size[0]-5, size[1]-5], outline="white", width=3)
    
    path = tempfile.mktemp(suffix=".jpg")
    img.save(path)
    return path


def demo_preprocessing():
    """Demo 1: Image Analysis & Preprocessing."""
    console.print(Panel("[bold cyan]Demo 1: Image Analysis & Preprocessing[/bold cyan]"))
    
    from fitstream.core.preprocessing import PreprocessingEngine
    
    engine = PreprocessingEngine()
    
    # Create test images
    images = {
        "Good portrait": create_demo_image("Person Portrait", (100, 130, 170)),
        "Dark image": create_demo_image("Dark Scene", (15, 15, 20)),
        "Small image": create_demo_image("Tiny", (128, 128, 128), (150, 150)),
    }
    
    for name, path in images.items():
        analysis = engine.analyze_image(path)
        report = engine.create_quality_report(analysis)
        console.print(f"\n  📷 [bold]{name}[/bold]:")
        for line in report.split("\n"):
            console.print(f"     {line}")
        os.unlink(path)
    
    console.print(f"\n  [green]✅ Preprocessing engine works![/green]\n")


def demo_story_parsing():
    """Demo 2: Story Parsing → Scene Breakdown."""
    console.print(Panel("[bold cyan]Demo 2: Story Parsing[/bold cyan]"))
    
    from fitstream.core.utils.prompt_utils import split_story_to_scenes, create_story_summary
    
    stories = {
        "Free-form story": (
            "Marie walks through a sunny Parisian street. "
            "She stops at a charming flower shop and picks a bouquet of roses. "
            "She enters a cozy café and orders an espresso. "
            "She sits by the window, watching the rain begin to fall. "
            "She smiles and opens her notebook to write."
        ),
        "Structured story": """
---
SCENE 1: A woman stands on a bridge overlooking the river at golden hour
CAMERA: wide shot
MOOD: romantic
DURATION: long
---
SCENE 2: She turns and smiles at the camera, wind in her hair
CAMERA: close-up
MOOD: happy
DURATION: short
---
SCENE 3: She walks along the riverbank as the sun sets behind her
CAMERA: medium shot
MOOD: peaceful
DURATION: medium
---
""",
    }
    
    for name, story in stories.items():
        scenes = split_story_to_scenes(story, max_scenes=8, style="cinematic")
        summary = create_story_summary(scenes)
        console.print(f"\n  📖 [bold]{name}[/bold]:")
        for line in summary.split("\n"):
            console.print(f"     {line}")
    
    console.print(f"\n  [green]✅ Story parsing works! ({sum(len(split_story_to_scenes(s)) for s in stories.values())} scenes total)[/green]\n")


def demo_tryon():
    """Demo 3: Try-On Prompt Construction."""
    console.print(Panel("[bold cyan]Demo 3: Virtual Try-On Prompts[/bold cyan]"))
    
    from fitstream.core.pipelines.tryon import detect_garment_category, build_tryon_prompt
    
    garments = [
        ("a blue cotton t-shirt with a graphic print", "walking casually"),
        ("elegant red evening dress with lace details", "walking on a runway"),
        ("dark denim jeans with ripped knees", "standing confidently"),
        ("white leather sneakers with gold accents", "walking through the city"),
        ("vintage straw hat with a ribbon", "strolling in a garden"),
    ]
    
    table = Table(title="Try-On Prompt Builder")
    table.add_column("Garment", style="cyan", width=35)
    table.add_column("Category", style="yellow", width=12)
    table.add_column("Generated Prompt (truncated)", style="white", width=50)
    
    for desc, action in garments:
        cat = detect_garment_category(desc)
        prompt = build_tryon_prompt(desc, cat, "cinematic", action)
        table.add_row(desc[:35], cat, prompt[:50] + "...")
    
    console.print(table)
    console.print(f"\n  [green]✅ Try-on prompt builder works![/green]\n")


def demo_multi_image():
    """Demo 4: Multi-Image Reference Validation."""
    console.print(Panel("[bold cyan]Demo 4: Multi-Image Composition (LoomVideo-style)[/bold cyan]"))
    
    from fitstream.core.pipelines.loom import validate_image_references, build_multi_image_prompt
    
    test_cases = [
        {
            "prompt": "The woman (@Image 1) wearing the red dress (@Image 2) walks in the garden (@Image 3)",
            "images": 3,
            "label": "Valid 3-image composition",
        },
        {
            "prompt": "A beautiful scene with nature",
            "images": 2,
            "label": "Missing @Image references",
        },
        {
            "prompt": "Person (@Image 1) in location (@Image 5)",
            "images": 2,
            "label": "Out-of-range reference",
        },
    ]
    
    for tc in test_cases:
        warnings = validate_image_references(tc["prompt"], tc["images"])
        status = "✅" if not warnings else "⚠️"
        console.print(f"\n  {status} [bold]{tc['label']}[/bold]")
        console.print(f"     Prompt: {tc['prompt'][:70]}...")
        console.print(f"     Images: {tc['images']}")
        if warnings:
            for w in warnings:
                console.print(f"     ⚠️ {w}")
        else:
            console.print(f"     → All references valid!")
    
    # Build a multi-image prompt
    prompt = build_multi_image_prompt(
        {1: "the elegant woman", 2: "the vintage red dress", 3: "the Parisian café"},
        action="sits at a table, sipping coffee with a gentle smile",
        style="warm",
    )
    console.print(f"\n  📝 Generated multi-image prompt:")
    console.print(f"     {prompt[:120]}...")
    
    console.print(f"\n  [green]✅ Multi-image validation works![/green]\n")


def demo_job_queue():
    """Demo 5: Job Queue Management."""
    console.print(Panel("[bold cyan]Demo 5: Job Queue[/bold cyan]"))
    
    from fitstream.core.job_queue import JobQueue, JobType, JobStatus
    
    queue = JobQueue()
    
    # Create some jobs
    job1 = queue.create_job(JobType.ANIMATE, prompt="Person walking in park")
    job2 = queue.create_job(JobType.STORY, prompt="A day in Paris")
    job3 = queue.create_job(JobType.TRYON, prompt="Red dress try-on")
    
    # Simulate processing
    queue.start_job(job1.id)
    queue.update_progress(job1.id, 0.25, "Loading model...")
    queue.update_progress(job1.id, 0.50, "Generating frames...")
    queue.update_progress(job1.id, 0.75, "Encoding video...")
    queue.complete_job(job1.id, video_path="/outputs/demo.mp4", metadata={"seed": 42, "fps": 16})
    
    queue.start_job(job2.id)
    queue.fail_job(job2.id, "GPU out of memory")
    
    # List jobs
    table = Table(title="Job Queue Status")
    table.add_column("ID", style="cyan", width=10)
    table.add_column("Type", style="yellow", width=10)
    table.add_column("Status", width=12)
    table.add_column("Progress", width=10)
    table.add_column("Duration", width=10)
    table.add_column("Prompt", width=30)
    
    for job in queue.list_jobs():
        status_style = {
            "completed": "[green]✅ Done[/green]",
            "failed": "[red]❌ Failed[/red]",
            "queued": "[yellow]⏳ Queued[/yellow]",
            "processing": "[blue]⚙️ Running[/blue]",
        }.get(job.status, job.status)
        
        table.add_row(
            job.id,
            job.type,
            status_style,
            f"{job.progress:.0%}",
            f"{job.duration:.1f}s",
            job.prompt[:30],
        )
    
    console.print(table)
    console.print(f"\n  [green]✅ Job queue works![/green]\n")


def demo_summary():
    """Final summary."""
    console.print(Panel.fit(
        "[bold green]🎉 All demos completed successfully![/bold green]\n\n"
        "[bold]FitStream is ready. Next steps:[/bold]\n\n"
        "  1. Install on your RTX 4090 machine:\n"
        "     [cyan]bash scripts/setup.sh[/cyan]\n\n"
        "  2. Download the AI model (~5GB):\n"
        "     [cyan]python scripts/download_models.py --model vace-1.3b[/cyan]\n\n"
        "  3. Start the server:\n"
        "     [cyan]PYTHONPATH=. python -m fitstream.api.server[/cyan]\n\n"
        "  4. Open the web UI:\n"
        "     [cyan]http://localhost:8000/app[/cyan]\n\n"
        "  5. Or use the CLI:\n"
        "     [cyan]fitstream animate -i photo.jpg -p 'Person walks in a garden'[/cyan]",
        title="🎬 FitStream Demo Complete",
    ))


def main():
    console.print(Panel.fit(
        "[bold]🎬 FitStream End-to-End Demo[/bold]\n"
        "Testing all components WITHOUT GPU\n"
        f"Python {sys.version.split()[0]}",
        title="Demo",
    ))
    
    demos = [
        ("1/5", demo_preprocessing),
        ("2/5", demo_story_parsing),
        ("3/5", demo_tryon),
        ("4/5", demo_multi_image),
        ("5/5", demo_job_queue),
    ]
    
    for label, func in demos:
        console.print(f"\n[dim]{'─'*60} [{label}][/dim]")
        func()
    
    console.print(f"\n[dim]{'─'*60}[/dim]")
    demo_summary()


if __name__ == "__main__":
    main()

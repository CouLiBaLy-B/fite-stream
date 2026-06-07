"""
FitStream Model Downloader
Downloads model weights from HuggingFace Hub.

Usage:
    python scripts/download_models.py --model vace-1.3b
    python scripts/download_models.py --model vace-14b
    python scripts/download_models.py --model loomvideo
    python scripts/download_models.py --model all
"""

import os
import sys
import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

MODELS = {
    "vace-1.3b": {
        "name": "Wan2.1 VACE 1.3B Preview",
        "repo": "Wan-AI/Wan2.1-VACE-1.3B-Preview",
        "local_dir": "./models/VACE-Wan2.1-1.3B-Preview",
        "size_gb": "~5GB",
        "min_vram": "16GB",
        "description": "Lightweight model, good for RTX 4090",
    },
    "vace-14b": {
        "name": "Wan2.1 VACE 14B",
        "repo": "Wan-AI/Wan2.1-VACE-14B",
        "local_dir": "./models/VACE-Wan2.1-14B",
        "size_gb": "~28GB",
        "min_vram": "48GB+",
        "description": "Full model, best quality (needs A100/H100)",
    },
    "wan-i2v": {
        "name": "Wan2.2 Image-to-Video A14B",
        "repo": "Wan-AI/Wan2.2-I2V-A14B",
        "local_dir": "./models/Wan2.2-I2V-A14B",
        "size_gb": "~28GB",
        "min_vram": "24GB+",
        "description": "Latest Wan 2.2 Image-to-Video model",
    },
    "loomvideo": {
        "name": "LoomVideo 5B",
        "repo": "MSALab/LoomVideo",
        "local_dir": "./models/LoomVideo",
        "size_gb": "~10GB",
        "min_vram": "24GB+",
        "description": "Fashion-specialized, multi-image composition",
    },
}


@click.command()
@click.option("--model", "-m", required=True,
              type=click.Choice(list(MODELS.keys()) + ["all", "list"]),
              help="Model to download")
@click.option("--force", is_flag=True, help="Force re-download")
def main(model, force):
    """📥 Download FitStream model weights."""
    
    if model == "list":
        # List available models
        console.print("\n📦 [bold]Available Models:[/bold]\n")
        for key, info in MODELS.items():
            exists = os.path.exists(info["local_dir"]) and os.listdir(info.get("local_dir", "/nonexistent"))
            status = "✅ Downloaded" if exists else "❌ Not downloaded"
            console.print(f"  [cyan]{key}[/cyan] — {info['name']}")
            console.print(f"    Size: {info['size_gb']} | Min VRAM: {info['min_vram']}")
            console.print(f"    {info['description']}")
            console.print(f"    Status: {status}\n")
        return
    
    models_to_download = list(MODELS.keys()) if model == "all" else [model]
    
    from huggingface_hub import snapshot_download
    
    for model_key in models_to_download:
        info = MODELS[model_key]
        
        # Check if already downloaded
        if not force and os.path.exists(info["local_dir"]):
            contents = os.listdir(info["local_dir"]) if os.path.isdir(info["local_dir"]) else []
            if contents:
                console.print(f"[yellow]⚡ {info['name']} already downloaded. Use --force to re-download.[/yellow]")
                continue
        
        console.print(f"\n[bold blue]📥 Downloading {info['name']}...[/bold blue]")
        console.print(f"   Repo: {info['repo']}")
        console.print(f"   Size: {info['size_gb']}")
        console.print(f"   Target: {info['local_dir']}")
        console.print(f"   This may take a while...\n")
        
        try:
            os.makedirs(info["local_dir"], exist_ok=True)
            
            snapshot_download(
                repo_id=info["repo"],
                local_dir=info["local_dir"],
                local_dir_use_symlinks=False,
            )
            
            console.print(f"[bold green]✅ {info['name']} downloaded successfully![/bold green]")
            
        except Exception as e:
            console.print(f"[bold red]❌ Failed to download {info['name']}: {e}[/bold red]")
            sys.exit(1)


if __name__ == "__main__":
    main()

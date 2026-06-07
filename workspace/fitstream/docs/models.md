# 🤖 Supported Models

## Download Models

```bash
# List available models
python scripts/download_models.py --model list

# Download specific model
python scripts/download_models.py --model vace-1.3b    # ~5GB, RTX 4090
python scripts/download_models.py --model vace-14b     # ~28GB, A100/H100
python scripts/download_models.py --model wan-i2v      # ~28GB, Wan 2.2 I2V
python scripts/download_models.py --model loomvideo    # ~10GB, Multi-image
```

## Model Comparison

| Model | Params | Download | Min VRAM | Quality | Speed | Best For |
|-------|--------|----------|----------|---------|-------|----------|
| **Wan VACE 1.3B** | 1.3B | ~5GB | 16GB | ★★★☆ | ★★★★ | Default, RTX 4090 |
| **Wan VACE 14B** | 14B | ~28GB | 48GB | ★★★★★ | ★★★☆ | Best quality |
| **Wan 2.2 I2V A14B** | 14B | ~28GB | 24GB+ | ★★★★ | ★★★☆ | Latest Wan model |
| **LoomVideo 5B** | 5B | ~10GB | 40GB+ | ★★★★ | ★★★☆ | Multi-image, fashion |
| **LTX-Video 13B** | 13B | ~12GB | 12GB | ★★★☆ | ★★★★★ | Fast prototyping |

## VRAM Usage Guide

| GPU | VRAM | Recommended Model | Notes |
|-----|------|--------------------|-------|
| RTX 3060 | 12GB | LTX-Video 13B | Only fast prototyping |
| RTX 4070 | 12GB | LTX-Video 13B | Only fast prototyping |
| RTX 4090 | 24GB | **Wan VACE 1.3B** | With CPU offload enabled |
| A100 | 40GB | Wan VACE 14B | Full quality |
| A100 | 80GB | Wan VACE 14B | No offload needed |
| H100 | 80GB | Wan VACE 14B | Fastest inference |

## Optimizations Applied (RTX 4090)

FitStream automatically applies these optimizations when VRAM ≤ 24GB:

1. **Model CPU Offload** — Pipeline components moved to CPU when not in use
2. **VAE Slicing** — Decode latents in slices instead of all at once
3. **VAE Tiling** — Tile-based decoding for high-resolution outputs
4. **T5 on CPU** — Text encoder runs on CPU (saves ~4GB VRAM)
5. **BFloat16** — Half-precision computation throughout
6. **Aggressive GC** — Explicit cache clearing between generations

## Model Sources

| Model | HuggingFace | GitHub |
|-------|-------------|--------|
| Wan VACE 1.3B | [Wan-AI/Wan2.1-VACE-1.3B-Preview](https://huggingface.co/Wan-AI/Wan2.1-VACE-1.3B-Preview) | [ali-vilab/VACE](https://github.com/ali-vilab/VACE) |
| Wan VACE 14B | [Wan-AI/Wan2.1-VACE-14B](https://huggingface.co/Wan-AI/Wan2.1-VACE-14B) | [ali-vilab/VACE](https://github.com/ali-vilab/VACE) |
| Wan 2.2 I2V | [Wan-AI/Wan2.2-I2V-A14B](https://huggingface.co/Wan-AI/Wan2.2-I2V-A14B) | [Wan-Video/Wan2.1](https://github.com/Wan-Video/Wan2.1) |
| LoomVideo | [MSALab/LoomVideo](https://huggingface.co/MSALab/LoomVideo) | [MSALab-PKU/LoomVideo](https://github.com/MSALab-PKU/LoomVideo) |
| LTX-Video | [Lightricks/LTX-Video](https://huggingface.co/Lightricks/LTX-Video) | [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) |

#!/bin/bash
# =============================================================
# FitStream Setup Script
# Sets up the complete environment for FitStream
# Optimized for RTX 4090 (24GB VRAM)
# =============================================================

set -e

echo "🎬 FitStream Setup"
echo "==================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Check Python version
echo -e "\n${BLUE}[1/6] Checking Python version...${NC}"
python_version=$(python3 --version 2>/dev/null | cut -d' ' -f2)
if [[ -z "$python_version" ]]; then
    echo -e "${RED}Python 3 not found! Please install Python 3.10+${NC}"
    exit 1
fi
echo -e "${GREEN}  ✅ Python $python_version${NC}"

# 2. Create virtual environment
echo -e "\n${BLUE}[2/6] Creating virtual environment...${NC}"
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
    echo -e "${GREEN}  ✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}  ✅ Virtual environment already exists${NC}"
fi

source .venv/bin/activate

# 3. Install PyTorch with CUDA
echo -e "\n${BLUE}[3/6] Installing PyTorch with CUDA support...${NC}"
pip install --upgrade pip setuptools wheel
pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cu124

# 4. Install FitStream and dependencies
echo -e "\n${BLUE}[4/6] Installing FitStream...${NC}"
pip install -e ".[dev]"

# 5. Install additional video dependencies
echo -e "\n${BLUE}[5/6] Installing video processing tools...${NC}"
pip install imageio[ffmpeg] opencv-python-headless

# Check ffmpeg
if command -v ffmpeg &> /dev/null; then
    echo -e "${GREEN}  ✅ ffmpeg found$(NC}"
else
    echo -e "${RED}  ⚠️ ffmpeg not found. Install with: sudo apt install ffmpeg${NC}"
fi

# 6. Create directories
echo -e "\n${BLUE}[6/6] Creating directories...${NC}"
mkdir -p models outputs uploads assets/demo

# 7. GPU check
echo -e "\n${BLUE}Checking GPU...${NC}"
python3 -c "
import torch
if torch.cuda.is_available():
    name = torch.cuda.get_device_name(0)
    mem = torch.cuda.get_device_properties(0).total_mem / (1024**3)
    print(f'  ✅ GPU: {name} ({mem:.1f}GB)')
    if mem >= 24:
        print(f'  ✅ Sufficient VRAM for Wan VACE 1.3B')
    if mem >= 48:
        print(f'  ✅ Sufficient VRAM for Wan VACE 14B')
else:
    print('  ❌ No CUDA GPU detected')
"

echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}🎬 FitStream setup complete!${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Download a model:"
echo "     python -m fitstream.cli download --model vace-1.3b"
echo ""
echo "  2. Generate your first animation:"
echo "     python -m fitstream.cli animate \\"
echo "       --image assets/demo/person.jpg \\"
echo "       --prompt 'A person walks through a sunlit garden'"
echo ""
echo "  3. Start the API server:"
echo "     python -m fitstream.api.server"
echo ""
echo "  4. Open API docs at: http://localhost:8000/docs"

#!/bin/bash
# =============================================================================
# AlgoCompiler — Setup Script for Linux
# Run this script ONCE to install all required dependencies.
# Usage: ./scripts/setup_linux.sh
# =============================================================================

# --- Color Codes ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║       AlgoCompiler — Linux Setup      ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# --- Step 1: Check for Python 3 ---
echo -e "${BLUE}[1/4] Checking Python 3 installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed!${NC}"
    echo ""
    echo "Please install it using your package manager:"
    echo "  Ubuntu/Debian:  sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora/CentOS:  sudo dnf install python3 python3-pip"
    echo "  Arch Linux:     sudo pacman -S python"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}✓ Found: ${PYTHON_VERSION}${NC}"

# --- Step 2: Check for pip ---
echo -e "${BLUE}[2/4] Checking pip...${NC}"
if ! python3 -m pip --version &> /dev/null; then
    echo -e "${YELLOW}pip not found. Attempting to install...${NC}"
    python3 -m ensurepip --upgrade
fi
echo -e "${GREEN}✓ pip is available${NC}"

# --- Step 3: Create a virtual environment ---
echo -e "${BLUE}[3/4] Creating Python virtual environment in ./venv ...${NC}"
# Get the directory of this script, then go up one level to project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}→ Virtual environment already exists, skipping creation${NC}"
fi

# --- Step 4: Install dependencies ---
echo -e "${BLUE}[4/4] Installing dependencies from requirements.txt...${NC}"
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║  ✓ Setup complete! You are ready to go.  ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "To launch AlgoCompiler, run:"
    echo -e "  ${YELLOW}./run_app.sh${NC}"
    echo ""
    echo -e "Then open your browser at: ${BLUE}http://localhost:5000${NC}"
else
    echo -e "${RED}✗ Something went wrong during installation. Please check the error messages above.${NC}"
    exit 1
fi

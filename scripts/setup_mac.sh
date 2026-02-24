#!/bin/bash
# =============================================================================
# AlgoCompiler — Setup Script for macOS
# Run this script ONCE to install all required dependencies.
# Usage: ./scripts/setup_mac.sh
# =============================================================================

# --- Color Codes ---
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║       AlgoCompiler — macOS Setup      ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# --- Step 1: Check for Python 3 ---
echo -e "${BLUE}[1/4] Checking Python 3 installation...${NC}"

# On macOS, 'python3' may refer to the system Python or a Homebrew one
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python 3 is not installed!${NC}"
    echo ""
    echo "Recommended: Install via Homebrew"
    echo "  1. Install Homebrew: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "  2. Then run:         brew install python3"
    echo ""
    echo "Alternative: Download from https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1)
echo -e "${GREEN}✓ Found: ${PYTHON_VERSION}${NC}"

# Warn about macOS system Python (< 3.8 may have issues)
PYTHON_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${YELLOW}⚠ Warning: Python 3.8+ is recommended. You have ${PYTHON_VERSION}.${NC}"
fi

# --- Step 2: Check for pip ---
echo -e "${BLUE}[2/4] Checking pip...${NC}"
if ! python3 -m pip --version &> /dev/null; then
    echo -e "${YELLOW}pip not found. Attempting to install...${NC}"
    python3 -m ensurepip --upgrade
fi
echo -e "${GREEN}✓ pip is available${NC}"

# --- Step 3: Create a virtual environment ---
echo -e "${BLUE}[3/4] Creating Python virtual environment in ./venv ...${NC}"
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

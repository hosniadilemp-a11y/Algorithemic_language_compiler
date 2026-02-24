#!/bin/bash
# =============================================================================
# AlgoCompiler Web Server Launcher for macOS
# Usage: ./run_app_mac.sh
# =============================================================================

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   AlgoCompiler Web Server (macOS)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed!${NC}"
    echo "Run ./scripts/setup_mac.sh first."
    exit 1
fi

# Navigate to project root
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo -e "${BLUE}→ Activating virtual environment...${NC}"
    source venv/bin/activate
fi

# Kill any existing instances
echo -e "${BLUE}→ Stopping any existing server instances...${NC}"
pkill -f "python3 src/web/app.py" 2>/dev/null
pkill -f "python src/web/app.py" 2>/dev/null
sleep 1

# Clear parser cache
echo -e "${BLUE}→ Clearing parser cache...${NC}"
rm -f src/compiler/parser.out src/compiler/parsetab.py 2>/dev/null

# Start the server in the background
echo -e "${GREEN}→ Starting AlgoCompiler...${NC}"
python3 src/web/app.py &
SERVER_PID=$!

# Wait a moment for the server to start
sleep 2

# Auto-open browser on macOS
echo -e "${BLUE}→ Opening browser at http://localhost:5000${NC}"
open http://localhost:5000

echo ""
echo -e "${GREEN}Server is running (PID: $SERVER_PID)${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo ""

# Wait for Ctrl+C
trap "kill $SERVER_PID 2>/dev/null; echo 'Server stopped.'" SIGINT
wait $SERVER_PID

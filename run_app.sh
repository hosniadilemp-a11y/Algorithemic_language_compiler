#!/bin/bash
# AlgoCompiler Web Server Launcher for Linux/Mac

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   AlgoCompiler Web Server${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed!${NC}"
    exit 1
fi

# Kill any existing instances
echo -e "${BLUE}Stopping any existing server instances...${NC}"
pkill -f "python3 src/web/app.py" 2>/dev/null
sleep 1

# Clear parser cache to ensure latest changes are loaded
echo -e "${BLUE}Clearing parser cache...${NC}"
rm -f src/compiler/parser.out src/compiler/parsetab.py 2>/dev/null

# Start the server
echo -e "${GREEN}Starting AlgoCompiler web server...${NC}"
echo -e "${BLUE}Server will be available at: http://localhost:5000${NC}"
echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
echo ""

cd "$(dirname "$0")"
python3 src/web/app.py

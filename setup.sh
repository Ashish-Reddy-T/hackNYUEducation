#!/bin/bash
# Complete setup and startup script for Agora

set -e

echo "=================================="
echo "  AGORA - Complete Setup Script"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please copy .env.example to .env and add your API keys:"
    echo "  cp .env.example .env"
    echo "  # Edit .env with your API keys"
    exit 1
fi

echo -e "${GREEN}✓${NC} .env file found"
echo ""

# 1. Start Qdrant
echo "=================================="
echo "  Step 1: Starting Qdrant"
echo "=================================="
echo ""

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: docker-compose not found${NC}"
    echo "Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "Starting Qdrant vector database..."
docker-compose up -d

echo ""
echo -e "${GREEN}✓${NC} Qdrant started on http://localhost:6333"
echo ""

# Wait for Qdrant to be ready
echo "Waiting for Qdrant to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Qdrant is ready!"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# 2. Setup Backend
echo "=================================="
echo "  Step 2: Setting up Backend"
echo "=================================="
echo ""

cd backend

# Check for conda
if ! command -v conda &> /dev/null; then
    echo -e "${YELLOW}Warning: conda not found${NC}"
    echo "Install Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    echo "Or use pip with requirements.txt"
    exit 1
fi

# Create conda environment
if conda env list | grep -q "^agora "; then
    echo -e "${GREEN}✓${NC} Conda environment 'agora' already exists"
else
    echo "Creating conda environment..."
    conda env create -f environment.yml
    echo -e "${GREEN}✓${NC} Conda environment created"
fi

echo ""
echo "Activating environment and installing dependencies..."

# Copy environment variables
cp ../.env .env 2>/dev/null || echo ".env already exists in backend/"

echo ""
echo -e "${GREEN}✓${NC} Backend setup complete"
echo ""

# 3. Start Backend
echo "=================================="
echo "  Step 3: Starting Backend Server"
echo "=================================="
echo ""

echo "To start the backend, run:"
echo ""
echo -e "${YELLOW}  cd backend${NC}"
echo -e "${YELLOW}  conda activate agora${NC}"
echo -e "${YELLOW}  python -m app.main${NC}"
echo ""
echo "Backend will be available at: http://localhost:8000"
echo "API docs at: http://localhost:8000/docs"
echo ""

# 4. Frontend Setup Instructions
echo "=================================="
echo "  Step 4: Frontend Setup"
echo "=================================="
echo ""
echo "For the frontend, you need to:"
echo ""
echo "1. Initialize SvelteKit project:"
echo -e "${YELLOW}   npm create svelte@latest frontend${NC}"
echo -e "   (Choose: Skeleton, TypeScript, ESLint, Prettier)"
echo ""
echo "2. Install dependencies:"
echo -e "${YELLOW}   cd frontend${NC}"
echo -e "${YELLOW}   pnpm install${NC}"
echo -e "${YELLOW}   pnpm add -D tailwindcss postcss autoprefixer${NC}"
echo -e "${YELLOW}   pnpm add socket.io-client @tldraw/tldraw zod${NC}"
echo ""
echo "3. Copy frontend service files:"
echo -e "${YELLOW}   cp -r frontend-template/lib frontend/src/${NC}"
echo ""
echo "4. Configure Tailwind:"
echo -e "${YELLOW}   pnpm dlx tailwindcss init -p${NC}"
echo -e "   (See FRONTEND_GUIDE.md for configuration)"
echo ""
echo "5. Create .env:"
echo -e "${YELLOW}   echo 'PUBLIC_API_URL=http://localhost:8000' > .env${NC}"
echo -e "${YELLOW}   echo 'PUBLIC_WS_URL=ws://localhost:8000/api/ws/connect' >> .env${NC}"
echo ""
echo "6. Start dev server:"
echo -e "${YELLOW}   pnpm dev${NC}"
echo ""
echo "Frontend will be available at: http://localhost:5173"
echo ""

echo "=================================="
echo "  Setup Complete!"
echo "=================================="
echo ""
echo "Quick Start Guide:"
echo ""
echo "Terminal 1 - Backend:"
echo -e "  ${YELLOW}cd backend${NC}"
echo -e "  ${YELLOW}conda activate agora${NC}"
echo -e "  ${YELLOW}python -m app.main${NC}"
echo ""
echo "Terminal 2 - Frontend (after setup):"
echo -e "  ${YELLOW}cd frontend${NC}"
echo -e "  ${YELLOW}pnpm dev${NC}"
echo ""
echo "See README.md for detailed documentation"
echo "See FRONTEND_GUIDE.md for frontend implementation"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
echo ""

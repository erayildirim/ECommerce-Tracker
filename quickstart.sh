#!/bin/bash
# Quick Start Guide for E-Commerce Tracker

echo "=================================="
echo "E-Commerce Tracker - Quick Start"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}[1/4] Checking Python version...${NC}"
python --version

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${BLUE}[2/4] Creating virtual environment...${NC}"
    python -m venv venv
    source venv/Scripts/activate
else
    echo -e "${BLUE}[2/4] Activating virtual environment...${NC}"
    source venv/Scripts/activate
fi

# Install dependencies
echo -e "${BLUE}[3/4] Installing dependencies...${NC}"
pip install -r requirements.txt --quiet
playwright install --with-deps

# Setup environment
echo -e "${BLUE}[4/4] Setting up environment...${NC}"
cp .env.example .env

echo ""
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Update .env file with your database credentials"
echo "  2. Start API: python -m uvicorn src.api.main:app --reload"
echo "  3. Or use Docker: docker-compose up -d"
echo ""
echo "API Documentation: http://localhost:8000/docs"

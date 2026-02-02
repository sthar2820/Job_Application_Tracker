#!/bin/bash
# Quick run script for Job Application Tracker

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Job Application Tracker${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}Virtual environment not found!${NC}"
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
    echo ""
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import streamlit" 2>/dev/null; then
    echo -e "${RED}Dependencies not installed!${NC}"
    echo "Installing dependencies..."
    pip install -r requirements.txt
    echo -e "${GREEN}✓ Dependencies installed${NC}"
    echo ""
fi

# Check if database exists
if [ ! -f "job_applications.db" ]; then
    echo -e "${RED}Database not found!${NC}"
    echo "Initializing database..."
    python -m app.db.init_db
    echo -e "${GREEN}✓ Database initialized${NC}"
    echo ""
fi

# Check if credentials exist
if [ ! -f "credentials.json" ]; then
    echo -e "${RED}⚠️  credentials.json not found!${NC}"
    echo "Please:"
    echo "  1. Go to https://console.cloud.google.com/"
    echo "  2. Enable Gmail API"
    echo "  3. Create OAuth credentials"
    echo "  4. Download as credentials.json"
    echo ""
    exit 1
fi

# Menu
echo "Select an option:"
echo "  1) Run poller once (process new emails)"
echo "  2) Start dashboard"
echo "  3) Start continuous poller"
echo "  4) Run tests"
echo "  5) Reset database (⚠️  deletes all data)"
echo ""
read -p "Enter choice [1-5]: " choice

case $choice in
    1)
        echo -e "${GREEN}Running poller once...${NC}"
        python -m app.poller --once
        ;;
    2)
        echo -e "${GREEN}Starting dashboard...${NC}"
        streamlit run app/dashboard.py
        ;;
    3)
        echo -e "${GREEN}Starting continuous poller...${NC}"
        python -m app.poller
        ;;
    4)
        echo -e "${GREEN}Running tests...${NC}"
        python -m app.tests
        ;;
    5)
        read -p "⚠️  This will DELETE ALL DATA. Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            python -m app.db.init_db --reset
            echo -e "${GREEN}✓ Database reset${NC}"
        else
            echo "Cancelled"
        fi
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

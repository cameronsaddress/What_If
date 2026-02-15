#!/bin/bash
# What If — Quick Start

set -e

echo "What If — Setup"
echo "==============="

# Check Python
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,12) else 1)" 2>/dev/null; then
    echo "Error: Python 3.12+ required"
    exit 1
fi
echo "Python OK: $(python3 --version)"

# Virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Dependencies
echo "Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Environment
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "Edit .env with your OpenRouter API key before running."
fi

# Database
echo "Initializing database..."
python3 -c "from backend import Base, engine; Base.metadata.create_all(engine)"

echo ""
echo "Setup complete."
echo ""
echo "  1. Edit .env with your OpenRouter API key"
echo "  2. Run: streamlit run app.py"
echo "  3. Open: http://localhost:8501"
echo ""
echo "Tests: pytest test_app.py test_improvements.py -v"

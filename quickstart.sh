#!/bin/bash
# Quantum Life Fork Simulator - Quick Start Script

echo "🌊 Quantum Life Fork Simulator - Quick Setup"
echo "==========================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.12"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3,12) else 1)" 2>/dev/null; then
    echo "❌ Error: Python 3.12+ is required (found: $python_version)"
    exit 1
fi

echo "✅ Python version OK: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for .env file
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your API keys before running!"
    echo "   Required: ANTHROPIC_API_KEY or OPENAI_API_KEY"
fi

# Create database
echo "🗄️ Initializing database..."
python -c "from backend import Base, engine; Base.metadata.create_all(engine)"

echo ""
echo "✨ Setup complete!"
echo ""
echo "To run the application:"
echo "  1. Edit .env file with your API keys"
echo "  2. Run: streamlit run app.py"
echo ""
echo "For tests: pytest test_app.py -v"
echo ""
echo "Happy simulating! 🚀"
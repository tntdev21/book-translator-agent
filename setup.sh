#!/bin/bash
# Setup script for book translation project

echo "📚 Book Translation Project Setup"
echo "=================================="

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv

    echo "Installing dependencies..."
    source venv/bin/activate
    pip install -r requirements.txt

    echo "✅ Setup complete!"
else
    echo "✅ Virtual environment already exists"
fi

echo ""
echo "To activate the environment, run:"
echo "  source venv/bin/activate"
echo ""
echo "Or use the activate script:"
echo "  source activate.sh"

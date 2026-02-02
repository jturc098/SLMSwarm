#!/bin/bash

# Setup virtual environment for Project Hydra-Consensus

echo "Creating Python virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Virtual environment setup complete!"
echo ""
echo "To activate the environment:"
echo "  source venv/bin/activate"
echo ""
echo "Then run:"
echo "  export PYTHONPATH=\$PWD"
echo "  python src/hydra_control.py --init"
echo "  python src/hydra_control.py --serve"
echo ""
echo "Or use the run script: ./run.sh"
echo ""

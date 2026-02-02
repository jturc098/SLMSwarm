#!/bin/bash

# Run Project Hydra-Consensus

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Run ./setup_venv.sh first"
    exit 1
fi

# Set Python path
export PYTHONPATH=$(pwd)

# Parse command
case "$1" in
    init)
        echo "Initializing Hydra-Consensus..."
        python src/hydra_control.py --init
        ;;
    serve)
        echo "Starting Hydra Control Plane..."
        python src/hydra_control.py --serve
        ;;
    task)
        if [ -z "$2" ]; then
            echo "Usage: ./run.sh task \"Your task description\""
            exit 1
        fi
        python src/hydra_control.py --task "$2"
        ;;
    *)
        echo "Usage:"
        echo "  ./run.sh init          # Initialize system"
        echo "  ./run.sh serve         # Start control plane"
        echo "  ./run.sh task \"text\"   # Execute a task"
        exit 1
        ;;
esac
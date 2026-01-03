#!/bin/bash

# Start Backend Server
echo "Starting Backend Server..."

# Check if virtual environment exists, if not create one
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment
echo "Activating virtual environment..."
source backend/venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
cd backend
pip install -r requirements.txt

# Start the server
echo "Starting FastAPI server on http://localhost:8000"
uvicorn app.main:app --reload


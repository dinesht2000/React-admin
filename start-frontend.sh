#!/bin/bash

# Start Frontend Server
echo "Starting Frontend Server..."

cd frontend

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start the development server
echo "Starting React development server on http://localhost:3000"
npm start


#!/bin/bash

# Start All Services
echo "=========================================="
echo "Starting All Services"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker first."
    exit 1
fi

# Start PostgreSQL with Docker Compose
echo ""
echo "Starting PostgreSQL database..."
docker-compose up -d

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
sleep 5

# Check if PostgreSQL is ready
until docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
    echo "Waiting for PostgreSQL..."
    sleep 2
done

echo "PostgreSQL is ready!"
echo ""

# Seed database with initial users
echo "Seeding database with initial users..."
if [ ! -d "backend/venv" ]; then
    echo "Creating virtual environment..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# Activate virtual environment and run seed script
source backend/venv/bin/activate
cd backend
pip install -q -r requirements.txt
python seed_users.py
cd ..
deactivate

echo ""

# Start Frontend
echo "Starting Frontend Server..."
./start-frontend.sh &
FRONTEND_PID=$!


# Start Backend in background
echo "Starting Backend Server..."
./start-backend.sh &
BACKEND_PID=$!


# Function to cleanup on exit
cleanup() {
    echo ""
    echo "Shutting down services..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    docker-compose down
    exit
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Wait for processes
wait


#!/bin/bash

# Smart Attendance System - Deployment Script

set -e

echo "=== Smart Attendance System Deployment ==="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Installing..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
    echo "Please log out and log back in for Docker permissions to take effect."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Installing..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    
    # Generate a random secret key
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s/your-super-secret-key-change-me/$SECRET_KEY/" .env
    
    echo "Please edit .env file with your settings."
fi

# Create necessary directories
mkdir -p data ai/models certs

# Build and start containers
echo "Building and starting services..."
docker-compose up -d --build

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Frontend: http://localhost"
echo "Backend: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Next steps:"
echo "1. Create an admin user: curl -X POST http://localhost:8000/api/auth/register -H 'Content-Type: application/json' -d '{\"username\": \"admin\", \"password\": \"admin123\", \"role\": \"admin\"}'"
echo "2. Login at http://localhost"
echo "3. Add students and enroll their faces"
echo "4. Start the camera to begin attendance tracking"

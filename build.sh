#!/bin/bash

# AI Receptionist Pro Build Script

echo "========================================"
echo "AI Receptionist Pro Build Script"
echo "========================================"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed."
    echo "Please install Node.js (v16 or higher) before proceeding."
    echo "Visit https://nodejs.org/ to download and install Node.js."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d 'v' -f 2)
NODE_MAJOR_VERSION=$(echo $NODE_VERSION | cut -d '.' -f 1)
if [ "$NODE_MAJOR_VERSION" -lt 16 ]; then
    echo "Error: Node.js version $NODE_VERSION is not supported."
    echo "Please upgrade to Node.js v16 or higher."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed."
    echo "Please install npm before proceeding."
    exit 1
fi

echo "Node.js version: $(node -v)"
echo "npm version: $(npm -v)"

echo "\nBuilding AI Receptionist Pro..."

# Install frontend dependencies
echo "\n[1/3] Installing frontend dependencies..."
cd frontend || { echo "Error: frontend directory not found."; exit 1; }
npm install || { echo "Error: Failed to install frontend dependencies."; exit 1; }

# Build frontend
echo "\n[2/3] Building frontend..."
npm run build || { echo "Error: Failed to build frontend."; exit 1; }

# Install backend dependencies
echo "\n[3/3] Installing backend dependencies..."
cd ../backend || { echo "Error: backend directory not found."; exit 1; }
npm install || { echo "Error: Failed to install backend dependencies."; exit 1; }

echo "\n========================================"
echo "Build completed successfully!"
echo "========================================"

echo "\nTo start the application:"
echo "1. Start the backend server:"
echo "   cd backend && npm start"
echo "2. Start the frontend server:"
echo "   cd frontend && npm start"

echo "\nFor development mode:"
echo "1. Start the backend server in dev mode:"
echo "   cd backend && npm run dev"
echo "2. Start the frontend server in dev mode:"
echo "   cd frontend && npm run dev"

echo "\nRefer to README.md for more information."
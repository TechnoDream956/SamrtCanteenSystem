#!/usr/bin/env bash
# exit on error
set -o errexit

# 1. Install Python dependencies
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
elif [ -f "web_server/requirements.txt" ]; then
    pip install -r web_server/requirements.txt
fi

# 2. Compile C++ Canteen Engine for Linux (Render)
# We use -O3 for maximum performance in production
echo "🔨 Compiling C++ Canteen Engine for Render (Linux)..."
# Move to the project root for compilation
cd ..
mkdir -p backend/bin
g++ -O3 -o backend/bin/canteen_tool \
    backend/bin/canteen_tool.cpp \
    backend/services/AuthService.cpp \
    backend/services/CanteenService.cpp \
    -Ibackend/services

# 3. Ensure binary is executable
chmod +x backend/bin/canteen_tool

echo "✅ Build Complete: Backend + C++ Engine ready."

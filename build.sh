#!/bin/bash

# Build the Svelte frontend
echo "Building Svelte frontend..."
cd frontend
npm run build

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "Frontend build completed successfully!"
    echo "Static files are now in frontend/build/"
    echo ""
    echo "You can now run the application with:"
    echo "python main.py"
    echo ""
    echo "The app will be available at http://localhost:8000"
else
    echo "Frontend build failed!"
    exit 1
fi

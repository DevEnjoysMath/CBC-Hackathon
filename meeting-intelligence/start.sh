#!/bin/bash

echo "===================================="
echo "🚀 NEXUS - Meeting Intelligence"
echo "===================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"

# Check if API key is set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  Warning: ANTHROPIC_API_KEY is not set!"
    echo "   Please set it with: export ANTHROPIC_API_KEY='your-key-here'"
    echo ""
    read -p "Do you want to continue anyway? (demo mode) [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✅ Claude API key found"
fi

# Check if OpenAI key is set (optional)
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OpenAI API key not set (will use mock transcription)"
else
    echo "✅ OpenAI API key found"
fi

echo ""
echo "Installing dependencies..."
pip install -q -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    exit 1
fi

echo "✅ Dependencies installed"
echo ""
echo "===================================="
echo "🎉 Starting NEXUS server..."
echo "===================================="
echo ""
echo "📡 Server will be available at:"
echo "   http://localhost:5000"
echo ""
echo "💡 Quick tips:"
echo "   - Click 'Quick Demo' for instant results"
echo "   - Or paste your own meeting transcript"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 server.py

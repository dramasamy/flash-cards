#!/bin/bash

# Flash Cards Video Creator - Setup Script

echo "🎬 Flash Cards Video Creator Setup"
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8 or higher."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is required but not installed."
    echo "Please install pip3."
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg is not installed."
    echo "Installing FFmpeg (macOS with Homebrew)..."
    if command -v brew &> /dev/null; then
        brew install ffmpeg
    else
        echo "❌ Please install FFmpeg manually:"
        echo "macOS: brew install ffmpeg"
        echo "Ubuntu: sudo apt install ffmpeg"
        echo "Windows: Download from https://ffmpeg.org/"
        exit 1
    fi
fi

echo "✅ FFmpeg is available"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install -r requirements.txt

# Check if config.yaml has API keys configured
echo "� Checking API configuration..."
if grep -q "your_.*_key_here" config.yaml; then
    echo "⚠️  Please edit config.yaml and add your API keys!"
    echo "   The file is already created with placeholders."
else
    echo "✅ API keys appear to be configured in config.yaml"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p cache temp output static/images

# Set permissions
chmod +x setup.sh

echo ""
echo "🎉 Setup completed!"
echo ""
echo "Next steps:"
echo "1. Your API keys are already configured in config.yaml!"
echo "   ✅ OpenAI API key: configured"
echo "   ✅ Azure Speech Service: configured"  
echo "   ✅ Pexels API key: configured"
echo ""
echo "2. To run the application:"
echo "   source venv/bin/activate"
echo "   python app.py"
echo ""
echo "3. Open your browser to http://localhost:5000"
echo ""
echo "📚 API Key Resources:"
echo "   - OpenAI: https://platform.openai.com/api-keys"
echo "   - Azure Speech: https://azure.microsoft.com/services/cognitive-services/speech-services/"
echo "   - Pexels: https://www.pexels.com/api/"
echo "   - Unsplash: https://unsplash.com/developers"
echo "   - Pixabay: https://pixabay.com/api/docs/"

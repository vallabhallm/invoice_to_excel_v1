#!/bin/bash
# Quick setup and run script

echo "🚀 Invoice Processor Quick Start"

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies
echo "📦 Installing dependencies..."
poetry install

# Setup application
echo "🔧 Setting up application..."
poetry run invoice-processor setup

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Edit .env file and add your AI API keys"
echo "2. Place invoice files in data/input/"
echo "3. Run: poetry run invoice-processor process"
echo ""
echo "💡 Pro tip: Run 'poetry run invoice-processor status' to check configuration"

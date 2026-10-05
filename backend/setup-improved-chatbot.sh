#!/bin/bash

echo "🔧 Setting up improved ChatBot backend..."

# Install new dependencies
echo "📦 Installing LangChain dependencies..."
pip install -r requirements.txt

# Pull better model
echo "🤖 Pulling improved LLM model (llama3.2:3b)..."
ollama pull llama3.2:3b

echo "✅ Setup complete! Restart the backend server to use the new model."
echo ""
echo "📋 Changes made:"
echo "- Upgraded from gemma3:1b to llama3.2:3b (3x larger model)"
echo "- Added LangChain for better prompt management"
echo "- Improved prompt engineering with system instructions"
echo "- Better temperature and token settings"
echo ""
echo "🚀 To start the backend:"
echo "cd backend"
echo "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

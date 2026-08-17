#!/bin/bash
# One-line installer for qwen-code-agent

set -e

echo "🚀 Installing Qwen Code Agent..."

# Remove existing installation
if [ -d ~/.qwen-code-agent ]; then
    rm -rf ~/.qwen-code-agent
fi

# Clone repo
git clone https://github.com/ParthParikh-240906/qwen-code-agent.git ~/.qwen-code-agent
cd ~/.qwen-code-agent

# Install dependencies
pip3 install -r requirements.txt

# Check if GROQ_API_KEY is provided as environment variable
if [ -z "$GROQ_API_KEY" ]; then
    # Try to copy from existing project if it exists
    if [ -f ~/projects/qwen-code-agent/.env ]; then
        cp ~/projects/qwen-code-agent/.env .env
        echo "✓ Copied .env from existing project"
    else
        # Create template
        echo "GROQ_API_KEY=YOUR_KEY_HERE" > .env
        echo "GROQ_MODEL=openai/gpt-oss-20b" >> .env
        echo "GROQ_ORCHESTRATOR_MODEL=openai/gpt-oss-120b" >> .env
        echo "USE_GROQ_FOR_GENERATE=true" >> .env
        echo "⚠️  Add your Groq API key to ~/.qwen-code-agent/.env"
    fi
else
    # Use environment variable
    echo "GROQ_API_KEY=$GROQ_API_KEY" > .env
    echo "GROQ_MODEL=openai/gpt-oss-20b" >> .env
    echo "GROQ_ORCHESTRATOR_MODEL=openai/gpt-oss-120b" >> .env
    echo "USE_GROQ_FOR_GENERATE=true" >> .env
    echo "✓ API key set from environment"
fi

# Add aliases
echo "🔧 Setting up aliases..."
echo "" >> ~/.zshrc
echo "# Qwen Code Agent" >> ~/.zshrc
echo 'alias qsummarize="python3 ~/.qwen-code-agent/agent.py summarize"' >> ~/.zshrc
echo 'alias qexplain="python3 ~/.qwen-code-agent/agent.py explain"' >> ~/.zshrc
echo 'alias qgenerate="python3 ~/.qwen-code-agent/agent.py qgenerate-fast"' >> ~/.zshrc
echo 'alias qsearch="python3 ~/.qwen-code-agent/agent.py qsearch"' >> ~/.zshrc
echo 'alias qresearch="python3 ~/.qwen-code-agent/agent.py qresearch"' >> ~/.zshrc
echo 'alias qbuild="python3 ~/.qwen-code-agent/agent.py qbuild"' >> ~/.zshrc

echo ""
echo "✅ Installation complete!"
echo ""
echo "Run this to activate:"
echo "  source ~/.zshrc"
echo ""
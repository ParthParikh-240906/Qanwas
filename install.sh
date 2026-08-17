#!/bin/bash
# One-line installer for qwen-code-agent

set -e

echo "🚀 Installing Qwen Code Agent..."

# Check if already installed
if [ -d ~/.qwen-code-agent ]; then
    echo "📦 Already installed! Updating..."
    cd ~/.qwen-code-agent
    git pull
    pip3 install -r requirements.txt
    source ~/.zshrc
    echo "✅ Updated! Try: qbuild 'create a hello world app'"
    exit 0
fi

# 1. Clone repo
echo "📥 Cloning repository..."
git clone https://github.com/ParthParikh-240906/qwen-code-agent.git ~/.qwen-code-agent
cd ~/.qwen-code-agent

# 2. Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# 3. Setup .env
if [ ! -f .env ]; then
    echo ""
    echo "🔑 Enter your Groq API key (from https://console.groq.com):"
    read -p "API Key: " GROQ_KEY
    echo "GROQ_API_KEY=$GROQ_KEY" > .env
    echo "GROQ_MODEL=openai/gpt-oss-20b" >> .env
    echo "GROQ_ORCHESTRATOR_MODEL=openai/gpt-oss-120b" >> .env
    echo "USE_GROQ_FOR_GENERATE=true" >> .env
    echo "✓ API key saved to .env"
fi

# 4. Add aliases (only if not already added)
echo "🔧 Setting up aliases..."
if ! grep -q "qwen-code-agent" ~/.zshrc; then
    echo "" >> ~/.zshrc
    echo "# Qwen Code Agent" >> ~/.zshrc
    echo 'alias qsummarize="python3 ~/.qwen-code-agent/agent.py summarize"' >> ~/.zshrc
    echo 'alias qexplain="python3 ~/.qwen-code-agent/agent.py explain"' >> ~/.zshrc
    echo 'alias qgenerate="python3 ~/.qwen-code-agent/agent.py qgenerate-fast"' >> ~/.zshrc
    echo 'alias qsearch="python3 ~/.qwen-code-agent/agent.py qsearch"' >> ~/.zshrc
    echo 'alias qresearch="python3 ~/.qwen-code-agent/agent.py qresearch"' >> ~/.zshrc
    echo 'alias qbuild="python3 ~/.qwen-code-agent/agent.py qbuild"' >> ~/.zshrc
else
    echo "✓ Aliases already exist"
fi

# 5. Reload shell
source ~/.zshrc

echo ""
echo "✅ Installation complete!"
echo ""
echo "Available commands:"
echo "  qsummarize <file>     - Summarize a code file"
echo "  qexplain <file>       - Explain a code file"
echo "  qgenerate <prompt>    - Generate code (GPT-OSS-20B)"
echo "  qsearch <question>    - Web search with grounded answer"
echo "  qresearch <topic>     - Deep research"
echo "  qbuild <request>      - Multi-agent orchestration"
echo ""
echo "Try: qbuild 'create a hello world app'"
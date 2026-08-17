#!/bin/bash
# One-line installer for qwen-code-agent

set -e

echo "🚀 Installing Qwen Code Agent..."

# Remove existing installation and aliases
if [ -d ~/.qwen-code-agent ]; then
    echo "📦 Removing existing installation..."
    rm -rf ~/.qwen-code-agent
fi

# Remove old aliases
sed -i '' '/alias qsummarize/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qexplain/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qgenerate/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qsearch/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qresearch/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qbuild/d' ~/.zshrc 2>/dev/null || true

# Clone repo
echo "📥 Cloning repository..."
git clone https://github.com/ParthParikh-240906/qwen-code-agent.git ~/.qwen-code-agent
cd ~/.qwen-code-agent

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Setup .env
echo ""
echo "🔑 Enter your Groq API key (from https://console.groq.com):"
read -p "API Key: " GROQ_KEY
echo "GROQ_API_KEY=$GROQ_KEY" > .env
echo "GROQ_MODEL=openai/gpt-oss-20b" >> .env
echo "GROQ_ORCHESTRATOR_MODEL=openai/gpt-oss-120b" >> .env
echo "USE_GROQ_FOR_GENERATE=true" >> .env
echo "✓ API key saved"

# Add aliases
echo "🔧 Setting up aliases..."
echo "" >> ~/.zshrc
echo "# Qwen Code Agent" >> ~/.zshrc
echo 'alias qsummarize="python3 ~/.qwen-code-agent/agent.py summarize"' >> ~/.zshrc
echo 'alias qexplain="python3 ~/.qwen-code-agent/agent.py explain"' >> ~/.zshrc
echo 'alias qgenerate="python3 ~/.qwen-code-agent/agent.py qgenerate-fast"' >> ~/.zshrc
echo 'alias qgenerate-fast="python3 ~/.qwen-code-agent/agent.py qgenerate-fast"' >> ~/.zshrc
echo 'alias qsearch="python3 ~/.qwen-code-agent/agent.py qsearch"' >> ~/.zshrc
echo 'alias qresearch="python3 ~/.qwen-code-agent/agent.py qresearch"' >> ~/.zshrc
echo 'alias qbuild="python3 ~/.qwen-code-agent/agent.py qbuild"' >> ~/.zshrc

echo ""
echo "✅ Installation complete!"
echo ""
echo "Run this to activate:"
echo "  source ~/.zshrc"
echo ""
echo "Then try:"
echo "  qbuild 'create a hello world app'"
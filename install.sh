#!/bin/bash
# One-line installer for qwen-code-agent V5

set -e

echo "🚀 Installing Qwen Code Agent V5..."

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

# Remove old aliases first
sed -i '' '/alias qsummarize/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qexplain/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qgenerate/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qsearch/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qresearch/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qbuild/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/# Qwen Code Agent/d' ~/.zshrc 2>/dev/null || true

# Add aliases
echo "🔧 Setting up aliases..."
echo "" >> ~/.zshrc
echo "# Qwen Code Agent V5" >> ~/.zshrc
echo 'alias qsummarize="python3 ~/.qwen-code-agent/agent.py summarize"' >> ~/.zshrc
echo 'alias qexplain="python3 ~/.qwen-code-agent/agent.py explain"' >> ~/.zshrc
echo 'alias qgenerate="python3 ~/.qwen-code-agent/agent.py generate"' >> ~/.zshrc
echo 'alias qsearch="python3 ~/.qwen-code-agent/agent.py qsearch"' >> ~/.zshrc
echo 'alias qresearch="python3 ~/.qwen-code-agent/agent.py qresearch"' >> ~/.zshrc
echo 'alias qbuild="python3 ~/.qwen-code-agent/agent.py qbuild"' >> ~/.zshrc
echo 'alias qmodify="python3 ~/.qwen-code-agent/agent.py qmodify"' >> ~/.zshrc

echo ""
echo "✅ Installation complete!"
echo ""
echo "Run this to activate:"
echo "  source ~/.zshrc"
echo ""
echo "Available commands:"
echo "  qsummarize <file>     - Summarize code file"
echo "  qexplain <file>       - Explain code file"
echo "  qgenerate <prompt>    - Generate code"
echo "  qsearch <question>    - Web search"
echo "  qresearch <topic>     - Deep research"
echo "  qbuild <request>      - Build complete project"
echo ""
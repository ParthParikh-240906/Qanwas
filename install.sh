#!/bin/bash
# One-line installer for Qanwas

echo "🚀 Installing Qanwas..."

# Remove existing installation
if [ -d ~/.qanwas ]; then
    rm -rf ~/.qanwas
fi

# Clone repo
git clone https://github.com/ParthParikh-240906/Qanwas.git ~/.qanwas
cd ~/.qanwas

# Install dependencies
pip3 install -r requirements.txt

# Check for API key
if [ -z "$GROQ_API_KEY" ]; then
    if [ -f ~/projects/Qanwas/.env ]; then
        cp ~/projects/Qanwas/.env .env
        echo "✓ Copied .env from existing project"
    else
        echo "GROQ_API_KEY=YOUR_KEY_HERE" > .env
        echo "GROQ_MODEL=openai/gpt-oss-20b" >> .env
        echo "GROQ_ORCHESTRATOR_MODEL=openai/gpt-oss-120b" >> .env
        echo "⚠️  Add your Groq API key to ~/.qanwas/.env"
    fi
else
    echo "GROQ_API_KEY=$GROQ_API_KEY" > .env
    echo "GROQ_MODEL=openai/gpt-oss-20b" >> .env
    echo "GROQ_ORCHESTRATOR_MODEL=openai/gpt-oss-120b" >> .env
    echo "✓ API key set from environment"
fi

# Remove old aliases
sed -i '' '/alias qsummarize/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qexplain/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qgenerate/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qsearch/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qresearch/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qbuild/d' ~/.zshrc 2>/dev/null || true
sed -i '' '/alias qmodify/d' ~/.zshrc 2>/dev/null || true

# Add new aliases
echo "" >> ~/.zshrc
echo "# Qanwas" >> ~/.zshrc
echo 'alias qsummarize="python3 ~/.qanwas/agent.py summarize"' >> ~/.zshrc
echo 'alias qexplain="python3 ~/.qanwas/agent.py explain"' >> ~/.zshrc
echo 'alias qgenerate="python3 ~/.qanwas/agent.py generate"' >> ~/.zshrc
echo 'alias qsearch="python3 ~/.qanwas/agent.py qsearch"' >> ~/.zshrc
echo 'alias qresearch="python3 ~/.qanwas/agent.py qresearch"' >> ~/.zshrc
echo 'alias qbuild="python3 ~/.qanwas/agent.py qbuild"' >> ~/.zshrc
echo 'alias qmodify="python3 ~/.qanwas/agent.py qmodify"' >> ~/.zshrc

echo ""
echo "✅ Qanwas installed!"
echo "Run: source ~/.zshrc"
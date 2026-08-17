#!/bin/bash
# One-line installer for qwen-code-agent

set -e

echo "🚀 Installing Qwen Code Agent..."

# 1. Clone repo
git clone https://github.com/ParthParikh-240906/qwen-code-agent.git ~/.qwen-code-agent
cd ~/.qwen-code-agent

# 2. Install dependencies
pip3 install -r requirements.txt

# 3. Setup .env
if [ ! -f .env ]; then
    echo "Enter your Groq API key (from https://console.groq.com):"
    read GROQ_KEY
    echo "GROQ_API_KEY=$GROQ_KEY" > .env
    echo "GROQ_MODEL=openai/gpt-oss-20b" >> .env
    echo "GROQ_ORCHESTRATOR_MODEL=openai/gpt-oss-120b" >> .env
fi

# 4. Add aliases
echo 'alias qsummarize="python3 ~/.qwen-code-agent/agent.py summarize"' >> ~/.zshrc
echo 'alias qexplain="python3 ~/.qwen-code-agent/agent.py explain"' >> ~/.zshrc
echo 'alias qgenerate="python3 ~/.qwen-code-agent/agent.py qgenerate-fast"' >> ~/.zshrc
echo 'alias qsearch="python3 ~/.qwen-code-agent/agent.py qsearch"' >> ~/.zshrc
echo 'alias qresearch="python3 ~/.qwen-code-agent/agent.py qresearch"' >> ~/.zshrc
echo 'alias qbuild="python3 ~/.qwen-code-agent/agent.py qbuild"' >> ~/.zshrc

source ~/.zshrc

echo "✅ Done! Try: qbuild 'create a hello world app'"
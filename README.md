# AgentsTeam

AI-powered CLI for generating complete, working projects and auto-fixing errors. Local-first with Ollama, cloud fallback with OpenAI. Optimized for gpt-oss models.

- Local-first: prefers Ollama (privacy, speed, no limits)
- gpt-oss priority: selects gpt-oss:20b when available
- Cloud fallback: OpenAI (gpt-4o, gpt-4o-mini) when needed
- Clean generation: prompts tuned for “code only” output
- Intelligent fixer: detects errors and applies safe, AI-generated fixes with backups
- Model scanning: supports multiple Ollama hosts (LAN GPUs, localhost)

## Table of Contents
- Overview
- Project Structure
- Installation & Setup
- Configuration
- Quick Start
- Usage
  - Interactive Shell
  - Direct Generation
  - Model Management
  - Error Correction
- Intelligent Model Selection
- Examples
- Architecture
- Commands Reference (Quick)
- Best Practices
- Disclaimer
- License

## Overview
AgentsTeam brings AI into your terminal: describe what you want, and it generates full projects, files, and tests. It can also run commands, detect errors, and fix them automatically.

## Project Structure
```
AgentsTeam/
├── cli/                    # Core CLI interface and shell
│   ├── core/               # Code generation, model selection, project analysis, error correction
│   ├── clients/            # AI provider clients (Ollama, OpenAI)
│   └── utils/              # Configuration and logging utilities
├── projects/               # Example/generated projects
│   ├── tetris-game/
│   ├── snake-game/
│   ├── system-monitor/
│   └── gui-calculator/
├── requirements.txt
├── setup.py
└── README.md
```

## Installation & Setup

Prerequisites:
- Python 3.8+
- Git
- Ollama (recommended)

Install Ollama and pull a model:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the recommended local coding model
ollama pull gpt-oss:20b
```

Install AgentsTeam:
```bash
git clone https://github.com/dexmac221/AgentsTeam.git
cd AgentsTeam
pip install -r requirements.txt
pip install -e .
```

## Configuration
Use CLI config or environment variables.

CLI:
```bash
# OpenAI (optional)
agentsteam config --openai-key sk-...

# Single Ollama URL (default)
agentsteam config --ollama-url http://localhost:11434

# Multiple Ollama hosts to scan (comma-separated)
agentsteam config --ollama-hosts "http://192.168.1.62:11434,http://localhost:11434"

# Show current settings
agentsteam config --show
```

Environment variables (alternatives):
```bash
export OPENAI_API_KEY="sk-..."
export OLLAMA_BASE_URL="http://localhost:11434"
export OLLAMA_HOSTS="http://192.168.1.62:11434,http://localhost:11434"
```

Notes:
- When multiple hosts are configured, AgentsTeam scans each host and picks the first one with the preferred model (gpt-oss:20b > gpt-oss > other coding models).
- The selected host is used for both generation and fixes.

## Quick Start
Best practice: work inside the projects/ directory so generated files stay isolated from the framework.
```bash
mkdir -p projects/my-app && cd projects/my-app

# Start interactive shell
agentsteam shell

# Or generate directly
agentsteam generate "Simple CLI that prints current date/time" --tech python

# List models (per-host inventories)
agentsteam models
```

## Usage
### Interactive Shell (recommended)
```bash
agentsteam shell
```
- Conversational coding with context
- Built-in commands (help, ls, cat, read, edit, run, etc.)
- Intelligent model selection

Examples:
```
[AgentsTeam] 🤖 create a FastAPI web service for managing books
[AgentsTeam] 🤖 edit main.py to add authentication middleware
[AgentsTeam] 🤖 /fix main.py
```

### Direct Generation
```bash
# Basic project
agentsteam generate "Simple REST API for blog posts"

# With technologies
agentsteam generate "Tetris game" --tech python,pygame

# Force a specific model
agentsteam generate "..." --model ollama:gpt-oss:20b
agentsteam generate "..." --model openai:gpt-4o
```

### Model Management
```bash
agentsteam models
```
- Shows Ollama models per configured host
- Shows OpenAI models if API key set

### Error Correction
```bash
# Run a command with auto-fix loop
agentsteam fix --run-command "python main.py" --max-attempts 3

# Fix a specific file
agentsteam fix --file main.py
```

Improved fixer (latest):
- Robust code extraction from AI responses (multiple strategies)
- Strict retry mode requesting a single fenced code block
- Safe writes with .backup files

Tip: Use --debug with fix to view applied changes.

## Intelligent Model Selection
Priority order:
1) Local gpt-oss:20b (preferred)
2) Other local coding models (qwen2.5-coder, codellama, llama3.* etc.)
3) OpenAI gpt-4o / gpt-4o-mini

Model scanning across multiple Ollama hosts (LAN GPUs, localhost). Selects the first host with the preferred model and reuses that host consistently.

## Examples
Example projects included:
- projects/tetris-game
- projects/snake-game
- projects/system-monitor
- projects/gui-calculator

You can run them from their directories; see each subfolder’s README or main file.

## Architecture
AgentsTeam uses modular components:
- ModelSelector: picks local/cloud model and scans Ollama hosts
- CodeGenerator: prompts provider for plan/files and writes code
- ErrorCorrector: detects and fixes errors with AI, using backups
- Clients: Ollama (local) and OpenAI (cloud)
- Utils: config and logging

## Commands Reference (Quick)
- agentsteam shell
- agentsteam models
- agentsteam config --show
- agentsteam config --openai-key sk-...
- agentsteam config --ollama-url http://host:11434
- agentsteam config --ollama-hosts "http://host1:11434,http://host2:11434"
- agentsteam generate "desc" [--tech ...] [--model ...] [-o dir]
- agentsteam fix --run-command "..." [--max-attempts N]
- agentsteam fix --file path/to/file

## Best Practices
- Always work inside projects/ to isolate generated code
- Be specific with prompts for better results
- If a generation looks incomplete, retry; then refine the prompt

## Disclaimer
AI-generated code may contain bugs or vulnerabilities. Review and test before production use. Ensure license compatibility of dependencies.

## License
MIT. See LICENSE.
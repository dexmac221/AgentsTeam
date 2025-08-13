# AgentsTeam

AI-powered CLI for generating complete, working projects and auto-fixing errors. Local-first with Ollama, cloud fallback with OpenAI. Optimized for gpt-oss models.

- Local-first: prefers Ollama (privacy, speed, no limits)
- gpt-oss priority: selects gpt-oss:20b when available
- Cloud fallback: OpenAI (gpt-4o, gpt-4o-mini) when needed
- Clean generation: prompts tuned for “code only” output
- Live streaming: see model output as it’s generated (default on)
- Code-only enforcement: file content remains code without markdown noise
- Intelligent fixer: detects errors and applies safe, AI-generated fixes with backups
- In-place improvements: improve existing files with streaming and backups
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
  - Improving Existing Code
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
agentsteam generate "Simple CLI that prints current date/time" --tech python --stream --verbose

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

# Streaming options
agentsteam generate "..." --no-stream   # disable live streaming
agentsteam generate "..." --stream -v   # stream with verbose on-chunk printing
```

### Improving Existing Code
```bash
# Improve a file in place (creates .backup)
agentsteam improve path/to/file.py -d "Add CLI flags --rows/--cols/--gens; keep no external deps" --stream --show-diff

# Force a specific model
agentsteam improve path/to/file.py -d "Refactor for readability" --model openai:gpt-4o
```
The shell also supports improvements interactively:
```
/improve main.py "Add ANSI colors and a --pattern option; no external deps"
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

# Recursive scan (Python): run without args to scan the repo
agentsteam fix
```

Improved fixer (latest):
- Robust code extraction from AI responses (multiple strategies)
- Strict retry mode requesting a single fenced code block
- Safe writes with .backup files

Tip: Use --debug with fix to view applied changes.

Validators and toolchains:
- Python: py_compile
- JavaScript: node --check
- TypeScript: tsc --noEmit (requires tsc)
- Go: go build
- Java: javac
- C: cc/gcc/clang -fsyntax-only
- C++: c++/g++/clang++ -fsyntax-only
- Rust: rustc --emit=metadata

Notes:
- Validators run only if the corresponding toolchain is installed; otherwise validation is skipped for that file.
- Recursive Python scan ignores common folders (.git, .venv, venv, node_modules, __pycache__, dist, build, .mypy_cache, .pytest_cache, .idea, .vscode) and caps at 200 files for speed.

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
- projects/example-fastapi (generated via gpt-oss:20b local model)

### Conway's Game of Life (no external dependencies)
This walkthrough shows how to create a tiny, single-file template and iterate on it.

1) Generate the initial template (streamed)
```bash
agentsteam generate "Single-file Python Conway's Game of Life that prints an ASCII board to the terminal; no external dependencies" \
  --tech python \
  -o projects/game-of-life \
  --stream --verbose
```

2) Run it
```bash
python projects/game-of-life/main.py
```

3a) Improve via CLI (adds flags, ANSI colors, patterns)
```bash
agentsteam improve projects/game-of-life/main.py \
  -d "Add argparse with --rows, --cols, --gens, and --pattern (glider, blinker, random with optional --seed); render alive cells in green; keep no external deps" \
  --stream --show-diff

# Try the new flags
python projects/game-of-life/main.py --rows 15 --cols 30 --gens 20 --pattern blinker
```

3b) Or improve from the interactive shell
```
cd projects/game-of-life
agentsteam shell
/improve main.py "Add ANSI green cells and --rows/--cols/--gens/--pattern; no external deps"
```

Notes:
- File content generation is enforced to be code-only to avoid markdown artifacts.
- If your description says “no external dependencies”, AgentsTeam will keep requirements.txt empty.

### Generated FastAPI Example (local gpt-oss:20b)
Command used:
```bash
agentsteam generate "Minimal FastAPI API with one /health endpoint" --tech python,fastapi -o projects/example-fastapi
```
Key file (`projects/example-fastapi/app.py`):
```python
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", version=app.version)
```
Run it:
```bash
cd projects/example-fastapi
pip install -r requirements.txt
python main.py  # or: uvicorn app:app --reload
curl http://127.0.0.1:8000/health
```

You can run them from their directories; see each subfolder’s README or main file.

## Architecture
AgentsTeam uses modular components:
- ModelSelector: picks local/cloud model and scans Ollama hosts
- CodeGenerator: prompts provider for plan/files and writes code; file content uses strict code-only prompts and streaming. Plans and setup instructions stay as plain text.
- ErrorCorrector: detects and fixes errors with AI, using backups
- Clients: Ollama (local) and OpenAI (cloud)
- Utils: config and logging

### Try/Error Incremental Builder Status
Implemented:
- LLM step planning (small incremental steps)
- Minimal scaffold bootstrap (main.py + README)
- Per-step JSON file change generation & application (changed/new files only)
- Diff tracking & introspection (recent diffs, stdout/stderr, applied files fed back to model)
- Dynamic run command inference (re-evaluates each step; switches to pytest only when test files exist)
- Expected substring gating on non-pytest runs (`--expect`)
- Adaptive multi-attempt fix loop (up to 3 single-attempt internal fixer cycles; configurable via `--fix-attempts`)
- ImportError heuristic stub injection for simple missing greeting function
- Path safety (prevent writes outside target project)
- State persistence (.agentsteam_state.json)
- Resume from persisted state (`--resume` to skip completed steps)
- Stagnation reflection recovery (auto micro-step rewrite after repeated no-change cycles)
- Large diff guard with reduction request (oversize change shrink request)
- Automatic Python dependency detection & requirements.txt updates
- Targeted multi-file fix reasoning (stack trace candidate prioritization)
- Assertion-aware expectation handling (server probe fallback for web apps)
- HTTP server probing for expectations (`--probe` support, heuristic endpoints)
- README auto-update with progress table (last 25 steps)
- Progress JSON log (.agentsteam_progress.json)
- Rollback snapshots with automatic re-plan after rollback
- Branching candidate patch evaluation & scoring (`--candidates`)
- Structured pytest failure parsing (basic) included in introspection
- Negative memory (hash-based) to skip repeating failed patches
- Semantic negative memory (similarity detection to avoid near-duplicate failed patches)
- Selective file-level rollback (revert only current step's changed files before full snapshot rollback)

Planned / Not Yet Implemented:
- Richer pytest failure semantic analysis feeding targeted suggestions
- Advanced dependency version inference (pinning popular versions)
- Multi-run adaptive probing strategies (POST /metrics etc.)
- Semantic clustering of negative memory entries with summaries
- Coverage-aware / test-pass-rate candidate scoring heuristics
- Selective partial snapshot rollback (file subset diff scoring)

---
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
- agentsteam try-error "desc" [--tech ...] [--model ...] [--max-steps N] [--plan-only]
- agentsteam improve path/to/file.py -d "changes" [--model ...] [--stream|--no-stream] [--show-diff]

## Best Practices
- Always work inside projects/ to isolate generated code
- Be specific with prompts for better results
- If a generation looks incomplete, retry; then refine the prompt
- For complex goals, use `try-error` to climb from a minimal scaffold using incremental validation

## Disclaimer
AI-generated code may contain bugs or vulnerabilities. Review and test before production use. Ensure license compatibility of dependencies.

Generated projects are starter templates/scaffolds: they aim to give you a structured baseline (files, layout, example code) but are not guaranteed to run end‑to‑end without:
- Installing and pinning any missing dependencies
- Filling in TODOs / implementation gaps
- Adding configuration (env vars, database URLs, credentials)
- Writing additional tests and hardening security

Always treat outputs as a draft to refine, not production‑ready software.

## License
MIT. See LICENSE.

<!-- TRY_ERROR_PROGRESS_START -->
### Incremental Progress

Step | Status | Files | Notes
--- | --- | --- | ---
<!-- TRY_ERROR_PROGRESS_END -->
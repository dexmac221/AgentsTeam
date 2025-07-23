# AgentsTeam

AgentsTeam is an AI-powered development framework that enables intelligent code generation, project creation, and automated development workflows through CLI interaction.

## 🚀 Features

- **Intelligent Project Generation**: Create complete, production-ready projects with complex architectures
- **Interactive AI Shell**: Conversational coding with AI models for real-time development
- **Multi-Domain Expertise**: Supports web development, computer vision, data analysis, and more
- **CLI-First Approach**: Optimized for command-line interaction and automation
- **Real Implementation**: Generates actual working code, not just templates or boilerplate
- **Agent Collaboration**: Multiple AI agents can work together on complex tasks
- **Multi-Provider Support**: Works with both local Ollama models and OpenAI cloud models
- **Autonomous Execution**: Set targets and let AI work autonomously with real-time progress tracking
- **Intelligent Error Correction**: Automatic compilation error detection and fixing with AI assistance

## 📁 Project Structure

```
AgentsTeam/
├── cli/                    # Core CLI interface and shell
│   ├── core/              # Code generation, model selection, project analysis
│   ├── clients/           # AI provider clients (Ollama, OpenAI)
│   └── utils/             # Configuration and logging utilities
├── projects/               # Example projects created by AgentsTeam
│   ├── ollama-web-chat/   # Full-stack chat application
│   └── yolo-detector/     # Computer vision object detection system
├── requirements.txt       # Core dependencies
├── setup.py              # Installation configuration
└── README.md              # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Git

### Install AgentsTeam CLI

1. **Clone the repository**:
   ```bash
   git clone https://github.com/dexmac221/AgentsTeam.git
   cd AgentsTeam
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install AgentsTeam CLI**:
   ```bash
   pip install -e .
   ```

4. **Verify installation**:
   ```bash
   agentsteam --help
   ```

### Configure API Keys

Set up your AI provider credentials:

```bash
# Configure OpenAI (for cloud models)
agentsteam config --openai-key your_openai_api_key

# Check current configuration
agentsteam config --show
```

## 🎮 CLI Usage Guide

AgentsTeam provides multiple ways to interact with AI for code generation:

### 1. Interactive Shell Mode (Recommended)

The interactive shell provides the most powerful and intuitive way to work with AgentsTeam:

```bash
agentsteam shell
```

**Shell Features:**
- **Conversational Coding**: Just describe what you want to build
- **Context Awareness**: Maintains conversation history and project context
- **File Operations**: Create, edit, and manage files with AI assistance
- **Built-in Commands**: Shell commands integrated with AI capabilities
- **Smart Model Selection**: Automatically chooses the best AI model for each task

**Shell Commands:**
- Type `help` to see all built-in commands
- Use `/help` to see all slash commands  
- Commands are documented in detail in the Complete Commands Reference section below

**Interactive Shell Examples:**

```bash
# Start the shell
agentsteam shell

# Natural language project creation
[AgentsTeam] 🤖 create a FastAPI web service for managing books

# File editing with context
[AgentsTeam] 🤖 edit main.py to add authentication middleware

# Project assistance  
[AgentsTeam] 🤖 add unit tests for the book service

# Mixed shell and AI commands
[AgentsTeam] 🤖 ls
[AgentsTeam] 🤖 show me the structure of this project
[AgentsTeam] 🤖 run python -m pytest
```

### 2. Direct Generation Mode

For quick project generation without interactive mode:

```bash
# Basic project generation
agentsteam generate "Simple REST API for blog posts"

# With specific technologies
agentsteam generate "Tetris game" --tech python,pygame

# Force specific model
agentsteam generate "Microservices platform" --model openai:gpt-4
```

**Generation Options:**
- `--tech`: Specify technologies (comma-separated)
- `--model`: Force specific model (`ollama:codellama`, `openai:gpt-4`)
- `--output`: Output directory (default: current directory)

### 3. Model Management

```bash
# List available models
agentsteam models

# Example output:
# 🤖 Available Models:
# 
# 🏠 Ollama (Local):
#   • codellama:7b
#   • llama2:13b
#   • mistral:7b
# 
# ☁️ OpenAI (Cloud):
#   • gpt-4o
#   • gpt-4o-mini  
#   • gpt-3.5-turbo
```

### 4. Configuration Management

```bash
# Show current configuration
agentsteam config --show

# Set OpenAI API key
agentsteam config --openai-key sk-your-api-key

# Configuration is stored in ~/.agentsteam/config.json
```

## 🚀 Autonomous Execution System

AgentsTeam features a powerful autonomous execution system that can work towards complex targets with minimal user intervention:

### Key Features
- **Target-Driven Development**: Set high-level goals and let AI create detailed execution plans
- **Real-Time Progress Tracking**: Visual progress indicators show completed, current, and pending steps
- **Intelligent Error Handling**: Automatic detection and fixing of compilation errors and build issues
- **User Control**: Pause, resume, or stop autonomous execution at any time
- **Multi-Step Workflows**: Handle complex projects requiring dozens of coordinated steps

### Autonomous Execution Examples

#### Complete Project Creation
```bash
agentsteam shell
/auto "Create a complete REST API for a blog system with authentication, database, and tests"
```

#### Game Development
```bash
/auto "Build a Tetris game for Commodore 64 using cc65 compiler"
# System will:
# 1. Create project structure
# 2. Generate C64-specific game code
# 3. Set up cc65 build system
# 4. Compile and test automatically
# 5. Fix any compilation errors with AI
```

#### Web Application Development  
```bash
/auto "Create a React chat application with real-time messaging and user authentication"
# System autonomously handles:
# - Frontend React components
# - Backend API development
# - WebSocket integration
# - Database setup
# - Authentication system
# - Testing and deployment
```

### Progress Tracking
```bash
/plan           # Show execution plan with progress
/progress       # Detailed progress with step results
/pause          # Pause execution for review
/resume         # Continue autonomous execution
```

### Example Progress Display
```
📋 Execution Plan:
🎯 Target: Create a C64 Tetris game
📊 Progress: 3/7 steps

✅ Step 1: Create project structure
   Result: Created src/, build/, assets/ directories
✅ Step 2: Generate game code
   Result: Created tetris.c with full game logic
✅ Step 3: Set up build system
   Result: Created Makefile for cc65 compilation
⏳ Step 4: Compile game (CURRENT)
⏸️ Step 5: Test in VICE emulator
⏸️ Step 6: Optimize performance
⏸️ Step 7: Create documentation
```

## 🛠️ Intelligent Error Correction

AgentsTeam automatically detects and fixes compilation errors across multiple programming languages and build systems:

### Supported Compilers & Tools
- **C/C++**: gcc, clang, cc65 (Commodore 64)
- **Rust**: rustc, cargo
- **Go**: go build, go test
- **Java**: javac, maven
- **TypeScript**: tsc
- **And many more...**

### Auto-Correction Workflow
1. **Error Detection**: Monitors compilation output for error patterns
2. **Source Analysis**: Reads and analyzes source code context
3. **AI-Powered Fixing**: Generates corrected code using advanced AI models
4. **Automatic Application**: Applies fixes with backup creation
5. **Retry Compilation**: Automatically retries compilation until success

### Example Error Correction
```bash
# Compile broken C code
\cc65 -t c64 -o build/game.s src/game.c

# Output:
# ❌ Compilation errors detected:
# src/game.c(42): Error: ';' expected
# src/game.c(67): Error: Undefined symbol: 'INVALID_COLOR'

# 🤖 AI automatically:
# 1. Analyzes source code and errors
# 2. Generates corrected version
# 3. Creates backup: game.c.backup
# 4. Applies fixes to game.c
# 5. Retries compilation
# ✅ Compilation successful!
```

### Direct Shell Commands with Error Handling
```bash
# Any command starting with \ gets automatic error correction
\make clean && make        # Auto-fixes build errors
\gcc -o app main.c        # Auto-fixes C compilation issues  
\cargo build --release    # Auto-fixes Rust compilation errors
\npm run build            # Auto-fixes TypeScript/JavaScript issues
```

## 🎯 Usage Examples

### Web Development

```bash
# Interactive shell approach
agentsteam shell
[AgentsTeam] 🤖 create a FastAPI web service with:
- User authentication (JWT)
- PostgreSQL database
- Docker containerization
- API documentation with Swagger
- Unit tests with pytest

# Direct generation approach
agentsteam generate "FastAPI web service with JWT auth and PostgreSQL" \
  --tech fastapi,postgresql,docker,jwt
```

### Computer Vision

```bash
agentsteam shell
[AgentsTeam] 🤖 build a real-time object detection system using:
- YOLO v8 for detection
- OpenCV for camera input
- WebSocket for live streaming
- Web interface for monitoring
```

### Data Analysis

```bash
agentsteam shell
[AgentsTeam] 🤖 create a data analysis pipeline for:
- CSV data processing with pandas
- Statistical analysis and visualization
- Machine learning model training
- Jupyter notebook with results
```

### CLI Tools

```bash
agentsteam generate "Command-line task manager" \
  --tech python,click,sqlite
```

## 🧠 Intelligent Model Selection

AgentsTeam automatically selects the best AI model based on task complexity:

### Simple Tasks → Local Models (Ollama)
- Basic CRUD applications
- Simple scripts and utilities
- Static websites
- Basic file operations

### Medium Tasks → Balanced Selection
- REST APIs with authentication
- Dashboards and admin interfaces
- Real-time features
- Database integrations

### Complex Tasks → Cloud Models (OpenAI)
- Microservices architectures
- Machine learning pipelines
- Complex algorithms
- Large-scale applications

**Manual Override:**
```bash
# Force Ollama for faster, local processing
/ollama

# Force OpenAI for highest quality
/openai

# Return to automatic selection
/auto
```

## 🎯 Example Projects

AgentsTeam demonstrates its capabilities through real project examples:

### 1. YOLO Object Detector
- **Real-time object detection** with YOLO v8
- **Multi-object tracking** with persistent IDs
- **Segmentation masks** visualization
- **Web interface** with live streaming
- **CLI agent integration** for automation
- **Professional async architecture**

```bash
cd projects/yolo-detector
python run.py --help
```

### 2. Ollama Web Chat
- **Full-stack chat application** with FastAPI backend
- **Real-time WebSocket communication**
- **Modern responsive frontend**
- **Database integration**
- **Multiple LLM model support**

```bash
cd projects/ollama-web-chat
python main.py
```

## 🏗️ Architecture

AgentsTeam uses a multi-agent architecture where different AI agents specialize in:

- **Project Architecture**: System design and structure planning
- **Code Generation**: Writing actual implementation code
- **Documentation**: Creating comprehensive documentation
- **Testing**: Generating test suites and validation
- **Integration**: Connecting components and services

## 📋 Complete Commands Reference

### Built-in Shell Commands

| Command | Description | Usage Example |
|---------|-------------|---------------|
| `help` | Show available commands | `help` |
| `models` | List available AI models | `models` |
| `config` | Show/set configuration | `config` |
| `clear` | Clear chat history | `clear` |
| `cd <dir>` | Change directory | `cd projects/` |
| `ls` | List files in current directory | `ls` |
| `cat <file>` | Show file content | `cat main.py` |
| `project <name>` | Set current project name | `project my-webapp` |
| `create <file>` | Create file with AI assistance | `create app.py` |
| `edit <file>` | Edit file with AI assistance | `edit main.py` |
| `run <command>` | Execute shell command | `run python test.py` |
| `exit` | Exit the shell | `exit` |

### Slash Commands (Quick Actions)

#### Model Management
| Command | Description | Usage Example |
|---------|-------------|---------------|
| `/help` | Show slash commands help | `/help` |
| `/model` | Show current model info | `/model` |
| `/models` | List all available models | `/models` |
| `/switch` | Switch AI provider | `/switch openai` |
| `/ollama` | Force use Ollama models | `/ollama` |
| `/openai` | Force use OpenAI models | `/openai` |
| `/auto` | Use automatic model selection | `/auto` |
| `/select` | Select specific model | `/select gpt-4` |
| `/status` | Show system status | `/status` |
| `/server` | Set Ollama server URL | `/server http://localhost:11434` |
| `/local` | Use local Ollama instance | `/local` |

#### File Operations
| Command | Description | Usage Example |
|---------|-------------|---------------|
| `/read <file>` | Read and analyze file | `/read main.py` |
| `/tree` | Show project file tree | `/tree` |
| `/find <pattern>` | Find text in files | `/find "function main"` |

#### Code Analysis & Assistance
| Command | Description | Usage Example |
|---------|-------------|---------------|
| `/analyze` | Analyze current code | `/analyze` |
| `/debug <file>` | Debug code issues | `/debug app.py` |
| `/fix <file>` | Fix code problems | `/fix main.py` |
| `/refactor <file>` | Refactor code | `/refactor utils.py` |
| `/explain <file>` | Explain code functionality | `/explain algorithm.py` |

#### Project Operations
| Command | Description | Usage Example |
|---------|-------------|---------------|
| `/project` | Analyze entire project | `/project` |
| `/context` | Show current context | `/context` |
| `/summary` | Generate project summary | `/summary` |
| `/check` | Check project health | `/check` |

#### Development Tools
| Command | Description | Usage Example |
|---------|-------------|---------------|
| `/test` | Run project tests | `/test` |
| `/install` | Install dependencies | `/install` |
| `/git` | Git operations | `/git status` |
| `/clear` | Clear chat history | `/clear` |

#### 🚀 Autonomous Execution
| Command | Description | Usage Example |
|---------|-------------|---------------|
| `/auto <target>` | Start autonomous execution towards target | `/auto "Create a C64 Tetris game"` |
| `/target [desc]` | Set/show current target | `/target "Build a web API"` |
| `/plan` | Show execution plan and progress | `/plan` |
| `/progress` | Show detailed progress information | `/progress` |
| `/pause` | Pause autonomous execution | `/pause` |
| `/resume` | Resume autonomous execution | `/resume` |
| `/stop` | Stop autonomous execution | `/stop` |

#### 🛠️ Smart Compilation & Error Correction
| Command | Description | Usage Example |
|---------|-------------|---------------|
| `/compile <cmd>` | Smart compilation with error analysis | `/compile gcc -o app main.c` |
| `/retry` | Retry last shell command | `/retry` |
| `\<command>` | Direct shell execution with auto error fixing | `\cc65 -t c64 game.c` |

### Natural Language Commands

Beyond specific commands, you can use natural language for any development task:

#### Project Creation
```bash
[AgentsTeam] 🤖 create a FastAPI web service for managing books
[AgentsTeam] 🤖 build a machine learning pipeline for image classification
[AgentsTeam] 🤖 make a CLI tool for file organization
```

#### Code Modification
```bash
[AgentsTeam] 🤖 add authentication to this web app
[AgentsTeam] 🤖 optimize the database queries in models.py
[AgentsTeam] 🤖 add error handling to the main function
```

#### Analysis and Debugging
```bash
[AgentsTeam] 🤖 what's wrong with this code?
[AgentsTeam] 🤖 explain how this algorithm works
[AgentsTeam] 🤖 suggest improvements for this project
```

#### Testing and Quality
```bash
[AgentsTeam] 🤖 write unit tests for the user service
[AgentsTeam] 🤖 add logging to this application
[AgentsTeam] 🤖 create documentation for the API
```

## 🤖 AI Provider Support

### Local Models (Ollama)
- **Fast response times** for simple tasks
- **Privacy-focused** - code never leaves your machine
- **No API costs** - unlimited usage
- **Offline capable** - works without internet

**Supported Models:**
- CodeLlama (7B, 13B, 34B)
- Llama 2 (7B, 13B, 70B)
- Mistral (7B)
- And more...

### Cloud Models (OpenAI)
- **Highest quality** code generation
- **Complex reasoning** capabilities
- **Latest AI technology**
- **Reliable uptime**

**Supported Models:**
- GPT-4o (latest, most capable)
- GPT-4o-mini (fast, cost-effective)
- GPT-3.5-turbo (balanced performance)

## 🔧 Configuration

### Environment Variables
```bash
export AGENTSTEAM_OPENAI_KEY="your-api-key"
export AGENTSTEAM_OLLAMA_URL="http://localhost:11434"
export AGENTSTEAM_LOG_LEVEL="INFO"
```

### Configuration File
Location: `~/.agentsteam/config.json`

```json
{
  "openai": {
    "api_key": "your-api-key"
  },
  "ollama": {
    "base_url": "http://localhost:11434"
  },
  "preferences": {
    "default_provider": "auto",
    "log_level": "INFO"
  }
}
```

## 🧪 Testing

Run the test suite:
```bash
# Unit tests
python -m pytest tests/

# Integration tests
python -m pytest tests/integration/

# Example project tests
cd projects/yolo-detector && python -m pytest
cd projects/ollama-web-chat && python -m pytest
```

## 📈 Performance

AgentsTeam is optimized for:
- **Fast Project Generation**: Complete projects in minutes
- **Resource Efficiency**: Minimal memory and CPU usage
- **Scalability**: Handles large, complex projects
- **Reliability**: Robust error handling and recovery

## 🚀 Advanced Usage

### Batch Processing
```bash
# Generate multiple projects from a file
cat project_ideas.txt | xargs -I {} agentsteam generate "{}"
```

### Integration with IDEs
```bash
# VS Code integration
code --install-extension agentsteam.vscode-extension

# Vim integration
echo "nnoremap <leader>ag :!agentsteam shell<CR>" >> ~/.vimrc
```

### CI/CD Integration
```bash
# Generate and test projects in CI
agentsteam generate "$PROJECT_DESCRIPTION" --output ./generated
cd generated && python -m pytest
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup
```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
python -m pytest

# Format code
black cli/ tests/

# Lint code
flake8 cli/ tests/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the README files in individual project directories
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join our community discussions for questions and ideas

## 🌟 Acknowledgments

- Built with modern Python frameworks (FastAPI, asyncio)
- Utilizes state-of-the-art AI models for code generation
- Inspired by the need for intelligent development automation
- Thanks to the open-source community for foundational libraries

---

**AgentsTeam** - Intelligent AI-powered development framework for the future of software creation.

## 📚 Quick Reference

### Essential Commands
```bash
# Start interactive shell (recommended)
agentsteam shell

# Quick project generation
agentsteam generate "your project description"

# List available models
agentsteam models

# Configure API keys
agentsteam config --openai-key your-key

# Show current configuration
agentsteam config --show
```

### Shell Quick Tips
- Type naturally: "create a web server"
- Use `/model` to see current AI model
- Use `/switch` to change providers
- Use `help` for all commands
- Files are created in current directory
- Use `project myapp` to set project context

### Getting Started in 30 Seconds
```bash
git clone https://github.com/dexmac221/AgentsTeam.git
cd AgentsTeam
pip install -e .
agentsteam config --openai-key your-key
agentsteam shell
# Type: "create a simple FastAPI hello world app"
```

**Happy coding with AI! 🚀**
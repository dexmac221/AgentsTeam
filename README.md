# AgentsTeam

AgentsTeam is an AI-powered development framework that enables intelligent code generation, project creation, and automated development workflows through CLI interaction. **Now optimized for local Ollama models with gpt-oss support for maximum performance and privacy.**

## 🚀 Features

- **🎯 gpt-oss Model Integration**: Optimized for the powerful gpt-oss:20b model - GPT-4 level performance locally
- **🏠 Local-First Approach**: Defaults to Ollama for privacy, speed, and unlimited usage
- **🧹 Clean Code Generation**: Enhanced prompting system generates pure, executable code without explanatory text
- **Intelligent Project Generation**: Create complete, production-ready projects with complex architectures
- **Interactive AI Shell**: Conversational coding with AI models for real-time development
- **Multi-Domain Expertise**: Supports web development, computer vision, data analysis, games, and more
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
│   ├── chats/ollama-web-chat/  # Full-stack chat application
│   ├── yolo-detector/          # Computer vision object detection system
│   ├── system-monitor/         # FastAPI system monitoring dashboard
│   └── snake-game/             # Python Snake game with pygame
├── requirements.txt       # Core dependencies
├── setup.py              # Installation configuration
└── README.md              # This file
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Git
- **Ollama** (recommended for best performance)

### Quick Start with gpt-oss Model

1. **Install Ollama**:
   ```bash
   # Linux/macOS
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Or visit: https://ollama.com/download
   ```

2. **Install gpt-oss model**:
   ```bash
   ollama pull gpt-oss:20b
   ```

3. **Clone AgentsTeam**:
   ```bash
   git clone https://github.com/dexmac221/AgentsTeam.git
   cd AgentsTeam
   ```

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Install AgentsTeam CLI**:
   ```bash
   pip install -e .
   ```

6. **Start creating projects**:
   ```bash
   # Navigate to projects directory (recommended)
   mkdir projects/my-project && cd projects/my-project
   
   # Start the shell
   agentsteam shell
   
   # Or generate directly
   agentsteam generate "FastAPI web service for task management"
   ```

### Configure AI Providers (Optional)

AgentsTeam defaults to Ollama with gpt-oss models, but you can configure additional providers:

```bash
# Configure OpenAI (for cloud models as fallback)
agentsteam config --openai-key your_openai_api_key

# Configure custom Ollama server (if not localhost)
agentsteam config --ollama-url http://192.168.1.62:11434

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

AgentsTeam now defaults to local Ollama models for optimal performance:

### **🎯 Primary: gpt-oss Models**
- **gpt-oss:20b**: GPT-4 level performance running locally
- **gpt-oss:latest**: Lighter version for faster responses
- **Privacy-focused**: Code never leaves your machine
- **Unlimited usage**: No API costs or rate limits
- **Fast responses**: Direct hardware acceleration

### **🏠 Local Models (Ollama) - Default**
- **CodeLlama**: Specialized coding models (7B, 13B, 34B)
- **Qwen2.5-Coder**: Advanced coding assistance
- **Llama 3.1**: General purpose models
- **Automatic fallback**: Smart selection based on availability

### **☁️ Cloud Models (OpenAI) - Fallback**
- **GPT-4o-mini**: Cost-effective, high-quality
- **GPT-4o**: Latest OpenAI technology
- **Reliable uptime**: When local models unavailable

**Priority Order:**
1. gpt-oss:20b (preferred for complex tasks)
2. Other local coding models (CodeLlama, Qwen2.5-Coder)
3. Cloud models (if local unavailable)

## 🆕 Recent Improvements (v2.0)

### **Enhanced Code Generation**
- ✅ **Clean Code Output**: Eliminates explanatory text mixed with code
- ✅ **Better Prompting**: Specialized prompts for pure code generation
- ✅ **Code Extraction**: Smart filtering to ensure executable files
- ✅ **Language Detection**: Automatic language-specific handling

### **gpt-oss Model Integration**
- ✅ **Default Priority**: gpt-oss:20b is now the preferred model
- ✅ **Local-First**: Defaults to Ollama for privacy and performance
- ✅ **Automatic Detection**: Finds and prioritizes gpt-oss models
- ✅ **Fallback Strategy**: Graceful degradation to other models

### **Improved Project Generation**
- ✅ **Production-Ready**: Generates complete, working applications
- ✅ **Clean Structure**: Proper file organization and imports
- ✅ **Error Handling**: Comprehensive exception handling in generated code
- ✅ **Documentation**: Integrated README and setup instructions

## 🎯 Example Projects

AgentsTeam demonstrates its capabilities through real project examples, all generated using the gpt-oss:20b model:

### 1. **System Monitor Dashboard** (`projects/system-monitor/`)
A comprehensive real-time system monitoring application featuring:
- **FastAPI backend** with async endpoints
- **GPU monitoring** via nvidia-smi integration  
- **CPU, memory, disk, network** monitoring with psutil
- **WebSocket real-time updates**
- **Bootstrap 5 responsive dashboard**
- **Production-ready code** with proper error handling

```bash
cd projects/system-monitor
pip install -r requirements.txt
python run.py
# Open http://localhost:8000
```

### 2. **Snake Game** (`projects/snake-game/`)
A complete Python Snake game showcasing game development:
- **Pygame implementation** with clean OOP design
- **Complete game mechanics** (collision, scoring, game over)
- **Keyboard controls** (arrow keys, WASD)
- **Pause/restart functionality**
- **Modular code structure** with separate config and utils

```bash
cd projects/snake-game  
pip install -r requirements.txt
python main.py
```

### 3. **YOLO Object Detector** (`projects/yolo-detector/`)
A sophisticated computer vision system featuring:
- **Real-time object detection** with YOLOv8 models
- **Multi-object tracking** with Kalman filtering
- **Instance segmentation** capabilities
- **Web interface** with live streaming
- **AI agent CLI** for automation
- **Professional async architecture**

```bash
cd projects/yolo-detector
python run.py --help
```

### 4. **Ollama Web Chat** (`projects/chats/ollama-web-chat/`)
A real-time chat application showcasing:
- **FastAPI backend** with WebSocket support
- **Multiple LLM model support** via Ollama
- **Context-aware conversations**
- **Modern responsive frontend**

```bash
cd projects/chats/ollama-web-chat
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

### Local Models (Ollama) - Default Provider
- **GPT-OSS:20B** - Our recommended model, provides GPT-4 level quality
- **Fast response times** for simple tasks
- **Privacy-focused** - code never leaves your machine
- **No API costs** - unlimited usage
- **Offline capable** - works without internet

**Supported Models:**
- **gpt-oss:20b** (Recommended - GPT-4 quality)
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

# IMPORTANT: Always work in a project subfolder to avoid contaminating the main codebase
mkdir -p projects/my-test-project
cd projects/my-test-project
agentsteam shell
# Type: "create a simple FastAPI hello world app"
```

### 🚨 Important: Project Isolation Best Practice

**Always run AgentsTeam from inside the `projects/` directory to avoid contaminating the main codebase:**

```bash
# ✅ CORRECT - Work in isolated project folder
cd AgentsTeam/projects/my-new-project
agentsteam shell
/auto "create a web application"

# ❌ WRONG - Don't run from AgentsTeam root
cd AgentsTeam
agentsteam shell  # This might create files in the main codebase!
```

**Why this matters:**
- Keeps your generated projects separate from AgentsTeam source code
- Prevents accidental modification of AgentsTeam's core files
- Makes it easy to manage multiple projects
- Allows safe experimentation without affecting the framework

## ⚖️ Important Disclaimer: AI-Generated Code

**🤖 Code Generation Notice**: AgentsTeam uses AI models (including gpt-oss, OpenAI GPT models, and other LLMs) to generate code. Please be aware of the following important considerations:

### 📋 Responsibility and Review
- **Always review generated code** before using it in production environments
- **Test thoroughly** - AI-generated code may contain bugs, security vulnerabilities, or inefficiencies
- **You are responsible** for the code you deploy - the AI is a tool, not a replacement for professional judgment
- **Validate licensing compatibility** of any generated code with your project requirements

### 🔒 Security Considerations
- **Security review required** - AI-generated code should undergo the same security review as human-written code
- **Sensitive data handling** - Be cautious when AI generates code that handles authentication, encryption, or personal data
- **Dependency security** - Review all suggested packages and dependencies for known vulnerabilities
- **Access controls** - Ensure generated code follows proper access control and authorization patterns

### 📜 Legal and Licensing
- **No warranty** - Code is generated "as-is" without warranties of any kind
- **Copyright considerations** - While AI-generated code is generally not copyrightable, ensure compliance with your organization's policies
- **Third-party code** - AI may suggest code patterns similar to existing codebases; ensure no copyright infringement
- **License compatibility** - Verify that generated code and suggested dependencies are compatible with your project's license

### 🎯 Best Practices for AI-Generated Code
- **Incremental adoption** - Start with small, non-critical components
- **Peer review** - Have colleagues review AI-generated code just like human-written code
- **Testing strategy** - Implement comprehensive testing for all AI-generated functionality
- **Documentation** - Document the AI's role in code generation for future maintainers
- **Fallback plans** - Have contingency plans if AI-generated components need to be replaced

### 🌐 Model-Specific Considerations
- **Local models (Ollama/gpt-oss)** - Code never leaves your infrastructure, providing privacy benefits
- **Cloud models (OpenAI)** - Code may be processed by third-party services; review their data policies
- **Model updates** - Different model versions may generate different code for the same prompts

**By using AgentsTeam, you acknowledge understanding these considerations and agree to use AI-generated code responsibly.**

---

**Happy coding with AI! 🚀**
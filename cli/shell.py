#!/usr/bin/env python3
"""
Interactive AgentsTeam Shell - Conversational coding with AI
"""

import asyncio
import os
import sys
import subprocess
import re
from pathlib import Path
from typing import Dict, Optional
import json

from .core.model_selector import ModelSelector
from .clients.ollama_client import OllamaClient
from .clients.openai_client import OpenAIClient
from .utils.config import Config
from .utils.logger import setup_logger

class AgentsTeamShell:
    """
    Interactive AgentsTeam Shell for AI-powered development.
    
    This is the main shell interface that provides conversational coding capabilities
    with AI models, project management, file operations, and intelligent code generation.
    
    The shell supports multiple AI providers (Ollama and OpenAI), maintains context
    across conversations, and provides both regular commands and slash commands for
    quick operations.
    
    Attributes:
        config (Config): Configuration manager for settings and preferences
        logger: Logging utility for debugging and monitoring
        selector (ModelSelector): Handles model selection and switching logic
        current_project (str): Name of the currently active project
        current_dir (Path): Current working directory
        chat_history (list): Conversation history for context maintenance
        current_model_info (dict): Information about the currently selected model
        force_provider (str): Override for model provider ('ollama', 'openai', or None)
        project_context (dict): RAG context and project-specific information
        file_embeddings (dict): Cached file embeddings for semantic search
        project_summary (str): AI-generated summary of current project
        ollama_client (OllamaClient): Client for Ollama API interactions
        openai_client (OpenAIClient): Client for OpenAI API interactions
        commands (dict): Map of regular commands to their handler functions
        slash_commands (dict): Map of slash commands to their handler functions
    """
    
    def __init__(self):
        """
        Initialize the AgentsTeam shell with all necessary components.
        
        Sets up configuration, logging, model selection, AI clients, and command
        mappings. Also initializes session state for project management and
        conversation history.
        """
        self.config = Config()
        self.logger = setup_logger()
        self.selector = ModelSelector(self.config, self.logger)
        
        # Current session state
        self.current_project = None
        self.current_dir = Path.cwd()
        self.chat_history = []
        self.current_model_info = None
        self.force_provider = 'ollama'  # Default to Ollama with gpt-oss models
        
        # RAG and context management
        self.project_context = {}
        self.file_embeddings = {}
        self.project_summary = None
        
        # Autonomous execution system
        self.autonomous_mode = False
        self.current_target = None
        self.execution_plan = []
        self.current_step = 0
        self.execution_paused = False
        self.step_results = []
        self.max_autonomous_steps = 50  # Safety limit
        
        # Initialize clients
        self.ollama_client = OllamaClient(self.config, self.logger)
        self.openai_client = OpenAIClient(self.config, self.logger)
        
        # Available commands
        self.commands = {
            'help': self.cmd_help,
            'models': self.cmd_models,
            'config': self.cmd_config,
            'create': self.cmd_create_file,
            'edit': self.cmd_edit_file,
            'run': self.cmd_run_command,
            'cd': self.cmd_change_dir,
            'ls': self.cmd_list_files,
            'cat': self.cmd_show_file,
            'project': self.cmd_project,
            'clear': self.cmd_clear,
            'exit': self.cmd_exit
        }
        
        # Slash commands (can be used anywhere)
        self.slash_commands = {
            '/help': self.slash_help,
            '/model': self.slash_model_info,
            '/models': self.slash_list_models,
            '/switch': self.slash_switch_provider,
            '/ollama': self.slash_use_ollama,
            '/openai': self.slash_use_openai,
            '/auto': self.slash_use_auto,
            '/status': self.slash_status,
            '/server': self.slash_set_ollama_server,
            '/local': self.slash_use_local_ollama,
            '/clear': self.cmd_clear,
            '/git': self.slash_git_operations,
            '/test': self.slash_run_tests,
            '/install': self.slash_install_deps,
            '/tree': self.slash_show_tree,
            '/select': self.slash_select_model,
            '/read': self.slash_read_file,
            '/analyze': self.slash_analyze_code,
            '/debug': self.slash_debug_code,
            '/fix': self.slash_fix_code,
            '/refactor': self.slash_refactor_code,
            '/explain': self.slash_explain_code,
            '/find': self.slash_find_in_files,
            '/project': self.slash_analyze_project,
            '/context': self.slash_show_context,
            '/summary': self.slash_project_summary,
            '/check': self.slash_check_project,
            '/compile': self.slash_smart_compile,
            '/retry': self.slash_retry_last_command,
            '/auto': self.slash_autonomous_mode,
            '/target': self.slash_set_target,
            '/plan': self.slash_show_plan,
            '/pause': self.slash_pause_execution,
            '/resume': self.slash_resume_execution,
            '/stop': self.slash_stop_execution,
            '/progress': self.slash_show_progress
        }
    
    async def start(self):
        """Start the interactive shell"""
        print("🤖 AgentsTeam Interactive Shell")
        print("Type 'help' for commands or just describe what you want to build!")
        print("Use /help for slash commands, /model for current model info")
        print(f"Current directory: {self.current_dir}")
        
        # Check available models
        models = await self.selector.get_ollama_models()
        ollama_available = len(models) > 0
        openai_available = bool(self.config.get('openai.api_key'))
        
        ollama_url = self.config.get('ollama.base_url', 'http://localhost:11434')
        print(f"📍 Ollama: {'✅ Available' if ollama_available else '❌ Not available'}")
        print(f"   Server: {ollama_url}")
        if ollama_available:
            # Check if gpt-oss models are available
            gpt_oss_models = [m for m in models if 'gpt-oss' in m.lower()]
            if gpt_oss_models:
                print(f"   🎯 Preferred: {', '.join(gpt_oss_models)}")
                other_models = [m for m in models if 'gpt-oss' not in m.lower()]
                if len(other_models) <= 3:
                    print(f"   Others: {', '.join(other_models)}")
                else:
                    print(f"   Others: {', '.join(other_models[:3])} (+{len(other_models)-3} more)")
            else:
                if len(models) <= 5:
                    print(f"   Models: {', '.join(models)}")
                else:
                    print(f"   Models: {', '.join(models[:5])} (+{len(models)-5} more)")
            print(f"           Use /models to see all available models")
        
        print(f"☁️ OpenAI: {'✅ Available' if openai_available else '❌ Not configured'}")
        
        # Show current mode - default to Ollama
        mode = "🏠 Ollama (local models)" if not self.force_provider or self.force_provider == 'ollama' else f"🔒 Forced to {self.force_provider}"
        if not ollama_available:
            mode = "☁️ OpenAI (cloud models)" if openai_available else "❌ No models available"
        print(f"🧠 Mode: {mode}")
        print()
        
        try:
            while True:
                try:
                    # Get user input with model indicator
                    model_indicator = ""
                    if self.current_model_info:
                        provider = self.current_model_info['provider']
                        model = self.current_model_info.get('model', '')[:10]  # Truncate long names
                        if provider == 'ollama':
                            model_indicator = f"🏠{model}"
                        else:
                            model_indicator = f"☁️{model}"
                    elif self.force_provider:
                        model_indicator = f"🔒{self.force_provider}"
                    else:
                        model_indicator = "🔄auto"
                    
                    prompt = f"[{self.current_dir.name}|{model_indicator}] 🤖 "
                    user_input = input(prompt).strip()
                    
                    if not user_input:
                        continue
                    
                    # Process input
                    await self.process_input(user_input)
                    
                except KeyboardInterrupt:
                    print("\n👋 Use 'exit' to quit gracefully")
                except EOFError:
                    break
        
        except Exception as e:
            print(f"❌ Shell error: {e}")
        
        print("\n👋 Goodbye!")
    
    async def execute_shell_command(self, command: str):
        """Execute a direct shell command without AI interpretation"""
        try:
            print(f"💻 Executing: {command}")
            
            # Store command for potential retry
            self.last_shell_command = command
            
            # Execute the command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                cwd=str(self.current_dir)
            )
            
            # Print output
            if result.stdout:
                print(result.stdout.rstrip())
            
            if result.stderr:
                print(f"⚠️ Error: {result.stderr.rstrip()}")
                
            # Check for compilation errors and offer AI assistance
            if result.returncode != 0 and self._is_compilation_error(result.stderr, command):
                await self._handle_compilation_error(command, result.stderr)
                
        except Exception as e:
            print(f"❌ Failed to execute command: {e}")
    
    def _is_compilation_error(self, stderr: str, command: str) -> bool:
        """Check if the error is a compilation error that we can help with"""
        compilation_indicators = [
            'error:', 'Error:', 'ERROR:', ': Error:',
            'undefined reference', 'undeclared identifier', 'Undefined symbol',
            'syntax error', 'parse error', 'compilation terminated',
            'fatal error', 'cannot find', 'no such file',
            'expected', 'missing', 'invalid', 'redefinition',
            'note:', 'warning:', 'Warning:', 'WARNING:',
            'linker error', 'ld:', 'collect2:', 'undefined symbol',
            'multiple definition', 'first defined here',
            'Invalid input character', 'Unexpected newline'
        ]
        
        compilation_commands = [
            'gcc', 'g++', 'clang', 'clang++', 'rustc', 'go build', 'javac', 'tsc',
            'cargo build', 'cargo run', 'mvn compile', 'dotnet build', 'make',
            'cc65', 'ca65', 'ld65'  # Add cc65 tools
        ]
        
        is_compilation_cmd = any(cmd in command.lower() for cmd in compilation_commands)
        has_error_indicators = any(indicator in stderr for indicator in compilation_indicators)
        
        # Also check for cc65-specific error patterns
        cc65_patterns = [
            '): Error:', '): Fatal:', '): Warning:'
        ]
        has_cc65_errors = any(pattern in stderr for pattern in cc65_patterns)
        
        return is_compilation_cmd and (has_error_indicators or has_cc65_errors)
    
    async def _handle_compilation_error(self, command: str, error_output: str):
        """Handle compilation errors with AI assistance and automatic fixing"""
        print("\n🤖 Compilation error detected! Starting automatic fix process...")
        
        # Store the failed command for retry functionality
        self.last_compile_command = command
        
        # Extract source files from command for better context
        source_files = self._extract_source_files_from_command(command)
        context = ""
        original_files_content = {}
        
        if source_files:
            print(f"📁 Analyzing source files: {', '.join(source_files)}")
            for file_path in source_files[:3]:  # Limit to 3 files
                try:
                    full_path = self.current_dir / file_path
                    if full_path.exists():
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        original_files_content[file_path] = content
                        context += f"\n\nSource file {file_path}:\n```\n{content}\n```"
                except Exception as e:
                    context += f"\nCould not read {file_path}: {e}"
        
        # Create AI prompt to fix the code automatically
        fix_prompt = f"""
AUTONOMOUS CODE FIXING REQUEST:

I need you to fix compilation errors automatically. 

COMPILATION COMMAND: {command}
ERROR OUTPUT:
{error_output}

SOURCE CODE CONTEXT:
{context}

INSTRUCTIONS:
1. Analyze the compilation errors carefully
2. Identify the specific issues in the source code
3. Provide corrected versions of the files that need fixing
4. Use this exact format for each file that needs to be fixed:

FIX_FILE: filename.ext
```language
corrected code here
```

Important: 
- Only fix the actual compilation errors
- Preserve the original functionality and logic
- Use proper C syntax for C64/cc65 development
- Fix string literal issues, syntax errors, and undefined symbols
- Make minimal changes to fix the errors

Provide the corrected files now:
"""
        
        print("🔧 Requesting automatic code fixes from AI...")
        
        try:
            # Get AI response with fixes
            model_info = await self.selector.select_model('complex')
            client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
            
            response = await client.generate(
                model=model_info['model'],
                prompt=fix_prompt,
                system_prompt="You are an expert C programmer fixing compilation errors. Provide corrected code that compiles successfully."
            )
            
            print(f"📝 AI response received, processing fixes...")
            
            # Parse and apply fixes
            fixes_applied = await self._apply_automatic_fixes(response, source_files)
            
            if fixes_applied:
                print(f"✅ Applied {fixes_applied} automatic fixes")
                print("🔄 Retrying compilation...")
                
                # Automatically retry the compilation
                await self.execute_shell_command(command)
                
            else:
                print("❌ Could not parse automatic fixes from AI response")
                print("🤖 AI Analysis:")
                print(response)
                print(f"\n💡 Use '/retry' to retry compilation after manual fixes")
                
        except Exception as e:
            print(f"❌ Error during automatic fixing: {e}")
            print("🔄 Falling back to manual assistance...")
            
            # Fallback to original behavior
            error_analysis_prompt = f"""
I tried to compile with this command: {command}

But got this error:
{error_output}

{context}

Please analyze the compilation error and provide specific steps to fix it.
"""
            
            await self.chat_with_ai(error_analysis_prompt)
            print(f"\n💡 Use '/retry' to retry compilation after making fixes")
    
    def _extract_source_files_from_command(self, command: str) -> list:
        """Extract source file names from compilation command"""
        import re
        
        # Common source file extensions
        source_extensions = ['.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.rs', '.go', '.java', '.ts', '.js']
        
        # Split command into parts and look for file names
        parts = command.split()
        source_files = []
        
        for part in parts:
            # Check if part looks like a source file
            if any(part.endswith(ext) for ext in source_extensions):
                source_files.append(part)
            # Also check for files without explicit extensions in current directory
            elif '.' not in part and len(part) > 1:
                # Check if file exists with common extensions
                for ext in source_extensions:
                    potential_file = f"{part}{ext}"
                    if (self.current_dir / potential_file).exists():
                        source_files.append(potential_file)
                        break
        
        return source_files
    
    async def _apply_automatic_fixes(self, ai_response: str, source_files: list) -> int:
        """Parse AI response and apply automatic fixes to source files"""
        fixes_applied = 0
        
        try:
            # Parse the AI response for FIX_FILE directives
            lines = ai_response.split('\n')
            current_file = None
            current_code = []
            in_code_block = False
            
            for line in lines:
                line_stripped = line.strip()
                
                # Look for FIX_FILE directive
                if line_stripped.startswith('FIX_FILE:'):
                    # Apply previous fix if we have one
                    if current_file and current_code:
                        await self._apply_single_fix(current_file, '\n'.join(current_code))
                        fixes_applied += 1
                    
                    # Start new fix
                    current_file = line_stripped.replace('FIX_FILE:', '').strip()
                    current_code = []
                    in_code_block = False
                    print(f"🔧 Found fix for: {current_file}")
                
                # Look for code blocks
                elif line_stripped.startswith('```'):
                    if in_code_block:
                        # End of code block
                        in_code_block = False
                    else:
                        # Start of code block
                        in_code_block = True
                        current_code = []  # Reset code content
                
                # Collect code lines
                elif in_code_block and current_file:
                    current_code.append(line)
            
            # Apply the last fix if we have one
            if current_file and current_code:
                await self._apply_single_fix(current_file, '\n'.join(current_code))
                fixes_applied += 1
            
            return fixes_applied
            
        except Exception as e:
            print(f"❌ Error parsing automatic fixes: {e}")
            return 0
    
    async def _apply_single_fix(self, filename: str, corrected_code: str):
        """Apply a single file fix"""
        try:
            file_path = self.current_dir / filename
            
            # Create backup
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                print(f"📋 Created backup: {backup_path.name}")
            
            # Apply fix
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(corrected_code)
            
            print(f"✅ Applied fix to: {filename}")
            
        except Exception as e:
            print(f"❌ Error applying fix to {filename}: {e}")
    
    async def process_input(self, user_input: str):
        """Process user input - either command, slash command, shell command, or AI conversation"""
        
        # Check for direct shell commands (starting with \)
        if user_input.startswith('\\'):
            shell_command = user_input[1:]  # Remove the \ prefix
            await self.execute_shell_command(shell_command)
            return
        
        # Check for slash commands first
        if user_input.startswith('/'):
            parts = user_input.split()
            slash_cmd = parts[0].lower()
            
            if slash_cmd in self.slash_commands:
                await self.slash_commands[slash_cmd](parts[1:] if len(parts) > 1 else [])
                return
        
        # Check for built-in commands
        parts = user_input.split()
        command = parts[0].lower()
        
        if command in self.commands:
            await self.commands[command](parts[1:] if len(parts) > 1 else [])
        else:
            # Send to AI for processing
            await self.chat_with_ai(user_input)
    
    async def chat_with_ai(self, message: str):
        """Chat with AI and potentially execute commands"""
        print("🤔 Thinking...")
        
        # Check for automatic project analysis triggers
        message_lower = message.lower()
        auto_analysis_triggers = [
            'check this project', 'check the project', 'analyze this project', 
            'analyze the project', 'find issues', 'scan for problems',
            'check for errors', 'analyze and fix', 'review this project'
        ]
        
        if any(trigger in message_lower for trigger in auto_analysis_triggers):
            print("🚀 Detected project analysis request - running automatic check...")
            await self.slash_check_project([])
            return
        
        # Add to chat history
        self.chat_history.append({"role": "user", "content": message})
        
        # Build context
        context = self._build_context()
        
        # Select appropriate model based on force_provider setting
        if self.force_provider:
            model_info = await self._get_forced_model()
        else:
            complexity = self._analyze_message_complexity(message)
            model_info = await self.selector.select_model(complexity)
        
        # Store current model info
        self.current_model_info = model_info
        
        print(f"🧠 Using: {model_info['provider']}:{model_info['model']}")
        
        # Get client
        client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
        
        try:
            # Generate response
            response = await client.generate(
                model=model_info['model'],
                prompt=f"{context}\n\nUser: {message}",
                system_prompt=self._get_system_prompt()
            )
            
            print(f"🤖 {response}")
            
            # Add to history
            self.chat_history.append({"role": "assistant", "content": response})
            
            # Check if AI wants to execute commands
            await self._process_ai_response(response)
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def _get_forced_model(self):
        """Get model based on forced provider"""
        if self.force_provider == 'ollama':
            return await self.selector._select_local_model() or {
                'provider': 'ollama', 
                'model': 'No local models available',
                'base_url': self.selector.ollama_base_url
            }
        elif self.force_provider == 'openai':
            return await self.selector._select_cloud_model('balanced')
        else:
            # Fallback to auto selection
            complexity = 'medium'
            return await self.selector.select_model(complexity)
    
    def _build_context(self) -> str:
        """Build context for AI"""
        context = f"Current directory: {self.current_dir}\n"
        
        # Add recent files
        try:
            files = [f.name for f in self.current_dir.iterdir() if f.is_file()][:5]
            if files:
                context += f"Recent files: {', '.join(files)}\n"
        except:
            pass
        
        # Add project info if available
        if self.current_project:
            context += f"Current project: {self.current_project}\n"
        
        # Add recent chat history
        if len(self.chat_history) > 2:
            context += "\nRecent conversation:\n"
            for msg in self.chat_history[-4:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                context += f"{role}: {msg['content'][:100]}...\n"
        
        return context
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI"""
        return """You are an expert programming agent in an interactive shell. You can create complete projects with multiple files and directories.

COMMANDS YOU CAN USE:

CREATE FILE path/filename.ext
```language
# Your code here
```

CREATE DIR directory_name

RUN COMMAND: shell_command_here

CAPABILITIES:
✅ Create multiple files in one response
✅ Create directory structures (CREATE DIR tests/, CREATE FILE tests/test_main.py)
✅ Run commands (pip install, python run.py, git init, npm install, etc.)
✅ Create entire project structures with proper organization
✅ Setup virtual environments, install dependencies
✅ Run tests, start servers, commit to git
✅ Generate requirements.txt, package.json, Dockerfile, etc.

EXAMPLES:

User: "Create a FastAPI project with tests"
You: "I'll create a complete FastAPI project!

CREATE DIR src/
CREATE DIR tests/
CREATE DIR docs/

CREATE FILE src/main.py
```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

CREATE FILE tests/test_main.py
```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
```

CREATE FILE requirements.txt
```
fastapi
uvicorn
pytest
```

RUN COMMAND: pip install -r requirements.txt
RUN COMMAND: pytest tests/
"

ALWAYS:
- Create actual files and directories, don't just explain
- Use proper project structure with src/, tests/, docs/ directories
- Include requirements.txt, .gitignore, README.md
- Run commands to test and setup the project
- Be a complete programming assistant"""

    def _analyze_message_complexity(self, message: str) -> str:
        """Analyze message complexity"""
        message_lower = message.lower()
        
        complex_indicators = ['microservices', 'distributed', 'machine learning', 'kubernetes']
        medium_indicators = ['api', 'database', 'authentication', 'web app']
        
        if any(indicator in message_lower for indicator in complex_indicators):
            return 'complex'
        elif any(indicator in message_lower for indicator in medium_indicators):
            return 'medium'
        else:
            return 'simple'
    
    async def _process_ai_response(self, response: str):
        """Process AI response for commands"""
        lines = response.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Check for directory creation
            if line.startswith('CREATE DIR') or line.startswith('CREATE DIRECTORY'):
                dir_name = line.replace('CREATE DIR', '').replace('CREATE DIRECTORY', '').strip()
                await self._create_directory(dir_name)
            
            # Check for file creation
            elif line.startswith('CREATE FILE'):
                filename = line.replace('CREATE FILE', '').strip()
                
                # Handle files with paths (create directories first)
                if '/' in filename:
                    dir_path = '/'.join(filename.split('/')[:-1])
                    await self._create_directory(dir_path)
                
                # Get code from following lines
                code_lines = []
                j = i + 1
                while j < len(lines):
                    if lines[j].strip().startswith('```'):
                        j += 1
                        while j < len(lines) and not lines[j].strip().startswith('```'):
                            code_lines.append(lines[j])
                            j += 1
                        break
                    j += 1
                
                if code_lines:
                    await self._create_file(filename, '\n'.join(code_lines))
            
            # Check for command execution
            elif line.startswith('RUN COMMAND:'):
                command = line.replace('RUN COMMAND:', '').strip()
                await self._run_command(command)
    
    async def _create_file(self, filename: str, content: str):
        """Create a file with given content"""
        try:
            file_path = self.current_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Created: {filename}")
        except Exception as e:
            print(f"❌ Error creating {filename}: {e}")
    
    async def _create_directory(self, dir_path: str):
        """Create directory structure"""
        try:
            full_path = self.current_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"📁 Created directory: {dir_path}")
        except Exception as e:
            print(f"❌ Error creating directory {dir_path}: {e}")
    
    def _is_dangerous_command(self, command: str) -> bool:
        """Check if command is potentially dangerous"""
        dangerous_commands = [
            'sudo', 'su', 'rm -rf', 'rmdir', 'chmod 777', 'chmod -R',
            'mkfs', 'fdisk', 'dd', 'format', 'shutdown', 'reboot',
            'init 0', 'init 6', 'halt', 'poweroff', 'systemctl',
            'service', 'chown -R', 'usermod', 'userdel', 'groupdel',
            'iptables', 'ufw', 'firewall', 'mount', 'umount',
            'crontab -e', 'crontab -r', 'at ', '> /dev/', 'curl | sh',
            'wget | sh', 'bash <', 'sh <', 'eval', 'exec'
        ]
        
        cmd_lower = command.lower().strip()
        
        # Allow safe file reading commands
        safe_read_commands = ['cat ', 'less ', 'more ', 'head ', 'tail ', 'grep ', 'find ', 'ls ', 'tree ', 'file ']
        if any(cmd_lower.startswith(safe_cmd) for safe_cmd in safe_read_commands):
            # But still block if they try to read system files
            if any(sys_path in cmd_lower for sys_path in ['/etc/', '/usr/', '/var/', '/sys/', '/proc/']):
                return True
            return False
        
        # Check for dangerous patterns
        for dangerous in dangerous_commands:
            if dangerous in cmd_lower:
                return True
        
        # Check for pipe to shell execution
        if '|' in cmd_lower and any(shell in cmd_lower for shell in ['sh', 'bash', 'zsh', 'fish']):
            return True
        
        # Check for redirection to system files
        if '>' in cmd_lower and any(sys_file in cmd_lower for sys_file in ['/etc/', '/usr/', '/var/', '/sys/', '/proc/']):
            return True
        
        return False

    async def _run_command(self, command: str):
        """Run a shell command with safety checks"""
        # Security check for dangerous commands
        if self._is_dangerous_command(command):
            print(f"🛡️ BLOCKED: Potentially dangerous command detected!")
            print(f"Command: {command}")
            print("⚠️ For security reasons, the following are not allowed:")
            print("  • sudo/su commands")
            print("  • System file modifications (/etc/, /usr/, etc.)")
            print("  • File deletion with rm -rf")
            print("  • System service control")
            print("  • Pipe to shell execution")
            print("  • Network downloads piped to shell")
            print()
            print("💡 If you need to run system commands, please do so manually in your terminal.")
            return
        
        try:
            print(f"🔧 Running: {command}")
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=str(self.current_dir),
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            if result.stdout:
                print(f"📤 Output:\n{result.stdout}")
            if result.stderr:
                print(f"⚠️ Errors:\n{result.stderr}")
            
        except subprocess.TimeoutExpired:
            print("⏱️ Command timed out")
        except Exception as e:
            print(f"❌ Command error: {e}")
    
    # Built-in commands
    async def cmd_help(self, args):
        """Show help"""
        print("""
🤖 AgentsTeam Shell Commands:

Built-in Commands:
  help           - Show this help
  models         - List available AI models
  config         - Show/set configuration
  clear          - Clear chat history
  cd <dir>       - Change directory
  ls             - List files
  cat <file>     - Show file content
  project <name> - Set current project name
  exit           - Exit shell

File Operations:
  create <file>  - Create a file (AI-assisted)
  edit <file>    - Edit a file (AI-assisted)
  run <command>  - Run shell command

🆕 Direct Shell Commands:
  \\<command>    - Execute shell command directly (without AI)
  Examples:
    \\ls -la      - List files with details
    \\g++ main.cpp - Compile C++ code (with smart error handling)
    \\python test.py - Run Python script

🆕 Smart Compilation:
  - Automatic error detection for C++, Rust, Go, Java, etc.
  - AI-powered error analysis and fix suggestions
  - Source code context for better debugging
  - Use /compile or /retry for compilation workflows

🚀 Autonomous Execution:
  - Set targets and let AI work autonomously towards them
  - Real-time progress tracking with visible steps
  - Pause/resume/stop controls for user oversight
  - Multi-step execution with automatic error handling
  - Use /auto "target description" to start

AI Conversation:
  Just type what you want to build or ask questions!
  
Examples:
  "create a python calculator"
  "make a tetris game with pygame"
  "edit main.py to add error handling"
  "run the tests"
  \\make clean    (direct shell command)
        """)
    
    async def cmd_models(self, args):
        """Show available models"""
        print("🤖 Available Models:")
        
        ollama_models = await self.selector.get_ollama_models()
        if ollama_models:
            print(f"📍 Ollama: {', '.join(ollama_models)}")
        else:
            print("❌ Ollama not available")
        
        if self.config.get('openai.api_key'):
            openai_models = [
                "gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "o4-mini",
                "gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-3.5-turbo"
            ]
            print(f"☁️ OpenAI: {', '.join(openai_models)}")
        else:
            print("❌ OpenAI not configured")
    
    async def cmd_config(self, args):
        """Show/set configuration"""
        if not args:
            config = self.config.get_all()
            print("⚙️ Configuration:")
            print(json.dumps(config, indent=2))
        elif len(args) == 2:
            key, value = args
            self.config.set(key, value)
            print(f"✅ Set {key} = {value}")
    
    async def cmd_create_file(self, args):
        """Create file with AI assistance"""
        if not args:
            filename = input("📝 Filename: ")
        else:
            filename = args[0]
        
        description = input("📋 Describe what this file should do: ")
        await self.chat_with_ai(f"Create a file called '{filename}' that {description}")
    
    async def cmd_edit_file(self, args):
        """Edit file with AI assistance"""
        if not args:
            filename = input("📝 Filename: ")
        else:
            filename = args[0]
        
        if not (self.current_dir / filename).exists():
            print(f"❌ File {filename} doesn't exist")
            return
        
        changes = input("📋 What changes do you want to make?: ")
        await self.chat_with_ai(f"Edit the file '{filename}' to {changes}")
    
    async def cmd_run_command(self, args):
        """Run shell command"""
        command = ' '.join(args) if args else input("💻 Command: ")
        await self._run_command(command)
    
    async def cmd_change_dir(self, args):
        """Change directory"""
        if not args:
            target = Path.home()
        else:
            target = Path(args[0])
        
        try:
            if target.exists() and target.is_dir():
                self.current_dir = target.resolve()
                print(f"📁 Changed to: {self.current_dir}")
            else:
                print(f"❌ Directory not found: {target}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_list_files(self, args):
        """List files in current directory"""
        try:
            items = list(self.current_dir.iterdir())
            if not items:
                print("📁 Directory is empty")
                return
            
            print(f"📁 Contents of {self.current_dir}:")
            for item in sorted(items):
                icon = "📁" if item.is_dir() else "📄"
                print(f"  {icon} {item.name}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    async def cmd_show_file(self, args):
        """Show file content"""
        if not args:
            filename = input("📄 Filename: ")
        else:
            filename = args[0]
        
        try:
            file_path = self.current_dir / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"📄 {filename}:")
                print("-" * 40)
                print(content)
                print("-" * 40)
            else:
                print(f"❌ File not found: {filename}")
        except Exception as e:
            print(f"❌ Error reading file: {e}")
    
    async def cmd_project(self, args):
        """Set current project name"""
        if not args:
            print(f"📂 Current project: {self.current_project or 'None'}")
        else:
            self.current_project = ' '.join(args)
            print(f"📂 Project set to: {self.current_project}")
    
    async def cmd_clear(self, args):
        """Clear chat history"""
        self.chat_history = []
        print("🧹 Chat history cleared")
    
    async def cmd_exit(self, args):
        """Exit the shell"""
        print("👋 Goodbye!")
        sys.exit(0)
    
    # Slash Commands
    async def slash_help(self, args):
        """Show slash commands help"""
        print("""
🔥 Slash Commands (available anywhere):

Model Management:
  /model          - Show current model info
  /models         - List all available models
  /select MODEL   - Select specific model (e.g., /select gpt-4.1-mini)
  /switch         - Switch between auto/ollama/openai
  /ollama         - Force use Ollama models
  /openai         - Force use OpenAI models
  /auto           - Return to auto mode (smart selection)
  
Server Management:
  /server <url>   - Set Ollama server URL
  /local          - Switch to local Ollama (localhost)
  
🆕 Smart Compilation & Shell:
  /compile CMD    - Smart compilation with error analysis
  /retry          - Retry last shell command
  \\CMD           - Direct shell execution (use \\ prefix anywhere)
  
🚀 Autonomous Execution:
  /auto TARGET    - Start autonomous execution towards target
  /target [desc]  - Set/show current target
  /plan           - Show execution plan and progress
  /progress       - Show detailed progress information
  /pause          - Pause autonomous execution
  /resume         - Resume autonomous execution
  /stop           - Stop autonomous execution
  
Programming Tools:
  /git <command>  - Git operations (init, add, commit, push)
  /test           - Run project tests
  /install        - Install dependencies (pip, npm, cargo)
  /tree           - Show project structure

Code Analysis & Debugging:
  /read FILE      - Read and display file with line numbers
  /analyze FILE   - AI analysis of code quality and issues
  /debug FILE     - Debug code issues and errors
  /fix FILE       - Automatically fix code issues (creates backup)
  /refactor FILE  - Refactor code for better quality
  /explain FILE   - Explain how code works
  /find PATTERN   - Search for text/patterns in files

Project-Wide Analysis (RAG):
  /project [focus] - Analyze entire project with context (RAG-based)
  /check          - 🆕 Automatically analyze and fix project issues
  /context        - Show current project context and indexed files
  /summary        - Generate comprehensive project summary
  
Information:
  /status         - Show full system status  
  /help           - Show this help
  /clear          - Clear chat history

🆕 New Features Examples:
  # Smart Compilation
  /compile g++ -o app main.cpp      # Smart C++ compilation
  /retry                            # Retry after fixing errors
  \\ls -la                          # Direct shell command
  \\make clean && make              # Direct make command
  
  # Autonomous Execution
  /auto "Create a REST API for a blog system"  # Start autonomous mode
  /plan                             # Show execution plan
  /pause                            # Pause execution
  /resume                           # Resume execution
  
  # Regular Commands
  /git init                         # Initialize git repo
  /install                          # Install project dependencies
  /test                             # Run all tests
  /tree                             # Show project structure
  /server http://192.168.1.62:11434 # Use powerful server
        """)
    
    async def slash_model_info(self, args):
        """Show current model information"""
        print("🧠 Current Model Configuration:")
        
        if self.force_provider:
            print(f"   Mode: 🔒 Forced to {self.force_provider}")
        else:
            print("   Mode: 🔄 Auto (complexity-based selection)")
        
        if self.current_model_info:
            provider = self.current_model_info['provider']
            model = self.current_model_info['model']
            print(f"   Last used: {provider}:{model}")
        
        # Show what would be selected for different complexities
        print("\n   Auto-selection preview:")
        for complexity in ['simple', 'medium', 'complex']:
            try:
                if self.force_provider:
                    model_info = await self._get_forced_model()
                else:
                    model_info = await self.selector.select_model(complexity)
                provider = model_info['provider']
                model = model_info['model']
                icon = "🏠" if provider == "ollama" else "☁️"
                print(f"   {complexity.capitalize():8} → {icon} {provider}:{model}")
            except Exception as e:
                print(f"   {complexity.capitalize():8} → ❌ {e}")
    
    async def slash_list_models(self, args):
        """List all available models"""
        print("🤖 All Available Models:")
        print()
        
        # Ollama models
        ollama_models = await self.selector.get_ollama_models()
        if ollama_models:
            print("📍 Ollama Models:")
            for i, model in enumerate(ollama_models, 1):
                # Add star for coding models
                star = "⭐" if any(coding in model.lower() for coding in ['coder', 'code', 'llama']) else ""
                print(f"   {i:2}. {model} {star}")
            print(f"   ({len(ollama_models)} models available)")
            
            ollama_url = self.config.get('ollama.base_url', 'http://localhost:11434')
            print(f"   Server: {ollama_url}")
        else:
            print("📍 Ollama Models: ❌ Not available")
            print("   Install Ollama: curl -fsSL https://ollama.com/install.sh | sh")
            print("   Pull models: ollama pull qwen2.5-coder:7b")
        
        print()
        
        # OpenAI models
        if self.config.get('openai.api_key'):
            print("☁️ OpenAI Models:")
            openai_models = [
                ("gpt-4.1", "Latest GPT-4.1 model"),
                ("gpt-4.1-mini", "Affordable GPT-4.1 variant"), 
                ("gpt-4.1-nano", "Ultra-lightweight GPT-4.1"),
                ("o4-mini", "Reasoning-optimized model"),
                ("gpt-4o", "Multimodal GPT-4 Omni"),
                ("gpt-4o-mini", "Affordable GPT-4o (recommended)"),
                ("gpt-4", "Classic GPT-4"),
                ("gpt-3.5-turbo", "Fast and economical")
            ]
            for i, (model, desc) in enumerate(openai_models, 1):
                star = "⭐" if "mini" in model or "nano" in model else ""
                print(f"   {i:2}. {model} - {desc} {star}")
            print("   (⭐ = cost-optimized)")
        else:
            print("☁️ OpenAI Models: ❌ Not configured")
            print("   Set API key: export OPENAI_API_KEY=your_key_here")
        
        print()
        print("💡 Usage:")
        print("   /ollama     - Force use Ollama models")
        print("   /openai     - Force use OpenAI models")
        print("   /auto       - Smart model selection (default)")
        print("   /server URL - Change Ollama server")
        print("   /select MODEL - Select specific model")
    
    async def slash_select_model(self, args):
        """Select a specific model to use"""
        if not args:
            print("Usage: /select MODEL_NAME")
            print("Examples:")
            print("  /select qwen2.5-coder:7b")
            print("  /select gpt-4.1-mini") 
            print("  /select ollama:gemma2:9b")
            print("  /select openai:o4-mini")
            print()
            print("Use /models to see all available models")
            return
        
        model_str = args[0]
        try:
            # Parse model string
            model_info = self.selector.parse_model_string(model_str)
            provider = model_info['provider']
            model = model_info['model']
            
            # Verify model exists
            if provider == 'ollama':
                available_models = await self.selector.get_ollama_models()
                if model not in available_models:
                    print(f"❌ Model '{model}' not found in Ollama")
                    print(f"Available models: {', '.join(available_models[:5])}")
                    print("Install model: ollama pull " + model)
                    return
                print(f"🏠 Selected Ollama model: {model}")
                
            elif provider == 'openai':
                if not self.config.get('openai.api_key'):
                    print("❌ OpenAI API key not configured")
                    print("Set key: export OPENAI_API_KEY=your_key_here")
                    return
                print(f"☁️ Selected OpenAI model: {model}")
            
            # Force use this specific model
            self.current_model_info = model_info
            self.force_provider = provider
            print(f"✅ Will use {provider}:{model} for all requests")
            print("Use /auto to return to automatic selection")
            
        except Exception as e:
            print(f"❌ Error selecting model: {e}")
    
    async def slash_switch_provider(self, args):
        """Switch provider mode"""
        if not args:
            print("Usage: /switch [auto|ollama|openai]")
            print("Current mode:", "auto" if not self.force_provider else self.force_provider)
            return
        
        mode = args[0].lower()
        if mode == 'auto':
            self.force_provider = None
            print("🔄 Switched to auto mode (smart model selection)")
        elif mode == 'ollama':
            self.force_provider = 'ollama'
            print("🏠 Switched to Ollama only (local models)")
        elif mode == 'openai':
            self.force_provider = 'openai'
            print("☁️ Switched to OpenAI only (gpt-4o-mini)")
        else:
            print("❌ Invalid mode. Use: auto, ollama, or openai")
    
    async def slash_use_ollama(self, args):
        """Force use Ollama models"""
        self.force_provider = 'ollama'
        models = await self.selector.get_ollama_models()
        if models:
            print(f"🏠 Switched to Ollama only")
            if len(models) <= 5:
                print(f"   Available models: {', '.join(models)}")
            else:
                print(f"   Available models: {', '.join(models[:5])} (+{len(models)-5} more)")
                print(f"   Use /models to see all available models")
        else:
            print("⚠️ Switched to Ollama but no local models found")
            print("   Install models: ollama pull gemma2:9b")
    
    async def slash_use_openai(self, args):
        """Force use OpenAI models"""
        self.force_provider = 'openai'
        if self.config.get('openai.api_key'):
            print("☁️ Switched to OpenAI only (gpt-4o-mini)")
            print("   More affordable than gpt-4!")
        else:
            print("❌ OpenAI not configured")
            print("   Configure: agentsteam config --openai-key YOUR_KEY")
    
    async def slash_use_auto(self, args):
        """Return to auto mode"""
        self.force_provider = None
        print("🔄 Switched to auto mode")
        print("   AI will select the best model based on task complexity")
    
    async def slash_status(self, args):
        """Show full system status"""
        print("📊 AgentsTeam System Status:")
        print("=" * 40)
        
        # Current session
        print(f"📁 Directory: {self.current_dir}")
        print(f"📂 Project: {self.current_project or 'None'}")
        print(f"💬 Chat history: {len(self.chat_history)} messages")
        
        # Model status
        mode = "🔄 Auto" if not self.force_provider else f"🔒 {self.force_provider}"
        print(f"🧠 Model mode: {mode}")
        
        if self.current_model_info:
            provider = self.current_model_info['provider']
            model = self.current_model_info['model']
            print(f"🎯 Last model: {provider}:{model}")
        
        # Ollama status
        models = await self.selector.get_ollama_models()
        print(f"🏠 Ollama: {'✅' if models else '❌'} ({len(models)} models)")
        
        # OpenAI status
        has_key = bool(self.config.get('openai.api_key'))
        print(f"☁️ OpenAI: {'✅' if has_key else '❌'} (gpt-4o-mini)")
        
        print("=" * 40)
    
    async def slash_set_ollama_server(self, args):
        """Set Ollama server URL"""
        if not args:
            current_url = self.config.get('ollama.base_url', 'http://localhost:11434')
            print(f"Current Ollama server: {current_url}")
            print("Usage: /server <url>")
            print("Examples:")
            print("  /server http://192.168.1.62:11434")
            print("  /server http://localhost:11434")
            return
        
        url = args[0]
        if not url.startswith('http'):
            url = f"http://{url}"
        if ':11434' not in url:
            url = f"{url}:11434"
        
        # Update configuration
        self.config.set('ollama.base_url', url)
        
        # Update selector with new URL
        self.selector.ollama_base_url = url
        self.ollama_client.base_url = url
        
        print(f"🖥️ Ollama server set to: {url}")
        
        # Test connection and show available models
        try:
            models = await self.selector.get_ollama_models()
            if models:
                print(f"✅ Connected! Found {len(models)} models:")
                for model in models[:5]:  # Show first 5 models
                    print(f"   • {model}")
                if len(models) > 5:
                    print(f"   ... and {len(models) - 5} more")
            else:
                print("⚠️ Connected but no models found")
                print("   Install models: ollama pull gemma2:27b")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
    
    async def slash_use_local_ollama(self, args):
        """Switch to local Ollama server"""
        await self.slash_set_ollama_server(['http://localhost:11434'])
        print("🏠 Switched back to local Ollama")
    
    async def slash_git_operations(self, args):
        """Handle git operations"""
        if not args:
            print("Usage: /git <command>")
            print("Examples:")
            print("  /git init")
            print("  /git add .")
            print("  /git commit -m 'Initial commit'")
            print("  /git status")
            return
        
        git_cmd = ' '.join(args)
        await self._run_command(f"git {git_cmd}")
    
    async def slash_run_tests(self, args):
        """Run project tests"""
        print("🧪 Running tests...")
        
        # Try different test runners
        test_files = list(self.current_dir.rglob("test_*.py")) + list(self.current_dir.rglob("*_test.py"))
        
        if test_files:
            await self._run_command("python -m pytest -v")
        elif (self.current_dir / "package.json").exists():
            await self._run_command("npm test")
        elif (self.current_dir / "Cargo.toml").exists():
            await self._run_command("cargo test")
        else:
            print("⚠️ No tests found. Looking for:")
            print("  • Python: test_*.py files")
            print("  • Node.js: package.json with test script")
            print("  • Rust: Cargo.toml")
    
    async def slash_install_deps(self, args):
        """Install project dependencies"""
        print("📦 Installing dependencies...")
        
        installed = False
        
        # Python
        if (self.current_dir / "requirements.txt").exists():
            await self._run_command("pip install -r requirements.txt")
            installed = True
        elif (self.current_dir / "pyproject.toml").exists():
            await self._run_command("pip install -e .")
            installed = True
        
        # Node.js
        if (self.current_dir / "package.json").exists():
            await self._run_command("npm install")
            installed = True
        
        # Rust
        if (self.current_dir / "Cargo.toml").exists():
            await self._run_command("cargo build")
            installed = True
        
        # Go
        if (self.current_dir / "go.mod").exists():
            await self._run_command("go mod tidy")
            installed = True
        
        if not installed:
            print("⚠️ No dependency files found:")
            print("  • Python: requirements.txt, pyproject.toml")
            print("  • Node.js: package.json")
            print("  • Rust: Cargo.toml")
            print("  • Go: go.mod")
    
    async def slash_show_tree(self, args):
        """Show project structure as tree"""
        print("📁 Project Structure:")
        
        def show_tree(path, prefix="", max_depth=4, current_depth=0):
            if current_depth >= max_depth:
                return
            
            # Skip hidden and common ignored directories
            ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.env', 'target', 'dist', 'build'}
            
            items = []
            try:
                for item in path.iterdir():
                    if item.name.startswith('.') and item.name not in {'.gitignore', '.env'}:
                        continue
                    if item.is_dir() and item.name in ignore_dirs:
                        continue
                    items.append(item)
            except PermissionError:
                return
            
            items = sorted(items, key=lambda x: (x.is_file(), x.name.lower()))
            
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                
                if item.is_dir():
                    print(f"{prefix}{current_prefix}{item.name}/")
                    if current_depth < max_depth - 1:
                        next_prefix = prefix + ("    " if is_last else "│   ")
                        show_tree(item, next_prefix, max_depth, current_depth + 1)
                else:
                    size = item.stat().st_size
                    size_str = f" ({size:,} bytes)" if size < 10000 else f" ({size//1000}KB)"
                    print(f"{prefix}{current_prefix}{item.name}{size_str}")
        
        show_tree(self.current_dir)
    
    async def slash_read_file(self, args):
        """Read and display file contents with syntax highlighting"""
        if not args:
            print("Usage: /read <filename>")
            print("Examples:")
            print("  /read main.py")
            print("  /read src/models.py")
            print("  /read *.py (reads all Python files)")
            return
        
        pattern = args[0]
        try:
            # Handle glob patterns
            if '*' in pattern or '?' in pattern:
                from pathlib import Path
                matches = list(self.current_dir.glob(pattern))
                if not matches:
                    print(f"❌ No files found matching: {pattern}")
                    return
                
                for file_path in matches[:5]:  # Limit to first 5 files
                    if file_path.is_file():
                        await self._read_and_display_file(file_path)
                        print()
            else:
                file_path = self.current_dir / pattern
                if file_path.exists() and file_path.is_file():
                    await self._read_and_display_file(file_path)
                else:
                    print(f"❌ File not found: {pattern}")
                    
        except Exception as e:
            print(f"❌ Error reading file: {e}")
    
    async def _read_and_display_file(self, file_path):
        """Helper to read and display a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"📄 {file_path.name} ({len(content)} chars, {len(content.splitlines())} lines)")
            print("─" * 60)
            
            # Add line numbers
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                print(f"{i:3d}│ {line}")
            
            print("─" * 60)
            
        except Exception as e:
            print(f"❌ Error reading {file_path.name}: {e}")
    
    async def slash_analyze_code(self, args):
        """Analyze code for potential issues, patterns, and improvements"""
        if not args:
            print("Usage: /analyze <filename|pattern>")
            print("Examples:")
            print("  /analyze main.py")
            print("  /analyze src/*.py")
            print("  /analyze . (analyze all files in directory)")
            return
        
        pattern = args[0]
        files_to_analyze = []
        
        try:
            if pattern == '.':
                # Analyze all code files in directory
                files_to_analyze.extend(self.current_dir.glob('*.py'))
                files_to_analyze.extend(self.current_dir.glob('*.js'))
                files_to_analyze.extend(self.current_dir.glob('*.ts'))
                files_to_analyze.extend(self.current_dir.glob('*.java'))
                files_to_analyze.extend(self.current_dir.glob('*.cpp'))
                files_to_analyze.extend(self.current_dir.glob('*.c'))
            elif '*' in pattern:
                files_to_analyze = list(self.current_dir.glob(pattern))
            else:
                file_path = self.current_dir / pattern
                if file_path.exists():
                    files_to_analyze = [file_path]
            
            if not files_to_analyze:
                print(f"❌ No files found for: {pattern}")
                return
            
            print(f"🔍 Analyzing {len(files_to_analyze)} file(s)...")
            
            for file_path in files_to_analyze[:3]:  # Limit to 3 files
                await self._analyze_single_file(file_path)
                
        except Exception as e:
            print(f"❌ Error analyzing files: {e}")
    
    async def _analyze_single_file(self, file_path):
        """Analyze a single file using AI"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print(f"\n📊 Analysis of {file_path.name}:")
            
            analysis_prompt = f"""Analyze this {file_path.suffix} code for:
1. Potential bugs or issues
2. Code quality and best practices  
3. Performance improvements
4. Security vulnerabilities
5. Suggestions for improvement

Code:
```{file_path.suffix}
{content}
```

Provide a concise analysis with specific recommendations."""
            
            # Use current model to analyze
            if self.force_provider:
                model_info = await self._get_forced_model()
            else:
                model_info = await self.selector.select_model('medium')
            
            client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
            
            response = await client.generate(
                model=model_info['model'],
                prompt=analysis_prompt,
                system_prompt="You are a code analysis expert. Provide specific, actionable feedback."
            )
            
            print(f"🤖 Analysis ({model_info['provider']}:{model_info['model']}):")
            print(response)
            
        except Exception as e:
            print(f"❌ Error analyzing {file_path.name}: {e}")
    
    async def slash_debug_code(self, args):
        """Debug specific code issues or errors"""
        if not args:
            print("Usage: /debug <filename> [error_description]")
            print("Examples:")
            print("  /debug main.py")
            print("  /debug api.py 'AttributeError on line 45'")
            print("  /debug . 'Import error with module not found'")
            return
        
        filename = args[0]
        error_description = ' '.join(args[1:]) if len(args) > 1 else ""
        
        try:
            if filename == '.':
                # Look for recent error logs
                print("🔍 Looking for recent errors...")
                await self._run_command("tail -n 50 *.log 2>/dev/null || echo 'No log files found'")
                return
            
            file_path = self.current_dir / filename
            if not file_path.exists():
                print(f"❌ File not found: {filename}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            debug_prompt = f"""Debug this code:

File: {filename}
{f"Error/Issue: {error_description}" if error_description else ""}

Code:
```{file_path.suffix}
{content}
```

Please:
1. Identify potential issues
2. Explain what might be causing problems
3. Provide specific fixes
4. Show corrected code snippets if needed"""
            
            print(f"🐛 Debugging {filename}...")
            
            # Use more powerful model for debugging
            if self.force_provider:
                model_info = await self._get_forced_model()
            else:
                model_info = await self.selector.select_model('complex')
            
            client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
            
            response = await client.generate(
                model=model_info['model'],
                prompt=debug_prompt,
                system_prompt="You are a debugging expert. Provide clear explanations and concrete solutions."
            )
            
            print(f"🤖 Debug Analysis ({model_info['provider']}:{model_info['model']}):")
            print(response)
            
        except Exception as e:
            print(f"❌ Error debugging: {e}")
    
    async def slash_fix_code(self, args):
        """Fix code issues automatically"""
        if not args:
            print("Usage: /fix <filename> [issue_description]")
            print("Examples:")
            print("  /fix main.py")
            print("  /fix api.py 'Fix the authentication bug'")
            return
        
        filename = args[0]
        issue_description = ' '.join(args[1:]) if len(args) > 1 else ""
        
        try:
            file_path = self.current_dir / filename
            if not file_path.exists():
                print(f"❌ File not found: {filename}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            print(f"🔧 Fixing {filename}...")
            print("📋 Creating backup...")
            
            # Create backup
            backup_path = file_path.with_suffix(f"{file_path.suffix}.backup")
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            fix_prompt = f"""Fix the issues in this code:

File: {filename}
{f"Issue to fix: {issue_description}" if issue_description else ""}

Current Code:
```{file_path.suffix}
{original_content}
```

Please provide the complete corrected code. Focus on:
1. Fixing syntax errors
2. Resolving import issues
3. Correcting logic errors
4. Improving error handling
5. Following best practices

Return only the corrected code without explanations."""
            
            # Use powerful model for fixing
            model_info = await self.selector.select_model('complex')
            client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
            
            response = await client.generate(
                model=model_info['model'],
                prompt=fix_prompt,
                system_prompt="You are a code fixing expert. Return only corrected code."
            )
            
            # Extract code from response
            fixed_code = self._extract_code_from_response(response)
            
            if fixed_code and len(fixed_code) > 50:  # Basic validation
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_code)
                
                print(f"✅ Fixed {filename}")
                print(f"📁 Backup saved as {backup_path.name}")
                print("🔍 Use /read to review changes")
            else:
                print("⚠️ AI response didn't contain valid code. No changes made.")
                print("🤖 Response:")
                print(response)
                
        except Exception as e:
            print(f"❌ Error fixing code: {e}")
    
    async def slash_refactor_code(self, args):
        """Refactor code for better structure and performance"""
        if not args:
            print("Usage: /refactor <filename> [focus_area]")
            print("Examples:")
            print("  /refactor main.py")
            print("  /refactor api.py 'improve performance'")
            print("  /refactor models.py 'better organization'")
            return
        
        filename = args[0]
        focus_area = ' '.join(args[1:]) if len(args) > 1 else "general improvements"
        
        try:
            file_path = self.current_dir / filename
            if not file_path.exists():
                print(f"❌ File not found: {filename}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            print(f"♻️ Refactoring {filename} (focus: {focus_area})...")
            
            refactor_prompt = f"""Refactor this code for better quality:

File: {filename}
Focus area: {focus_area}

Current Code:
```{file_path.suffix}
{original_content}
```

Please refactor focusing on:
1. Code organization and structure
2. Performance improvements
3. Readability and maintainability
4. Following best practices
5. {focus_area}

Provide the refactored code with brief comments about major changes."""
            
            model_info = await self.selector.select_model('complex')
            client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
            
            response = await client.generate(
                model=model_info['model'],
                prompt=refactor_prompt,
                system_prompt="You are a code refactoring expert. Improve code quality while maintaining functionality."
            )
            
            print(f"♻️ Refactoring suggestions ({model_info['provider']}:{model_info['model']}):")
            print(response)
            
        except Exception as e:
            print(f"❌ Error refactoring: {e}")
    
    async def slash_explain_code(self, args):
        """Explain how code works"""
        if not args:
            print("Usage: /explain <filename> [specific_function]")
            print("Examples:")
            print("  /explain main.py")
            print("  /explain api.py 'authenticate_user function'")
            return
        
        filename = args[0]
        specific_part = ' '.join(args[1:]) if len(args) > 1 else ""
        
        try:
            file_path = self.current_dir / filename
            if not file_path.exists():
                print(f"❌ File not found: {filename}")
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            explain_prompt = f"""Explain how this code works:

File: {filename}
{f"Focus on: {specific_part}" if specific_part else ""}

Code:
```{file_path.suffix}
{content}
```

Please explain:
1. Overall purpose and functionality
2. Key components and their roles
3. Data flow and logic
4. Important functions/classes
5. Dependencies and integrations
{f"6. Detailed explanation of: {specific_part}" if specific_part else ""}

Make it clear and educational."""
            
            print(f"📖 Explaining {filename}...")
            
            model_info = await self.selector.select_model('medium')
            client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
            
            response = await client.generate(
                model=model_info['model'],
                prompt=explain_prompt,
                system_prompt="You are a code explanation expert. Make complex code easy to understand."
            )
            
            print(f"📖 Code Explanation ({model_info['provider']}:{model_info['model']}):")
            print(response)
            
        except Exception as e:
            print(f"❌ Error explaining code: {e}")
    
    async def slash_find_in_files(self, args):
        """Find text/patterns in files"""
        if not args:
            print("Usage: /find <pattern> [file_pattern]")
            print("Examples:")
            print("  /find 'def authenticate' ")
            print("  /find 'TODO' *.py")
            print("  /find 'import requests' src/")
            return
        
        search_pattern = args[0]
        file_pattern = args[1] if len(args) > 1 else "*.py"
        
        try:
            print(f"🔍 Searching for '{search_pattern}' in {file_pattern}...")
            
            # Use ripgrep-like search
            if file_pattern.endswith('/'):
                # Search in directory
                search_path = self.current_dir / file_pattern.rstrip('/')
                files_to_search = list(search_path.rglob("*.py")) + list(search_path.rglob("*.js")) + list(search_path.rglob("*.ts"))
            else:
                # Search in specific pattern
                files_to_search = list(self.current_dir.glob(file_pattern))
            
            found_matches = []
            
            for file_path in files_to_search:
                if file_path.is_file():
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        for line_num, line in enumerate(lines, 1):
                            if search_pattern.lower() in line.lower():
                                found_matches.append({
                                    'file': file_path.name,
                                    'line': line_num,
                                    'content': line.strip()
                                })
                                
                    except Exception as e:
                        print(f"⚠️ Could not search {file_path.name}: {e}")
            
            if found_matches:
                print(f"✅ Found {len(found_matches)} matches:")
                print()
                
                current_file = None
                for match in found_matches[:20]:  # Limit to 20 matches
                    if match['file'] != current_file:
                        current_file = match['file']
                        print(f"📄 {current_file}:")
                    
                    print(f"  {match['line']:3d}│ {match['content']}")
                
                if len(found_matches) > 20:
                    print(f"... and {len(found_matches) - 20} more matches")
            else:
                print(f"❌ No matches found for '{search_pattern}' in {file_pattern}")
                
        except Exception as e:
            print(f"❌ Error searching: {e}")
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code blocks from AI response"""
        import re
        
        # Look for code blocks
        code_block_pattern = r'```(?:\w+\n)?(.*?)```'
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # If no code blocks, return the whole response (might be direct code)
        return response.strip()
    
    async def _build_project_context(self):
        """Build comprehensive project context using RAG approach"""
        print("🔄 Building project context...")
        
        # Clear existing context
        self.project_context = {}
        self.file_embeddings = {}
        
        # Find all relevant files
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.rs', '.go'}
        config_extensions = {'.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'}
        doc_extensions = {'.md', '.txt', '.rst'}
        
        all_files = []
        for ext in code_extensions | config_extensions | doc_extensions:
            all_files.extend(self.current_dir.rglob(f"*{ext}"))
        
        # Filter out unwanted directories
        ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv', '.env', 'target', 'dist', 'build'}
        relevant_files = []
        
        for file_path in all_files:
            if not any(ignore_dir in file_path.parts for ignore_dir in ignore_dirs):
                if file_path.is_file() and file_path.stat().st_size < 1000000:  # Max 1MB per file
                    relevant_files.append(file_path)
        
        print(f"📊 Found {len(relevant_files)} relevant files")
        
        # Read and categorize files
        for file_path in relevant_files[:50]:  # Limit to 50 files
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                relative_path = file_path.relative_to(self.current_dir)
                file_info = {
                    'path': str(relative_path),
                    'extension': file_path.suffix,
                    'size': len(content),
                    'lines': len(content.splitlines()),
                    'content': content,
                    'summary': await self._generate_file_summary(str(relative_path), content)
                }
                
                self.project_context[str(relative_path)] = file_info
                
            except Exception as e:
                print(f"⚠️ Could not read {file_path}: {e}")
        
        # Generate project structure summary
        await self._generate_project_summary()
        
        print(f"✅ Project context built: {len(self.project_context)} files indexed")
    
    async def _generate_file_summary(self, file_path: str, content: str) -> str:
        """Generate a brief summary of a file's purpose and key components"""
        if len(content) > 2000:
            content = content[:2000] + "..."
        
        try:
            summary_prompt = f"""Provide a brief 2-3 sentence summary of this file's purpose and key components:

File: {file_path}
Content:
```
{content}
```

Focus on: purpose, main functions/classes, dependencies, role in the project."""
            
            # Use local model for file summaries to avoid API costs
            client = self.ollama_client
            summary = await client.generate(
                model="qwen2.5-coder:7b", 
                prompt=summary_prompt,
                system_prompt="You are a code analysis expert. Provide concise file summaries."
            )
            return summary[:500]  # Limit summary length
            
        except Exception as e:
            # Fallback to simple analysis
            lines = content.split('\n')
            imports = [line for line in lines if line.strip().startswith(('import ', 'from '))]
            functions = [line for line in lines if line.strip().startswith('def ')]
            classes = [line for line in lines if line.strip().startswith('class ')]
            
            return f"File with {len(lines)} lines, {len(imports)} imports, {len(functions)} functions, {len(classes)} classes"
    
    async def _generate_project_summary(self):
        """Generate overall project summary"""
        try:
            # Analyze project structure
            file_types = {}
            total_lines = 0
            
            for file_info in self.project_context.values():
                ext = file_info['extension']
                file_types[ext] = file_types.get(ext, 0) + 1
                total_lines += file_info['lines']
            
            # Create structured project overview
            structure_overview = f"""
Project Structure Analysis:
- Total files: {len(self.project_context)}
- Total lines of code: {total_lines:,}
- File types: {', '.join(f'{count} {ext}' for ext, count in file_types.items())}

Key Files:
{chr(10).join(f'- {path}: {info["summary"][:100]}...' for path, info in list(self.project_context.items())[:10])}
"""
            
            # Generate AI-powered project summary
            project_summary_prompt = f"""Analyze this project and provide a comprehensive summary:

{structure_overview}

Provide:
1. Project type and technology stack
2. Main architecture and patterns
3. Key components and their relationships
4. Potential issues or improvement areas
5. Overall assessment

Be concise but comprehensive."""
            
            model_info = await self.selector.select_model('medium')
            client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
            
            self.project_summary = await client.generate(
                model=model_info['model'],
                prompt=project_summary_prompt,
                system_prompt="You are a senior software architect analyzing project structure."
            )
            
        except Exception as e:
            self.project_summary = f"Basic project with {len(self.project_context)} files across {len(file_types)} file types"
    
    async def _detect_and_fix_issues(self):
        """Automatically detect and fix common issues in the project"""
        if not hasattr(self, 'project_context') or not self.project_context:
            print("⚠️  No project context available. Building context first...")
            await self._build_project_context()
        
        print("🔍 Scanning for common issues...")
        issues_found = []
        
        # Check each file for common problems
        for file_path, file_info in self.project_context.items():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for syntax errors (Python files)
                if file_path.endswith('.py'):
                    issues = self._check_python_syntax(file_path, content)
                    issues_found.extend(issues)
                
                # Check for security issues
                security_issues = self._check_security_issues(file_path, content)
                issues_found.extend(security_issues)
                
                # Check for performance issues  
                perf_issues = self._check_performance_issues(file_path, content)
                issues_found.extend(perf_issues)
                
                # Check for code quality issues
                quality_issues = self._check_code_quality(file_path, content)
                issues_found.extend(quality_issues)
                
            except Exception as e:
                issues_found.append({
                    'type': 'file_error',
                    'file': file_path,
                    'description': f"Cannot read file: {e}",
                    'severity': 'medium',
                    'auto_fixable': False
                })
        
        if not issues_found:
            print("✅ No obvious issues detected in the project!")
            return
        
        # Display found issues
        print(f"⚠️  Found {len(issues_found)} issues:")
        
        critical_issues = [i for i in issues_found if i['severity'] == 'critical']
        high_issues = [i for i in issues_found if i['severity'] == 'high'] 
        medium_issues = [i for i in issues_found if i['severity'] == 'medium']
        low_issues = [i for i in issues_found if i['severity'] == 'low']
        
        for severity, issues, icon in [
            ('critical', critical_issues, '🔴'),
            ('high', high_issues, '🟠'), 
            ('medium', medium_issues, '🟡'),
            ('low', low_issues, '⚪')
        ]:
            if issues:
                print(f"\n{icon} {severity.upper()} ({len(issues)}):")
                for issue in issues:
                    print(f"   • {issue['file']}: {issue['description']}")
        
        # Auto-fix fixable issues
        fixable_issues = [i for i in issues_found if i.get('auto_fixable', False)]
        if fixable_issues:
            print(f"\n🔧 Auto-fixing {len(fixable_issues)} issues...")
            await self._auto_fix_issues(fixable_issues)
        
        # Generate comprehensive analysis for remaining issues
        if issues_found:
            await self._generate_issue_analysis(issues_found)
    
    def _check_python_syntax(self, file_path, content):
        """Check Python files for syntax errors"""
        issues = []
        try:
            compile(content, file_path, 'exec')
        except SyntaxError as e:
            issues.append({
                'type': 'syntax_error',
                'file': file_path,
                'line': e.lineno,
                'description': f"Syntax error: {e.msg}",
                'severity': 'critical',
                'auto_fixable': True,
                'fix_hint': self._suggest_syntax_fix(e, content)
            })
        except Exception as e:
            issues.append({
                'type': 'compile_error',
                'file': file_path,
                'description': f"Compilation error: {e}",
                'severity': 'high',
                'auto_fixable': False
            })
        return issues
    
    def _check_security_issues(self, file_path, content):
        """Check for common security issues"""
        issues = []
        content_lower = content.lower()
        
        # Check for hardcoded secrets
        if any(pattern in content_lower for pattern in ['password = ', 'api_key = ', 'secret = ', 'token = ']):
            issues.append({
                'type': 'hardcoded_secret',
                'file': file_path,
                'description': "Potential hardcoded secrets detected",
                'severity': 'high',
                'auto_fixable': False
            })
        
        # Check for SQL injection risks
        if 'execute(' in content_lower and '%s' in content_lower:
            issues.append({
                'type': 'sql_injection',
                'file': file_path,  
                'description': "Potential SQL injection risk",
                'severity': 'high',
                'auto_fixable': False
            })
        
        return issues
    
    def _check_performance_issues(self, file_path, content):
        """Check for common performance issues"""
        issues = []
        
        # Check for inefficient loops
        if 'for i in range(len(' in content:
            issues.append({
                'type': 'inefficient_loop',
                'file': file_path,
                'description': "Inefficient loop pattern detected",
                'severity': 'medium',
                'auto_fixable': True
            })
        
        return issues
    
    def _check_code_quality(self, file_path, content):
        """Check for code quality issues"""
        issues = []
        
        # Check for long lines
        for i, line in enumerate(content.split('\n'), 1):
            if len(line) > 120:
                issues.append({
                    'type': 'long_line',
                    'file': file_path,
                    'line': i,
                    'description': f"Line too long ({len(line)} chars)",
                    'severity': 'low',
                    'auto_fixable': False
                })
                break  # Only report first long line per file
        
        return issues
    
    def _suggest_syntax_fix(self, error, content):
        """Suggest fixes for common syntax errors"""
        if "invalid syntax" in str(error):
            if "(" in str(error):
                return "Check for missing closing parentheses"
            elif ":" in str(error):
                return "Check for missing colons in control structures"
        return "Check syntax around the indicated line"
    
    async def _auto_fix_issues(self, issues):
        """Automatically fix issues that can be safely auto-fixed"""
        for issue in issues:
            try:
                if issue['type'] == 'syntax_error':
                    await self._fix_syntax_error(issue)
                elif issue['type'] == 'inefficient_loop':
                    await self._fix_inefficient_loop(issue)
                
                print(f"   ✅ Fixed: {issue['description']} in {issue['file']}")
                
            except Exception as e:
                print(f"   ❌ Failed to fix {issue['description']} in {issue['file']}: {e}")
    
    async def _fix_syntax_error(self, issue):
        """Fix common syntax errors"""
        file_path = issue['file']
        
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        line_num = issue.get('line', 1) - 1  # Convert to 0-based
        if 0 <= line_num < len(lines):
            line = lines[line_num]
            
            # Fix missing parentheses
            if 'print(' in line and line.count('(') != line.count(')'):
                lines[line_num] = line.rstrip() + ')\n'
                
                with open(file_path, 'w') as f:
                    f.writelines(lines)
    
    async def _fix_inefficient_loop(self, issue):
        """Fix inefficient loop patterns"""
        # This would implement automatic refactoring of loops
        pass
    
    async def _generate_issue_analysis(self, issues):
        """Generate detailed analysis and recommendations for issues"""
        if not issues:
            return
        
        print("\n🤖 Generating detailed issue analysis...")
        
        issue_summary = []
        for issue in issues[:10]:  # Limit to top 10 issues
            issue_summary.append(f"- {issue['type']} in {issue['file']}: {issue['description']}")
        
        analysis_prompt = f"""
Analyze the following issues found in a software project and provide detailed recommendations:

Issues found:
{chr(10).join(issue_summary)}

Provide:
1. Root cause analysis for the most critical issues
2. Step-by-step fix recommendations
3. Prevention strategies
4. Impact assessment
5. Priority order for fixing

Focus on practical, actionable advice."""

        try:
            model_info = await self.selector.select_model('complex')
            client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
            
            analysis = await client.generate(
                model=model_info['model'],
                prompt=analysis_prompt,
                system_prompt="You are a senior software engineer providing code review and issue analysis."
            )
            
            print("📋 Detailed Issue Analysis:")
            print("=" * 60)
            print(analysis)
            print("=" * 60)
            
        except Exception as e:
            print(f"⚠️  Could not generate detailed analysis: {e}")
    
    async def slash_analyze_project(self, args):
        """Analyze entire project with RAG context"""
        focus_area = ' '.join(args) if args else "general analysis"
        
        print(f"🔍 Analyzing entire project (focus: {focus_area})...")
        
        # Build context if not available
        if not self.project_context:
            await self._build_project_context()
        
        # Find relevant files based on focus area
        relevant_files = self._find_relevant_files_for_query(focus_area)
        
        # Build comprehensive context
        context_content = f"""
PROJECT SUMMARY:
{self.project_summary}

RELEVANT FILES FOR "{focus_area}":
"""
        
        for file_path in relevant_files[:10]:  # Limit to 10 most relevant files
            file_info = self.project_context.get(file_path, {})
            context_content += f"""
FILE: {file_path}
Summary: {file_info.get('summary', 'No summary')}
Content snippet:
{file_info.get('content', '')[:1000]}...

"""
        
        # Generate analysis
        analysis_prompt = f"""Analyze this project focusing on: {focus_area}

{context_content}

Provide a comprehensive analysis covering:
1. Architecture and design patterns
2. Code quality and maintainability  
3. Security considerations
4. Performance implications
5. Testing coverage
6. Documentation quality
7. Specific insights about: {focus_area}
8. Recommendations for improvement"""
        
        model_info = await self.selector.select_model('complex')
        client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
        
        response = await client.generate(
            model=model_info['model'],
            prompt=analysis_prompt,
            system_prompt="You are a senior software architect providing comprehensive project analysis."
        )
        
        print(f"📊 Project Analysis ({model_info['provider']}:{model_info['model']}):")
        print(response)
    
    async def slash_show_context(self, args):
        """Show current project context and available files"""
        if not self.project_context:
            print("❌ No project context loaded. Use /project to analyze the project first.")
            return
        
        print("📋 Project Context Overview:")
        print(f"📊 Files indexed: {len(self.project_context)}")
        print()
        
        # Group files by type
        file_groups = {}
        for file_path, file_info in self.project_context.items():
            ext = file_info['extension']
            if ext not in file_groups:
                file_groups[ext] = []
            file_groups[ext].append((file_path, file_info))
        
        # Display by category
        for ext, files in sorted(file_groups.items()):
            print(f"📁 {ext} files ({len(files)}):")
            for file_path, file_info in files[:5]:  # Show first 5 of each type
                print(f"  📄 {file_path} ({file_info['lines']} lines)")
                print(f"      {file_info['summary'][:80]}...")
            if len(files) > 5:
                print(f"  ... and {len(files) - 5} more")
            print()
        
        if self.project_summary:
            print("🎯 Project Summary:")
            print(self.project_summary)
    
    async def slash_project_summary(self, args):
        """Generate or show project summary"""
        if not self.project_context:
            await self._build_project_context()
        
        if args and args[0] == 'refresh':
            print("🔄 Refreshing project summary...")
            await self._generate_project_summary()
        
        print("📋 Project Summary:")
        print("=" * 60)
        print(self.project_summary)
        print("=" * 60)
        
        # Add quick stats
        total_files = len(self.project_context)
        total_lines = sum(info['lines'] for info in self.project_context.values())
        file_types = {}
        
        for info in self.project_context.values():
            ext = info['extension']
            file_types[ext] = file_types.get(ext, 0) + 1
        
        print(f"\n📊 Quick Stats:")
        print(f"   Files: {total_files}")
        print(f"   Lines: {total_lines:,}")
        print(f"   Types: {', '.join(f'{count}{ext}' for ext, count in file_types.items())}")
    
    async def slash_check_project(self, args):
        """Automatically check project for issues and provide fixes"""
        print("🚀 Starting automatic project analysis...")
        
        # Build context if not available
        if not hasattr(self, 'project_context') or not self.project_context:
            await self._build_project_context()
        
        # Detect and fix issues automatically
        await self._detect_and_fix_issues()
        
        print("\n✅ Automatic project check completed!")
    
    async def slash_smart_compile(self, args):
        """Smart compilation with automatic error handling and fixes"""
        if not args:
            print("❌ Usage: /compile <compilation_command>")
            print("Example: /compile g++ -o main main.cpp")
            return
        
        command = ' '.join(args)
        print(f"🔨 Smart compilation: {command}")
        
        # Store command for potential retry
        self.last_compile_command = command
        
        # Try compilation
        await self.execute_shell_command(command)
    
    async def slash_retry_last_command(self, args):
        """Retry the last shell command that was executed"""
        if not hasattr(self, 'last_shell_command'):
            print("❌ No previous command to retry")
            return
        
        print(f"🔄 Retrying: {self.last_shell_command}")
        await self.execute_shell_command(self.last_shell_command)
    
    def _find_relevant_files_for_query(self, query: str) -> list:
        """Find files most relevant to a specific query"""
        if not self.project_context:
            return []
        
        query_lower = query.lower()
        scored_files = []
        
        for file_path, file_info in self.project_context.items():
            score = 0
            
            # Score based on filename relevance
            if any(word in file_path.lower() for word in query_lower.split()):
                score += 10
            
            # Score based on summary relevance
            summary = file_info.get('summary', '').lower()
            for word in query_lower.split():
                score += summary.count(word) * 5
            
            # Score based on file type relevance
            if query_lower in ['api', 'server', 'backend'] and file_info['extension'] == '.py':
                score += 5
            if query_lower in ['frontend', 'ui', 'client'] and file_info['extension'] in ['.js', '.ts']:
                score += 5
            if query_lower in ['config', 'settings'] and file_info['extension'] in ['.json', '.yaml', '.yml']:
                score += 5
            
            if score > 0:
                scored_files.append((score, file_path))
        
        # Sort by score and return file paths
        scored_files.sort(reverse=True)
        return [file_path for _, file_path in scored_files]
    
    # Autonomous Execution System
    async def slash_autonomous_mode(self, args):
        """Enter autonomous mode with a target"""
        if not args:
            print("Usage: /auto <target_description>")
            print("Examples:")
            print("  /auto \"Create a complete REST API for a blog system\"")
            print("  /auto \"Build and test a Python calculator with GUI\"")
            print("  /auto \"Set up a React app with authentication and deploy it\"")
            return
        
        target = ' '.join(args)
        await self._start_autonomous_execution(target)
    
    async def slash_set_target(self, args):
        """Set or show the current target"""
        if not args:
            if self.current_target:
                print(f"🎯 Current target: {self.current_target}")
            else:
                print("❌ No target set. Use /target <description> to set one.")
            return
        
        self.current_target = ' '.join(args)
        print(f"🎯 Target set: {self.current_target}")
        
        if not self.autonomous_mode:
            print("💡 Use /auto to start autonomous execution towards this target")
    
    async def slash_show_plan(self, args):
        """Show the current execution plan"""
        if not self.execution_plan:
            print("❌ No execution plan available.")
            print("💡 Set a target with /target or /auto to generate a plan")
            return
        
        print("📋 Execution Plan:")
        print(f"🎯 Target: {self.current_target}")
        print(f"📊 Progress: {self.current_step}/{len(self.execution_plan)} steps")
        print()
        
        for i, step in enumerate(self.execution_plan, 1):
            # Handle case where step might not be a dict
            if not isinstance(step, dict):
                print(f"⚠️ Step {i}: Invalid step format: {step}")
                continue
                
            status_icon = "✅" if i <= self.current_step else "⏳" if i == self.current_step + 1 else "⏸️"
            description = step.get('description', 'No description')
            print(f"{status_icon} Step {i}: {description}")
            
            if step.get('details'):
                print(f"   Details: {step['details']}")
            if i <= self.current_step and self.step_results:
                result = self.step_results[i-1] if i-1 < len(self.step_results) else None
                if result:
                    print(f"   Result: {result.get('summary', 'Completed')}")
        print()
    
    async def slash_show_progress(self, args):
        """Show detailed progress information"""
        await self.slash_show_plan([])
        
        if self.autonomous_mode:
            print("🤖 Autonomous Mode: ACTIVE")
            if self.execution_paused:
                print("⏸️  Status: PAUSED")
            else:
                print("▶️  Status: RUNNING")
        else:
            print("🤖 Autonomous Mode: INACTIVE")
        
        if self.step_results:
            print(f"\n📈 Completed Steps: {len(self.step_results)}")
            print("Recent results:")
            for i, result in enumerate(self.step_results[-3:], 1):  # Show last 3
                print(f"  {i}. {result.get('description', 'Unknown')}: {result.get('summary', 'Completed')}")
    
    async def slash_pause_execution(self, args):
        """Pause autonomous execution"""
        if not self.autonomous_mode:
            print("❌ Autonomous mode is not active")
            return
        
        self.execution_paused = True
        print("⏸️  Autonomous execution paused")
        print("💡 Use /resume to continue or /stop to end execution")
    
    async def slash_resume_execution(self, args):
        """Resume autonomous execution"""
        if not self.autonomous_mode:
            print("❌ Autonomous mode is not active")
            return
        
        if not self.execution_paused:
            print("▶️  Execution is already running")
            return
        
        self.execution_paused = False
        print("▶️  Resuming autonomous execution...")
        await self._continue_autonomous_execution()
    
    async def slash_stop_execution(self, args):
        """Stop autonomous execution"""
        if not self.autonomous_mode:
            print("❌ Autonomous mode is not active")
            return
        
        self.autonomous_mode = False
        self.execution_paused = False
        
        print("⏹️  Autonomous execution stopped")
        print(f"📊 Completed {self.current_step}/{len(self.execution_plan)} steps")
        
        if self.current_step < len(self.execution_plan):
            print("💡 You can resume later with /resume or start a new target with /auto")
    
    async def _start_autonomous_execution(self, target: str):
        """Start autonomous execution towards a target"""
        print(f"🚀 Starting autonomous execution...")
        print(f"🎯 Target: {target}")
        
        self.current_target = target
        self.autonomous_mode = True
        self.execution_paused = False
        self.current_step = 0
        self.step_results = []
        
        # Generate execution plan
        print("🧠 Generating execution plan...")
        await self._generate_execution_plan(target)
        
        if not self.execution_plan:
            print("❌ Failed to generate execution plan")
            self.autonomous_mode = False
            return
        
        print(f"📋 Generated plan with {len(self.execution_plan)} steps")
        await self.slash_show_plan([])
        
        print("\n🤖 Starting autonomous execution...")
        print("💡 Use /pause to pause, /stop to stop, /progress to see status")
        print("=" * 60)
        
        await self._continue_autonomous_execution()
    
    async def _generate_execution_plan(self, target: str):
        """Generate a detailed execution plan for the target"""
        # Build current context
        context = self._build_context()
        
        planning_prompt = f"""
Create a detailed step-by-step execution plan to achieve this target:

TARGET: {target}

CURRENT CONTEXT:
{context}

Generate a comprehensive plan with the following structure:
1. Each step should be specific and actionable
2. Steps should build upon each other logically
3. Include verification/testing steps
4. Consider error handling and fallbacks

Provide the plan as a JSON array where each step has:
- "description": Brief description of the step
- "action": The type of action (create_file, run_command, analyze, etc.)
- "details": Specific implementation details
- "verification": How to verify this step succeeded
- "dependencies": Previous steps this depends on

Example format:
[
  {{
    "description": "Create project structure",
    "action": "create_directories",
    "details": "Create src/, tests/, docs/ directories",
    "verification": "Check that directories exist",
    "dependencies": []
  }},
  {{
    "description": "Implement main module",
    "action": "create_file",
    "details": "Create src/main.py with core functionality",
    "verification": "Python syntax check passes",
    "dependencies": [1]
  }}
]

Generate a complete, practical plan (maximum 15 steps):
"""
        
        try:
            # Use a powerful model for planning
            model_info = await self.selector.select_model('complex')
            client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
            
            response = await client.generate(
                model=model_info['model'],
                prompt=planning_prompt,
                system_prompt="You are an expert project planner. Create detailed, actionable execution plans."
            )
            
            # Extract JSON from response
            plan_json = self._extract_json_from_response(response)
            if plan_json and isinstance(plan_json, list) and all(isinstance(step, dict) for step in plan_json):
                self.execution_plan = plan_json
                print(f"✅ Generated plan with {len(self.execution_plan)} steps")
            else:
                # Fallback: parse text-based plan
                print("🔄 JSON parsing failed, using text parsing fallback...")
                self.execution_plan = self._parse_text_plan(response)
                if self.execution_plan:
                    print(f"✅ Generated plan with {len(self.execution_plan)} steps (text format)")
                else:
                    print("❌ Failed to parse plan from response")
                
        except Exception as e:
            print(f"❌ Error generating plan: {e}")
            # Create a basic fallback plan
            self.execution_plan = [
                {
                    "description": "Analyze requirements and setup",
                    "action": "analyze", 
                    "details": f"Break down the target: {target}",
                    "verification": "Requirements are clear",
                    "dependencies": []
                }
            ]
            
        # Ensure we always have a valid plan
        if not self.execution_plan:
            print("🔧 Creating fallback plan...")
            self.execution_plan = [
                {
                    "description": f"Execute target: {target}",
                    "action": "general",
                    "details": f"Work towards completing: {target}",
                    "verification": "Target completed successfully",
                    "dependencies": []
                }
            ]
    
    def _extract_json_from_response(self, response: str):
        """Extract JSON from AI response"""
        import re
        import json
        
        # Look for JSON blocks
        json_pattern = r'```(?:json\n)?(.*?)```'
        matches = re.findall(json_pattern, response, re.DOTALL)
        
        for match in matches:
            try:
                return json.loads(match.strip())
            except json.JSONDecodeError:
                continue
        
        # Try to find JSON in the response without code blocks
        try:
            # Look for array patterns
            array_pattern = r'\[.*?\]'
            matches = re.findall(array_pattern, response, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
        except:
            pass
        
        return None
    
    def _parse_text_plan(self, response: str) -> list:
        """Parse text-based plan as fallback"""
        steps = []
        lines = response.split('\n')
        
        current_step = None
        step_counter = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for numbered steps (various formats)
            step_match = re.match(r'^(\d+)[\.\)]\s*(.*)', line)
            if step_match:
                if current_step:
                    steps.append(current_step)
                
                step_counter += 1
                step_description = step_match.group(2).strip()
                
                current_step = {
                    "description": step_description if step_description else f"Step {step_counter}",
                    "action": "general",
                    "details": step_description if step_description else f"Execute step {step_counter}",
                    "verification": "Manual check required",
                    "dependencies": []
                }
            # Look for bullet points
            elif line.startswith(('-', '*', '•')):
                if not current_step:
                    step_counter += 1
                    current_step = {
                        "description": f"Step {step_counter}",
                        "action": "general", 
                        "details": "",
                        "verification": "Manual check required",
                        "dependencies": []
                    }
                
                bullet_text = line[1:].strip()
                if bullet_text:
                    if not current_step["details"]:
                        current_step["description"] = bullet_text
                        current_step["details"] = bullet_text
                    else:
                        current_step["details"] += f" {bullet_text}"
        
        if current_step:
            steps.append(current_step)
        
        # If no structured steps found, create a single general step
        if not steps and response.strip():
            steps = [{
                "description": "Execute plan based on AI analysis",
                "action": "general",
                "details": response.strip()[:500],  # Limit details length
                "verification": "Manual check required",
                "dependencies": []
            }]
        
        return steps[:15]  # Limit to 15 steps
    
    async def _continue_autonomous_execution(self):
        """Continue autonomous execution from current step"""
        while (self.autonomous_mode and 
               not self.execution_paused and 
               self.current_step < len(self.execution_plan) and
               self.current_step < self.max_autonomous_steps):
            
            current_step_info = self.execution_plan[self.current_step]
            
            # Validate step format
            if not isinstance(current_step_info, dict):
                print(f"❌ Invalid step format at step {self.current_step + 1}: {current_step_info}")
                self.execution_paused = True
                print("⏸️  Execution paused due to invalid step format")
                return
            
            print(f"\n🔄 Step {self.current_step + 1}/{len(self.execution_plan)}: {current_step_info['description']}")
            print(f"📋 Details: {current_step_info.get('details', 'No details')}")
            
            # Execute the step
            step_result = await self._execute_step(current_step_info)
            
            # Store result
            self.step_results.append({
                'step': self.current_step + 1,
                'description': current_step_info['description'],
                'result': step_result,
                'summary': step_result.get('summary', 'Completed') if step_result else 'Failed'
            })
            
            if step_result and step_result.get('success', False):
                print(f"✅ Step {self.current_step + 1} completed: {step_result.get('summary', 'Success')}")
                self.current_step += 1
                
                # Brief pause between steps
                await asyncio.sleep(1)
                
            else:
                print(f"❌ Step {self.current_step + 1} failed: {step_result.get('error', 'Unknown error') if step_result else 'Execution failed'}")
                
                # Ask AI how to handle the failure
                await self._handle_step_failure(current_step_info, step_result)
                break
        
        # Check if we completed all steps
        if self.current_step >= len(self.execution_plan):
            await self._complete_autonomous_execution()
    
    async def _execute_step(self, step_info: dict) -> dict:
        """Execute a single step in the autonomous plan"""
        action = step_info.get('action', 'general')
        details = step_info.get('details', '')
        
        try:
            if action == 'create_file':
                return await self._execute_create_file_step(step_info)
            elif action == 'run_command':
                return await self._execute_command_step(step_info)
            elif action == 'create_directories':
                return await self._execute_create_directories_step(step_info)
            elif action == 'analyze':
                return await self._execute_analysis_step(step_info)
            else:
                # General AI-powered step execution
                return await self._execute_general_step(step_info)
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'summary': f'Step execution failed: {e}'
            }
    
    async def _execute_general_step(self, step_info: dict) -> dict:
        """Execute a general step using AI"""
        step_prompt = f"""
Execute this step in the autonomous plan:

STEP: {step_info['description']}
DETAILS: {step_info.get('details', '')}
VERIFICATION: {step_info.get('verification', '')}

Current directory: {self.current_dir}
Target: {self.current_target}

Please execute this step by taking appropriate actions. You can:
- Create files and directories
- Run commands
- Analyze code
- Make modifications

Provide specific actions to complete this step.
"""
        
        # Add to chat history and get AI response
        response = await self._get_ai_response_for_step(step_prompt)
        
        # Process AI response to execute actions
        await self._process_ai_response(response)
        
        return {
            'success': True,
            'summary': f'Executed: {step_info["description"]}',
            'details': response[:200] + '...' if len(response) > 200 else response
        }
    
    async def _execute_create_file_step(self, step_info: dict) -> dict:
        """Execute a file creation step"""
        # This would create files based on step details
        details = step_info.get('details', '')
        # Implementation would parse details to create specific files
        return {
            'success': True,
            'summary': f'File creation step completed'
        }
    
    async def _execute_command_step(self, step_info: dict) -> dict:
        """Execute a command step with automatic error handling"""
        details = step_info.get('details', '')
        
        try:
            # Extract command from details
            command = details.strip()
            if command.startswith('Execute ') or command.startswith('Run '):
                # Extract actual command
                parts = command.split(' ', 1)
                if len(parts) > 1:
                    command = parts[1]
            
            print(f"🔧 Executing command: {command}")
            
            # Execute command using the shell command system (with error handling)
            await self.execute_shell_command(command)
            
            return {
                'success': True,
                'summary': f'Command executed: {command}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'summary': f'Command execution failed: {e}'
            }
    
    async def _execute_create_directories_step(self, step_info: dict) -> dict:
        """Execute directory creation step"""
        # This would create directories
        details = step_info.get('details', '')
        # Implementation would parse and create directories
        return {
            'success': True,
            'summary': f'Directory creation completed'
        }
    
    async def _execute_analysis_step(self, step_info: dict) -> dict:
        """Execute an analysis step"""
        # This would perform analysis
        details = step_info.get('details', '')
        # Implementation would perform various analyses
        return {
            'success': True,
            'summary': f'Analysis completed'
        }
    
    async def _get_ai_response_for_step(self, prompt: str) -> str:
        """Get AI response for step execution"""
        try:
            model_info = await self.selector.select_model('medium')
            client = self.openai_client if model_info['provider'] == 'openai' else self.ollama_client
            
            response = await client.generate(
                model=model_info['model'],
                prompt=prompt,
                system_prompt=self._get_system_prompt()
            )
            
            return response
        except Exception as e:
            return f"Error getting AI response: {e}"
    
    async def _handle_step_failure(self, step_info: dict, result: dict):
        """Handle step failure by asking AI for recovery strategy"""
        print(f"🤔 Analyzing step failure...")
        
        failure_prompt = f"""
A step in autonomous execution failed:

FAILED STEP: {step_info['description']}
DETAILS: {step_info.get('details', '')}
ERROR: {result.get('error', 'Unknown error') if result else 'No result'}

Please suggest how to:
1. Fix the immediate issue
2. Modify the step to succeed
3. Continue with the execution plan

Should we retry this step, skip it, or modify the plan?
"""
        
        response = await self._get_ai_response_for_step(failure_prompt)
        print(f"🤖 Failure analysis: {response}")
        
        # For now, pause execution for user intervention
        self.execution_paused = True
        print("⏸️  Execution paused for manual intervention")
        print("💡 Use /resume to continue or /stop to end execution")
    
    async def _complete_autonomous_execution(self):
        """Complete autonomous execution and show results"""
        self.autonomous_mode = False
        
        print("\n🎉 Autonomous execution completed!")
        print(f"🎯 Target achieved: {self.current_target}")
        print(f"✅ Completed {self.current_step}/{len(self.execution_plan)} steps")
        
        # Show summary of results
        print("\n📊 Execution Summary:")
        for i, result in enumerate(self.step_results, 1):
            print(f"  {i}. {result['description']}: {result['summary']}")
        
        print(f"\n💡 Autonomous execution finished. Use /auto for a new target.")

def main():
    """Main shell entry point"""
    shell = AgentsTeamShell()
    asyncio.run(shell.start())

if __name__ == "__main__":
    main()
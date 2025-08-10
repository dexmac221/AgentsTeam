#!/usr/bin/env python3
"""
AgentsTeam CLI - Simple code generation without Docker complexity
Automatically scales from local Ollama to OpenAI based on task complexity
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from .core.model_selector import ModelSelector
from .core.code_generator import CodeGenerator
from .core.project_analyzer import ProjectAnalyzer
from .utils.config import Config
from .utils.logger import setup_logger

def main():
    parser = argparse.ArgumentParser(
        description="AgentsTeam CLI - AI-powered code generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive shell (recommended)
  agentsteam shell
  
  # Direct generation
  agentsteam generate "Simple REST API for blog posts"
  agentsteam generate "Tetris game with pygame" --tech python,pygame
  
  # Complex project (auto-scales to OpenAI)  
  agentsteam generate "Microservices platform" --model openai:gpt-4
        """)
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Shell command (interactive mode)
    shell_parser = subparsers.add_parser('shell', help='Start interactive shell')
    
    # Generate command
    gen_parser = subparsers.add_parser('generate', help='Generate code for a project')
    gen_parser.add_argument('description', help='Project description')
    gen_parser.add_argument('--tech', help='Technologies (comma-separated)', default='')
    gen_parser.add_argument('--model', help='Force specific model (ollama:gemma2, openai:gpt-4)')
    gen_parser.add_argument('--output', '-o', help='Output directory', default='./generated')
    gen_parser.add_argument('--complexity', choices=['simple', 'medium', 'complex'], help='Force complexity level')
    
    # Try-error incremental build command
    try_parser = subparsers.add_parser('try-error', help='Incremental try/error guided project build')
    try_parser.add_argument('description', help='Project description / goal')
    try_parser.add_argument('--tech', help='Technologies (comma-separated)', default='')
    try_parser.add_argument('--model', help='Force specific model (ollama:..., openai:...)')
    try_parser.add_argument('--output', '-o', help='Output directory', default='./generated_try')
    try_parser.add_argument('--run-cmd', help='Run command executed each iteration (auto-infer if omitted)')
    try_parser.add_argument('--max-steps', type=int, default=10, help='Maximum incremental build steps (global cap)')
    try_parser.add_argument('--epics', type=int, default=0, help='Number of high-level epics to decompose before generating steps (0=disabled)')
    try_parser.add_argument('--epic-steps', type=int, default=0, help='Max steps per epic (0=auto distribute)')
    try_parser.add_argument('--expect', help='Expected substring in stdout or HTTP probe response (treat absence as error)')
    try_parser.add_argument('--probe', help='HTTP probe spec path[:contains=TEXT] for server apps (e.g. /health:contains=ok)')
    try_parser.add_argument('--plan-only', action='store_true', help='Only produce and print the incremental plan (no execution)')
    try_parser.add_argument('--dynamic-run', dest='dynamic_run', action='store_true', help='Dynamically re-infer run command when project gains tests')
    try_parser.add_argument('--no-dynamic-run', dest='dynamic_run', action='store_false', help='Disable dynamic run command switching')
    try_parser.set_defaults(dynamic_run=True)
    try_parser.add_argument('--debug', action='store_true', help='Verbose debug output')
    try_parser.add_argument('--resume', action='store_true', help='Resume from previous state in output directory if available')
    try_parser.add_argument('--fix-attempts', type=int, default=3, help='Maximum automated fix attempts per failing step')
    
    # List models command
    list_parser = subparsers.add_parser('models', help='List available models')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configure API keys and settings')
    config_parser.add_argument('--openai-key', help='Set OpenAI API key')
    config_parser.add_argument('--ollama-url', help='Set Ollama base URL (e.g., http://192.168.1.62:11434)')
    config_parser.add_argument('--ollama-hosts', help='Comma-separated Ollama hosts to scan (e.g., http://192.168.1.62:11434,http://localhost:11434)')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    
    # Fix command (intelligent error correction)
    fix_parser = subparsers.add_parser('fix', help='Automatically fix errors in code')
    fix_parser.add_argument('target', nargs='?', help='File to fix or command to run and fix')
    fix_parser.add_argument('--file', '-f', help='Specific file to analyze and fix')
    fix_parser.add_argument('--run-command', '-c', dest='run_command', help='Command to run and auto-fix errors')
    fix_parser.add_argument('--error', '-e', help='Specific error message to address')
    fix_parser.add_argument('--max-attempts', type=int, default=3, help='Maximum fix attempts')
    fix_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize configuration and logger
    config = Config()
    logger = setup_logger()
    
    if args.command == 'shell':
        from .shell import main as shell_main
        shell_main()
    elif args.command == 'config':
        handle_config(args, config)
    elif args.command == 'models':
        asyncio.run(handle_models(config, logger))
    elif args.command == 'generate':
        asyncio.run(handle_generate(args, config, logger))
    elif args.command == 'try-error':
        asyncio.run(handle_try_error(args, config, logger))
    elif args.command == 'fix':
        asyncio.run(handle_fix(args, config, logger))

def handle_config(args, config):
    """Handle configuration commands"""
    if args.openai_key:
        config.set('openai.api_key', args.openai_key)
        print("✅ OpenAI API key configured")
    
    if args.ollama_url:
        config.set('ollama.base_url', args.ollama_url)
        print(f"✅ Ollama base URL set to {args.ollama_url}")
    
    if args.ollama_hosts:
        config.set('ollama.hosts', args.ollama_hosts)
        print(f"✅ Ollama hosts set to {args.ollama_hosts}")
    
    if args.show:
        print("\n🔧 Current Configuration:")
        print(f"OpenAI API Key: {'configured' if config.get('openai.api_key') else 'not configured'}")
        print(f"Ollama URL: {config.get('ollama.base_url', 'http://localhost:11434')}")
        print(f"Ollama Hosts: {config.get('ollama.hosts', '(not set; using Ollama URL)')}")

async def handle_models(config, logger):
    """List available models"""
    selector = ModelSelector(config, logger)
    
    print("\n🤖 Available Models:")
    
    # Check Ollama models across configured hosts
    any_ollama = False
    for host in selector.ollama_hosts:
        ollama_models = await selector.get_ollama_models(base_url=host)
        host_label = host.replace('http://', '').replace('https://', '')
        if ollama_models:
            any_ollama = True
            print(f"\n📍 Local (Ollama) at {host_label}:")
            for model in ollama_models:
                print(f"  • {model}")
        else:
            print(f"\n⚠️ No models found at Ollama host {host_label}")
    if not any_ollama:
        print("\n❌ Ollama not available (install: curl -fsSL https://ollama.com/install.sh | sh)")
    
    # Check OpenAI (align with selector choices)
    if config.get('openai.api_key'):
        print("\n☁️ OpenAI:")
        print("  • gpt-4o")
        print("  • gpt-4o-mini")
    else:
        print("\n❌ OpenAI not configured (run: agentsteam config --openai-key YOUR_KEY)")

async def handle_generate(args, config, logger):
    """Handle code generation"""
    print(f"🚀 Generating: {args.description}")
    
    # Initialize components
    analyzer = ProjectAnalyzer(logger)
    selector = ModelSelector(config, logger)
    generator = CodeGenerator(config, logger)
    
    # Analyze project complexity
    if args.complexity:
        complexity = args.complexity
        print(f"🎯 Using forced complexity: {complexity}")
    else:
        complexity = analyzer.analyze_complexity(
            args.description, 
            args.tech.split(',') if args.tech else []
        )
        print(f"🔍 Detected complexity: {complexity}")
    
    # Select appropriate model
    if args.model:
        model_info = selector.parse_model_string(args.model)
        print(f"🎯 Using forced model: {model_info['provider']}:{model_info['model']}")
    else:
        model_info = await selector.select_model(complexity)
        print(f"🤖 Selected model: {model_info['provider']}:{model_info['model']}")
    
    # Generate code
    try:
        result = await generator.generate_project(
            description=args.description,
            technologies=args.tech.split(',') if args.tech else [],
            model_info=model_info,
            output_dir=Path(args.output)
        )
        
        if result['success']:
            print(f"\n✅ Code generated successfully!")
            print(f"📁 Output directory: {result['output_dir']}")
            print(f"📊 Files created: {result['files_created']}")
            print(f"⏱️ Generation time: {result['generation_time']:.1f}s")
            
            if result.get('instructions'):
                print(f"\n📋 Next steps:")
                for instruction in result['instructions']:
                    print(f"  • {instruction}")
        else:
            print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Generation error: {e}")
        print(f"❌ Error: {e}")
        sys.exit(1)

async def handle_try_error(args, config, logger):
    """Handle incremental try-error build using orchestrator."""
    print(f"🧪 Try/Error Incremental Build: {args.description}")
    from .core.model_selector import ModelSelector
    from .core.project_analyzer import ProjectAnalyzer
    from .core.try_error_orchestrator import TryErrorOrchestrator
    from .clients.ollama_client import OllamaClient
    from .clients.openai_client import OpenAIClient

    selector = ModelSelector(config, logger)
    analyzer = ProjectAnalyzer(logger)

    # Select model
    if args.model:
        model_info = selector.parse_model_string(args.model)
        print(f"🎯 Using forced model: {model_info['provider']}:{model_info['model']}")
    else:
        complexity = analyzer.analyze_complexity(args.description, args.tech.split(',') if args.tech else [])
        model_info = await selector.select_model(complexity)
        print(f"🤖 Selected model: {model_info['provider']}:{model_info['model']}")

    # Init AI client
    if model_info['provider'] == 'ollama':
        from .clients.ollama_client import OllamaClient as OC
        ai_client = OC(config, logger, base_url=model_info.get('base_url'))
    else:
        from .clients.openai_client import OpenAIClient as OPC
        ai_client = OPC(config, logger)

    orchestrator = TryErrorOrchestrator(ai_client, logger, model=model_info['model'])
    orchestrator.max_fix_attempts = args.fix_attempts
    technologies = args.tech.split(',') if args.tech else []

    if args.plan_only:
        steps = await orchestrator.plan_steps(args.description, technologies, args.max_steps) if args.epics == 0 else await orchestrator.plan_hierarchical(args.description, technologies, args.epics, args.epic_steps, args.max_steps)
        print("🗂️ Plan steps:")
        for i, s in enumerate(steps, 1):
            print(f"  {i}. {s}")
        print("(plan-only requested; stopping before iterations)")
        return

    await orchestrator.run(
        description=args.description,
        technologies=technologies,
        output_dir=Path(args.output),
        run_cmd=args.run_cmd,
        max_steps=args.max_steps,
        expect=args.expect,
        dynamic_run=args.dynamic_run,
        resume=args.resume,
        probe=args.probe,
        epics=args.epics,
        epic_steps=args.epic_steps
    )
    
async def handle_fix(args, config, logger):
    """Handle intelligent error correction"""
    from .core.error_corrector import ErrorCorrector
    from .clients.ollama_client import OllamaClient
    from .clients.openai_client import OpenAIClient
    
    print("🔧 AgentsTeam Intelligent Error Correction")
    
    # Initialize model selector and get a solid model for debugging/fixing
    selector = ModelSelector(config, logger)
    try:
        model_info = await selector.select_model('complex')
    except Exception as e:
        print(f"❌ No AI models available. {e}")
        return
    
    if not model_info:
        print("❌ No AI models available. Please configure Ollama or OpenAI.")
        return
    
    print(f"🤖 Using model: {model_info['provider']}:{model_info['model']}")
    
    # Initialize AI client (honor base_url if using Ollama)
    if model_info['provider'] == 'ollama':
        ai_client = OllamaClient(config, logger, base_url=model_info.get('base_url'))
    else:
        ai_client = OpenAIClient(config, logger)
    
    # Initialize error corrector with selected model
    corrector = ErrorCorrector(ai_client, logger, model=model_info['model'])
    
    try:
        # Determine what to fix
        if args.run_command:
            # Run command and fix errors
            print(f"🚀 Running command with auto-fix: {args.run_command}")
            result = await corrector.run_and_fix(args.run_command, args.max_attempts)
            
            if result['success']:
                print(f"✅ Command completed successfully after {result['attempts']} attempt(s)")
                if result.get('fixes_applied'):
                    print(f"🔧 Fixed files: {', '.join(result['fixes_applied'])}")
                print(f"\n📄 Output:\n{result['output']}")
            else:
                print(f"❌ Command failed: {result.get('reason', 'Unknown reason')}")
                if result.get('fixes_attempted'):
                    print(f"🔧 Attempted fixes on: {', '.join(result['fixes_attempted'])}")
                print(f"\n📄 Error:\n{result.get('error','')}")
                
        elif args.file or args.target:
            # Fix specific file
            file_to_fix = args.file or args.target
            print(f"🔍 Analyzing file: {file_to_fix}")
            
            result = await corrector.fix_file_errors(file_to_fix, args.error)
            
            if result['success']:
                print(f"✅ File fixed successfully!")
                print(f"📁 Fixed file: {result['file']}")
                print(f"💾 Backup created: {result['backup']}")
                print(f"🔧 Changes made: {result['changes']}")
                
                if args.debug:
                    print(f"\n📄 Fixed code:\n{result['fixed_code']}")
            else:
                print(f"❌ Could not fix file: {result.get('error','Unknown error')}")
                
        else:
            print("🔍 Scanning current directory for issues...")
            
            current_dir = Path('.')
            ignored_dirs = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'dist', 'build', '.mypy_cache', '.pytest_cache', '.idea', '.vscode'}
            
            def is_ignored(path: Path) -> bool:
                return any(part in ignored_dirs for part in path.parts)
            
            # Recursive Python scan with a safety cap
            python_files = [p for p in current_dir.rglob('*.py') if not is_ignored(p)]
            max_files = 200
            if len(python_files) > max_files:
                print(f"Found {len(python_files)} Python files; limiting to first {max_files} to avoid long scans.")
                python_files = python_files[:max_files]
            
            if python_files:
                print(f"Found {len(python_files)} Python files. Checking for issues...")
                
                for py_file in python_files:
                    print(f"\n🔍 Checking {py_file}...")
                    try:
                        process = await asyncio.create_subprocess_exec(
                            'python', '-m', 'py_compile', str(py_file),
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        stdout, stderr = await process.communicate()
                        
                        if process.returncode != 0:
                            print(f"❌ Syntax error detected in {py_file}")
                            result = await corrector.fix_file_errors(str(py_file), stderr.decode())
                            
                            if result['success']:
                                print(f"✅ Fixed {py_file}")
                                print(f"🔧 Changes: {result['changes']}")
                            else:
                                print(f"❌ Could not fix {py_file}: {result.get('error','Unknown error')}")
                        else:
                            print(f"✅ {py_file} looks good")
                            
                    except Exception as e:
                        print(f"⚠️ Could not check {py_file}: {e}")
            else:
                print("No Python files found.")
                print("\nUsage examples:")
                print("  agentsteam fix --file main.py")
                print("  agentsteam fix --run-command 'python main.py'")
                print("  agentsteam fix 'python main.py'")
                
    except Exception as e:
        logger.error(f"Fix command error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
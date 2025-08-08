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
    
    # List models command
    list_parser = subparsers.add_parser('models', help='List available models')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configure API keys and settings')
    config_parser.add_argument('--openai-key', help='Set OpenAI API key')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    
    # Fix command (intelligent error correction)
    fix_parser = subparsers.add_parser('fix', help='Automatically fix errors in code')
    fix_parser.add_argument('target', nargs='?', help='File to fix or command to run and fix')
    fix_parser.add_argument('--file', '-f', help='Specific file to analyze and fix')
    fix_parser.add_argument('--command', '-c', help='Command to run and auto-fix errors')
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
    elif args.command == 'fix':
        asyncio.run(handle_fix(args, config, logger))

def handle_config(args, config):
    """Handle configuration commands"""
    if args.openai_key:
        config.set('openai.api_key', args.openai_key)
        print("✅ OpenAI API key configured")
    
    if args.show:
        print("\n🔧 Current Configuration:")
        print(f"OpenAI API Key: {'configured' if config.get('openai.api_key') else 'not configured'}")
        print(f"Ollama URL: {config.get('ollama.base_url', 'http://localhost:11434')}")

async def handle_models(config, logger):
    """List available models"""
    selector = ModelSelector(config, logger)
    
    print("\n🤖 Available Models:")
    
    # Check Ollama models
    ollama_models = await selector.get_ollama_models()
    if ollama_models:
        print("\n📍 Local (Ollama):")
        for model in ollama_models:
            print(f"  • {model}")
    else:
        print("\n❌ Ollama not available (install: curl -fsSL https://ollama.com/install.sh | sh)")
    
    # Check OpenAI
    if config.get('openai.api_key'):
        print("\n☁️ OpenAI:")
        print("  • gpt-4o")
        print("  • gpt-4o-mini")
        print("  • gpt-3.5-turbo")
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

async def handle_fix(args, config, logger):
    """Handle intelligent error correction"""
    from .core.error_corrector import ErrorCorrector
    from .core.model_selector import ModelSelector
    from .clients.ollama_client import OllamaClient
    from .clients.openai_client import OpenAIClient
    
    print("🔧 AgentsTeam Intelligent Error Correction")
    
    # Initialize model selector and get best available model
    selector = ModelSelector(config, logger)
    model_info = await selector.get_best_model()
    
    if not model_info:
        print("❌ No AI models available. Please configure Ollama or OpenAI.")
        return
    
    print(f"🤖 Using model: {model_info['provider']}:{model_info['name']}")
    
    # Initialize AI client
    if model_info['provider'] == 'ollama':
        ai_client = OllamaClient(
            base_url=config.get('ollama.base_url', 'http://localhost:11434'),
            logger=logger
        )
    else:
        ai_client = OpenAIClient(
            api_key=config.get('openai.api_key'),
            logger=logger
        )
    
    # Initialize error corrector
    corrector = ErrorCorrector(ai_client, logger)
    
    try:
        # Determine what to fix
        if args.command:
            # Run command and fix errors
            print(f"🚀 Running command with auto-fix: {args.command}")
            result = await corrector.run_and_fix(args.command, args.max_attempts)
            
            if result['success']:
                print(f"✅ Command completed successfully after {result['attempts']} attempt(s)")
                if result.get('fixes_applied'):
                    print(f"🔧 Fixed files: {', '.join(result['fixes_applied'])}")
                print(f"\n📄 Output:\n{result['output']}")
            else:
                print(f"❌ Command failed: {result['reason']}")
                if result.get('fixes_attempted'):
                    print(f"🔧 Attempted fixes on: {', '.join(result['fixes_attempted'])}")
                print(f"\n📄 Error:\n{result['error']}")
                
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
                print(f"❌ Could not fix file: {result['error']}")
                
        else:
            print("🔍 Scanning current directory for issues...")
            
            # Look for Python files with errors
            import os
            from pathlib import Path
            
            current_dir = Path('.')
            python_files = list(current_dir.glob('*.py'))
            
            if python_files:
                print(f"Found {len(python_files)} Python files. Checking for issues...")
                
                for py_file in python_files:
                    print(f"\n🔍 Checking {py_file}...")
                    
                    # Try to run a basic syntax check
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
                                print(f"❌ Could not fix {py_file}: {result['error']}")
                        else:
                            print(f"✅ {py_file} looks good")
                            
                    except Exception as e:
                        print(f"⚠️ Could not check {py_file}: {e}")
            else:
                print("No Python files found in current directory.")
                print("\nUsage examples:")
                print("  agentsteam fix --file main.py")
                print("  agentsteam fix --command 'python main.py'")
                print("  agentsteam fix 'python main.py'")
                
    except Exception as e:
        logger.error(f"Fix command error: {e}")
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
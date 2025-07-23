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

if __name__ == "__main__":
    main()
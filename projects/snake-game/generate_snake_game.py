#!/usr/bin/env python3
"""
Snake Game Project Generator using gpt-oss:20b model
This script will create a complete Python Snake game with pygame
"""

import asyncio
import sys
import os
from pathlib import Path

# Add AgentsTeam to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from cli.clients.ollama_client import OllamaClient
from cli.utils.config import Config
from cli.utils.logger import setup_logger

class SnakeGameGenerator:
    def __init__(self):
        self.config = Config()
        self.config.set('ollama.base_url', 'http://192.168.1.62:11434')
        self.logger = setup_logger()
        self.client = OllamaClient(self.config, self.logger)
        
    async def generate_clean_code(self, model: str, filename: str, description: str, 
                                 language: str, additional_requirements: str = "") -> str:
        """Generate clean code file without explanatory text"""
        
        system_prompt = f"""You are an expert {language} game developer. Generate ONLY clean, executable {language} code.

STRICT RULES:
- Output ONLY the raw {language} code
- NO explanations, descriptions, or markdown formatting
- NO ```code``` blocks or any formatting
- NO tables, feature lists, or documentation outside code
- Start directly with code (imports, class definitions, etc.)
- Include comments INSIDE the code using {language} comment syntax
- Make code complete, production-ready, and well-structured
- Follow {language} best practices and gaming conventions"""

        user_prompt = f"""Create the file: {filename}

Description: {description}

Requirements:
- Clean, well-structured {language} code
- Include all necessary imports and dependencies  
- Add clear comments using {language} comment syntax
- Follow {language} and game development best practices
- Make code complete and ready to run
{additional_requirements}

GENERATE ONLY THE RAW {language.upper()} CODE - NO OTHER TEXT:"""

        response = await self.client.generate(model, user_prompt, system_prompt)
        
        # Clean the response aggressively
        cleaned = self.clean_code_response(response)
        return cleaned
    
    def clean_code_response(self, response: str) -> str:
        """Aggressively clean the response to get only code"""
        lines = response.split('\n')
        cleaned_lines = []
        skip_patterns = [
            'below is', 'here is', 'here\'s', 'this is', 'this file', 'this code',
            'the following', 'above code', 'explanation:', 'description:',
            'note:', 'important:', 'features:', 'requirements:', 'usage:',
            '| feature |', '|---------|', 'implementation |', 'how to',
            'example:', 'install:', 'run:', 'start:', 'game features',
            'this snake', 'the game', 'controls:', 'gameplay:'
        ]
        
        in_code = False
        for line in lines:
            line_lower = line.lower().strip()
            
            # Skip obvious explanatory text
            if any(pattern in line_lower for pattern in skip_patterns):
                continue
                
            # Skip markdown formatting
            if line.strip().startswith('#') and not line.strip().startswith('#!/'):
                continue
            if line.strip().startswith('```'):
                continue
            if line.strip().startswith('|') and '|' in line[1:]:
                continue
            if line.strip().startswith('*') and not line.strip().startswith('*'):
                continue
                
            # Detect start of actual code
            if not in_code:
                if (line.strip().startswith('import ') or 
                    line.strip().startswith('from ') or
                    line.strip().startswith('#!/') or
                    line.strip().startswith('def ') or
                    line.strip().startswith('class ') or
                    line.strip().startswith('"""') or
                    line.strip().startswith("'''") or
                    (line.strip() and any(char in line for char in ['=', ':', '{', '}', '(', ')']))):
                    in_code = True
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Remove trailing explanatory text
        result_lines = result.split('\n')
        for i in range(len(result_lines) - 1, -1, -1):
            line_lower = result_lines[i].lower()
            if any(pattern in line_lower for pattern in ['this game', 'to play', 'controls', 'enjoy']):
                result = '\n'.join(result_lines[:i]).strip()
                break
        
        return result

async def generate_snake_game():
    """Generate the complete Snake game project"""
    
    generator = SnakeGameGenerator()
    
    # Check if gpt-oss:20b is available
    model = "gpt-oss:20b"
    is_available = await generator.client.check_model_available(model)
    if not is_available:
        print(f"❌ Model {model} not available. Trying gpt-oss:latest...")
        model = "gpt-oss:latest"
        is_available = await generator.client.check_model_available(model)
        if not is_available:
            print("❌ No gpt-oss model available!")
            return
    
    print(f"✅ Using model: {model}")
    
    try:
        # 1. Generate main Snake game
        print("🐍 Generating snake_game.py...")
        snake_code = await generator.generate_clean_code(
            model=model,
            filename="snake_game.py",
            description="Complete Snake game implementation using pygame with score, collision detection, and game over",
            language="Python",
            additional_requirements="""
- Use pygame for graphics and input handling
- Include Snake class for the snake entity
- Include Food class for food generation
- Include Game class for game logic and main loop
- Add score tracking and display
- Implement collision detection (walls and self)
- Add game over screen
- Include keyboard controls (arrow keys or WASD)
- Use proper game loop with FPS control
- Add colors and basic graphics
- Make game window resizable
- Include pause functionality"""
        )
        
        with open("snake_game.py", "w") as f:
            f.write(snake_code)
        print("✅ Generated snake_game.py")
        
        # 2. Generate game settings/config
        print("⚙️ Generating config.py...")
        config_code = await generator.generate_clean_code(
            model=model,
            filename="config.py",
            description="Configuration file with game settings, colors, and constants",
            language="Python",
            additional_requirements="""
- Define screen dimensions (WIDTH, HEIGHT)
- Define FPS constant
- Define color constants (RGB tuples)
- Define grid size and snake segment size
- Define initial snake speed
- Define score increment
- Include font settings
- Add any other game configuration constants"""
        )
        
        with open("config.py", "w") as f:
            f.write(config_code)
        print("✅ Generated config.py")
        
        # 3. Generate main entry point
        print("🚀 Generating main.py...")
        main_code = await generator.generate_clean_code(
            model=model,
            filename="main.py",
            description="Main entry point script to run the Snake game",
            language="Python",
            additional_requirements="""
- Import the Snake game from snake_game module
- Initialize pygame
- Create game instance
- Handle command line arguments if needed
- Add exception handling
- Include if __name__ == '__main__' guard
- Start the game loop"""
        )
        
        with open("main.py", "w") as f:
            f.write(main_code)
        print("✅ Generated main.py")
        
        # 4. Generate requirements.txt
        print("📦 Generating requirements.txt...")
        requirements_code = await generator.generate_clean_code(
            model=model,
            filename="requirements.txt",
            description="Python dependencies for the Snake game",
            language="text",
            additional_requirements="""
- Include pygame for game development
- Include any other necessary dependencies
- Use specific versions for stability
- Keep it minimal and clean"""
        )
        
        with open("requirements.txt", "w") as f:
            f.write(requirements_code)
        print("✅ Generated requirements.txt")
        
        # 5. Generate README.md
        print("📚 Generating README.md...")
        readme_code = await generator.generate_clean_code(
            model=model,
            filename="README.md",
            description="README documentation for the Snake game project",
            language="Markdown",
            additional_requirements="""
- Include project title and description
- Add installation instructions
- Include how to play/controls
- Add game features list
- Include requirements and setup
- Add screenshots section (placeholder)
- Include development/contribution info
- Add license information"""
        )
        
        with open("README.md", "w") as f:
            f.write(readme_code)
        print("✅ Generated README.md")
        
        # 6. Generate setup script
        print("🔧 Generating setup.py...")
        setup_code = await generator.generate_clean_code(
            model=model,
            filename="setup.py",
            description="Setup script for the Snake game project",
            language="Python",
            additional_requirements="""
- Use setuptools for package configuration
- Include project metadata (name, version, author, description)
- Define entry points for the game
- Include install_requires with dependencies
- Add classifiers for Python versions
- Include long description from README
- Make it pip installable"""
        )
        
        with open("setup.py", "w") as f:
            f.write(setup_code)
        print("✅ Generated setup.py")
        
        # 7. Generate utilities module
        print("🛠️ Generating utils.py...")
        utils_code = await generator.generate_clean_code(
            model=model,
            filename="utils.py",
            description="Utility functions for the Snake game",
            language="Python",
            additional_requirements="""
- Include helper functions for game operations
- Add function to check collisions
- Include function to generate random food position
- Add function to calculate score
- Include any common utility functions
- Add input validation functions
- Include game state management helpers"""
        )
        
        with open("utils.py", "w") as f:
            f.write(utils_code)
        print("✅ Generated utils.py")
        
        print("\n🎉 Snake Game project generated successfully!")
        print(f"✅ Generated using model: {model}")
        print("\nGenerated files:")
        print("  🐍 snake_game.py - Main game implementation")
        print("  ⚙️ config.py - Game configuration and constants")
        print("  🚀 main.py - Entry point script")
        print("  📦 requirements.txt - Dependencies")
        print("  📚 README.md - Documentation")
        print("  🔧 setup.py - Package setup")
        print("  🛠️ utils.py - Utility functions")
        
        print("\nNext steps:")
        print("1. pip install -r requirements.txt")
        print("2. python main.py")
        print("3. Enjoy the Snake game!")
        
    except Exception as e:
        print(f"❌ Error generating Snake game: {e}")

if __name__ == "__main__":
    asyncio.run(generate_snake_game())

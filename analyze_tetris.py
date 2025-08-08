#!/usr/bin/env python3
"""
Use AgentsTeam to analyze and improve the Tetris game
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from cli.shell import AgentsTeamShell

async def analyze_tetris():
    """Analyze the Tetris game using AgentsTeam"""
    
    shell = AgentsTeamShell()
    shell.current_dir = Path("/home/dexmac/Working/AgentsTeam/projects/tetris")
    
    # Read the tetris files
    main_py = (shell.current_dir / "main.py").read_text()
    tetris_py = (shell.current_dir / "tetris.py").read_text()
    pieces_py = (shell.current_dir / "pieces.py").read_text()
    
    analysis_prompt = f"""Analyze this Tetris game implementation and suggest improvements:

MAIN.PY:
{main_py}

TETRIS.PY:
{tetris_py}

PIECES.PY:
{pieces_py}

Please analyze the code and identify:
1. Any bugs or issues
2. Missing features that a complete Tetris game should have
3. Performance improvements
4. Code quality improvements
5. Game mechanics that could be enhanced

Provide specific suggestions for improvements."""

    print("🔍 Analyzing Tetris game with AgentsTeam...")
    await shell.chat_with_ai(analysis_prompt)

if __name__ == "__main__":
    asyncio.run(analyze_tetris())

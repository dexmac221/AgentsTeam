#!/usr/bin/env python3
"""
Intelligent Error Correction System for AgentsTeam

This module provides automatic error detection and correction capabilities
for various programming languages and runtime environments.
"""

import asyncio
import os
import re
import subprocess
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json

class ErrorCorrector:
    """
    Intelligent error correction system that can:
    1. Detect errors in code execution
    2. Read and analyze source code 
    3. Use AI to understand and fix errors
    4. Apply corrections automatically with backups
    """
    
    def __init__(self, ai_client, logger, model: Optional[str] = None):
        """
        Initialize the error corrector.
        
        Args:
            ai_client: AI client (Ollama or OpenAI) for generating fixes
            logger: Logger instance for debugging and monitoring
            model: Optional model identifier to use for AI generation
        """
        self.ai_client = ai_client
        self.logger = logger
        self.model = model
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.c': 'c',
            '.cpp': 'cpp',
            '.java': 'java',
            '.rs': 'rust',
            '.go': 'go'
        }
        
    async def run_and_fix(self, command: str, max_attempts: int = 3) -> Dict:
        """
        Run a command and automatically fix any errors that occur.
        
        Args:
            command: Command to execute
            max_attempts: Maximum number of fix attempts
            
        Returns:
            Dict with success status, output, and fix details
        """
        attempt = 0
        original_files = {}
        
        while attempt < max_attempts:
            attempt += 1
            self.logger.info(f"Attempt {attempt}: Running command: {command}")
            
            # Run the command
            result = await self._run_command(command)
            
            if result['success']:
                return {
                    'success': True,
                    'output': result['output'],
                    'attempts': attempt,
                    'fixes_applied': list(original_files.keys()) if original_files else []
                }
            
            # Extract error information
            error_info = self._analyze_error(result['stderr'], command)
            
            if not error_info['fixable']:
                return {
                    'success': False,
                    'error': result['stderr'],
                    'reason': 'Error not automatically fixable',
                    'attempts': attempt
                }
            
            # Try to fix the error
            fix_result = await self._fix_error(error_info, original_files)
            
            if not fix_result['success']:
                return {
                    'success': False,
                    'error': result['stderr'],
                    'reason': f"Could not generate fix: {fix_result['error']}",
                    'attempts': attempt
                }
                
            self.logger.info(f"Applied fix to {fix_result['file']}, retrying...")
        
        return {
            'success': False,
            'error': result['stderr'],
            'reason': f'Max attempts ({max_attempts}) exceeded',
            'attempts': attempt,
            'fixes_attempted': list(original_files.keys())
        }
    
    async def fix_file_errors(self, file_path: str, error_message: str = None) -> Dict:
        """
        Analyze a file and fix any errors found.
        
        Args:
            file_path: Path to the file to fix
            error_message: Optional specific error message to address
            
        Returns:
            Dict with fix results
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {'success': False, 'error': f'File not found: {file_path}'}
        
        # Read the original file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except Exception as e:
            return {'success': False, 'error': f'Could not read file: {e}'}
        
        # Create backup
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
        except Exception as e:
            self.logger.warning(f"Could not create backup: {e}")
        
        # Detect language
        language = self._detect_language(file_path)
        
        # Generate fix using AI
        fix_result = await self._generate_code_fix(
            file_path, original_content, language, error_message
        )
        
        if not fix_result['success']:
            return fix_result
        
        # Apply the fix
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fix_result['fixed_code'])
            
            return {
                'success': True,
                'file': str(file_path),
                'backup': str(backup_path),
                'changes': fix_result['explanation'],
                'fixed_code': fix_result['fixed_code']
            }
        except Exception as e:
            return {'success': False, 'error': f'Could not write fixed file: {e}'}
    
    async def _run_command(self, command: str) -> Dict:
        """Run a command and capture output."""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                'success': process.returncode == 0,
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8', errors='replace'),
                'stderr': stderr.decode('utf-8', errors='replace'),
                'output': stdout.decode('utf-8', errors='replace') + stderr.decode('utf-8', errors='replace')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'stderr': f"Command execution failed: {e}",
                'output': f"Command execution failed: {e}"
            }
    
    def _analyze_error(self, stderr: str, command: str) -> Dict:
        """Analyze error output to determine if it's fixable."""
        error_patterns = {
            # Python errors
            r'File "([^"]+)", line (\d+)': {'language': 'python', 'fixable': True},
            r'SyntaxError|NameError|AttributeError|ImportError|TypeError': {'language': 'python', 'fixable': True},
            
            # JavaScript/TypeScript errors  
            r'Error: .+ at .+:(\d+):(\d+)': {'language': 'javascript', 'fixable': True},
            r'SyntaxError|ReferenceError|TypeError': {'language': 'javascript', 'fixable': True},
            
            # C/C++ errors
            r'(\w+\.c[p]*):(\d+):(\d+): error:': {'language': 'c', 'fixable': True},
            r'undefined reference|undeclared|expected': {'language': 'c', 'fixable': True},
            
            # Java errors
            r'(\w+\.java):(\d+): error:': {'language': 'java', 'fixable': True},
            r'cannot find symbol|class .+ is public': {'language': 'java', 'fixable': True},
            
            # Rust errors
            r'error\[E\d+\]: .+ --> ([^:]+):(\d+):(\d+)': {'language': 'rust', 'fixable': True},
            
            # Go errors
            r'([^:]+):(\d+):(\d+): ': {'language': 'go', 'fixable': True}
        }
        
        for pattern, info in error_patterns.items():
            if re.search(pattern, stderr, re.IGNORECASE):
                match = re.search(pattern, stderr)
                return {
                    'fixable': True,
                    'language': info['language'],
                    'error_text': stderr,
                    'command': command,
                    'file_match': match.group(1) if match and len(match.groups()) > 0 else None,
                    'line_number': match.group(2) if match and len(match.groups()) > 1 else None
                }
        
        return {'fixable': False, 'error_text': stderr}
    
    async def _fix_error(self, error_info: Dict, original_files: Dict) -> Dict:
        """Generate and apply a fix for the detected error."""
        # Try to identify the problematic file
        file_path = self._find_error_file(error_info)
        
        if not file_path:
            return {'success': False, 'error': 'Could not identify file to fix'}
        
        # Read the file content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {'success': False, 'error': f'Could not read file {file_path}: {e}'}
        
        # Create backup if not already done
        if str(file_path) not in original_files:
            original_files[str(file_path)] = content
        
        # Generate fix using AI
        fix_result = await self._generate_code_fix(
            file_path, content, error_info['language'], error_info['error_text']
        )
        
        if not fix_result['success']:
            return fix_result
        
        # Apply the fix
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fix_result['fixed_code'])
            
            return {
                'success': True,
                'file': str(file_path),
                'explanation': fix_result['explanation']
            }
        except Exception as e:
            return {'success': False, 'error': f'Could not write fixed file: {e}'}
    
    def _find_error_file(self, error_info: Dict) -> Optional[Path]:
        """Find the file that needs to be fixed based on error information."""
        if error_info.get('file_match'):
            file_path = Path(error_info['file_match'])
            if file_path.exists():
                return file_path
        
        # Look for common files in current directory
        current_dir = Path('.')
        common_files = {
            'python': ['main.py', 'app.py', '*.py'],
            'javascript': ['main.js', 'index.js', 'app.js', '*.js'],
            'c': ['main.c', '*.c'],
            'java': ['Main.java', '*.java'],
            'rust': ['main.rs', 'lib.rs', '*.rs'],
            'go': ['main.go', '*.go']
        }
        
        language = error_info.get('language')
        if language in common_files:
            for pattern in common_files[language]:
                if '*' in pattern:
                    files = list(current_dir.glob(pattern))
                    if files:
                        return files[0]
                else:
                    file_path = current_dir / pattern
                    if file_path.exists():
                        return file_path
        
        return None
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension."""
        suffix = file_path.suffix.lower()
        return self.supported_languages.get(suffix, 'unknown')
    
    def _extract_fixed_code(self, response: str, language: str) -> Optional[str]:
        """Robustly extract fixed code from the AI response using multiple strategies."""
        # 1) Preferred: after FIXED_CODE: fenced block
        code_match = re.search(r'FIXED_CODE:\s*```(?:\w+)?\s*(.+?)\s*```', response, re.DOTALL)
        if code_match:
            return code_match.group(1).strip()
        
        # 2) Any fenced code block, pick the largest
        fences = re.findall(r'```(?:\w+)?\s*(.+?)\s*```', response, re.DOTALL)
        if fences:
            # choose the largest block assuming it's the full file
            return max((b.strip() for b in fences), key=len)
        
        # 3) Heuristic: if it looks like code, extract from first code-looking line
        lines = response.split('\n')
        code_start = None
        for i, line in enumerate(lines):
            s = line.strip()
            if language == 'python' and (s.startswith('import ') or s.startswith('from ') or s.startswith('def ') or s.startswith('class ') or s.startswith('#!') or s.startswith('"""') or s.startswith('# ')):
                code_start = i
                break
            if any(tok in s for tok in ('{', '}', ';', '(', ')')):
                code_start = i
                break
        if code_start is not None:
            candidate = '\n'.join(lines[code_start:]).strip()
            # Trim trailing narrative markers if any
            tail_markers = ['EXPLANATION:', 'Explanation:', 'Notes:', 'Usage:']
            for m in tail_markers:
                idx = candidate.rfind(m)
                if idx > 0:
                    candidate = candidate[:idx].strip()
            return candidate if candidate else None
        
        return None
    
    async def _generate_code_fix(self, file_path: Path, content: str, language: str, error_message: str) -> Dict:
        """Use AI to generate a fix for the code."""
        
        primary_prompt = f"""You are an expert code debugger and fixer. Please analyze the following {language} code and fix the errors.

FILE: {file_path}
ERROR MESSAGE:
{error_message}

CURRENT CODE:
```{language}
{content}
```

Please provide the corrected code. Your response should contain:
1. A brief explanation of what was wrong
2. The complete fixed code (not just the changes)

Format your response as:
EXPLANATION: [brief explanation of the fix]

FIXED_CODE:
```{language}
[complete corrected code here]
```

Make sure the fixed code is complete, syntactically correct, and addresses the specific error mentioned."""

        try:
            if not self.model:
                raise ValueError("AI model not specified for error correction")
            
            response = await self.ai_client.generate(
                model=self.model,
                prompt=primary_prompt,
                system_prompt=(
                    "You are a senior engineer fixing code. First explain the fix briefly, then output the full "
                    "corrected file inside a single code block."
                )
            )
            
            # Try robust extraction
            fixed_code = self._extract_fixed_code(response, language)
            explanation_match = re.search(r'EXPLANATION:\s*(.+?)(?=FIXED_CODE:|```|$)', response, re.DOTALL)
            explanation = explanation_match.group(1).strip() if explanation_match else "Applied automatic fix"
            
            if fixed_code:
                return {
                    'success': True,
                    'fixed_code': fixed_code,
                    'explanation': explanation
                }
            
            # Retry with strict instruction to return only a fenced code block
            retry_prompt = f"""Return ONLY the full corrected content of FILE {file_path} as a single fenced code block.
No prose, no explanation, no headers. Use exactly this format:
```{language}
<full corrected file content>
```
Current error to fix: {error_message or 'unknown error'}
Original content was provided earlier."""
            retry_resp = await self.ai_client.generate(
                model=self.model,
                prompt=retry_prompt,
                system_prompt=(
                    "Output ONLY one fenced code block with the complete corrected file. Do not include any text before or after."
                )
            )
            fixed_code = self._extract_fixed_code(retry_resp, language)
            if fixed_code:
                return {
                    'success': True,
                    'fixed_code': fixed_code,
                    'explanation': explanation
                }
            
            return {
                'success': False,
                'error': 'Could not extract fixed code from AI response'
            }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'AI generation failed: {e}'
            }

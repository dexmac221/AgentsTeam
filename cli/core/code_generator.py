"""
Code Generator - Intelligent code generation using multiple AI providers.

This module provides the core code generation functionality for AgentsTeam,
supporting both Ollama (local) and OpenAI (cloud) models. It handles project
creation, file generation, code completion, and intelligent code suggestions
based on project context and user requirements.

The generator uses advanced prompting techniques, context management, and
multiple AI providers to create production-quality code that follows best
practices and user specifications.
"""

import time
import json
import re
import aiohttp
from pathlib import Path
from typing import Dict, List, Any
from ..utils.logger import Logger
from ..clients.ollama_client import OllamaClient
from ..clients.openai_client import OpenAIClient

class CodeGenerator:
    """
    Core code generation engine for AgentsTeam.
    
    This class handles all code generation tasks including project creation,
    file generation, code completion, and intelligent suggestions. It supports
    multiple AI providers and uses advanced prompting techniques to generate
    production-quality code.
    
    The generator maintains context across conversations, understands project
    structure, and can create complex multi-file projects with proper
    architecture and best practices.
    
    Attributes:
        config: Configuration object containing API keys and settings
        logger (Logger): Logging utility for debugging and monitoring
        ollama_client (OllamaClient): Client for local Ollama model interactions
        openai_client (OpenAIClient): Client for OpenAI API interactions
    
    Example:
        >>> generator = CodeGenerator(config, logger)
        >>> result = await generator.generate_project(
        ...     description="FastAPI web service",
        ...     technologies=["python", "fastapi"],
        ...     model_info={"provider": "ollama", "model": "codellama"},
        ...     output_dir=Path("./my_project")
        ... )
    """
    
    def __init__(self, config, logger: Logger):
        """
        Initialize the code generator with configuration and AI clients.
        
        Args:
            config: Configuration object with API keys and settings
            logger (Logger): Logging utility for debugging and monitoring
        """
        self.config = config
        self.logger = logger
        self.ollama_client = OllamaClient(config, logger)
        self.openai_client = OpenAIClient(config, logger)
    
    async def generate_project(self, description: str, technologies: List[str], 
                             model_info: Dict[str, str], output_dir: Path) -> Dict[str, Any]:
        """
        Generate a complete project based on description and technologies.
        
        Creates a full project structure with multiple files, proper architecture,
        dependencies, and documentation. Uses AI to understand requirements and
        generate production-quality code following best practices.
        
        Args:
            description (str): Natural language description of the project
            technologies (List[str]): List of technologies/frameworks to use
            model_info (Dict[str, str): Information about the AI model to use
                                       containing 'provider' and 'model' keys
            output_dir (Path): Directory where the project should be created
            
        Returns:
            Dict[str, Any]: Generation result containing:
                - 'success' (bool): Whether generation was successful
                - 'files_created' (int): Number of files created
                - 'project_structure' (dict): Structure of created project
                - 'time_taken' (float): Time taken for generation
                - 'model_used' (str): Model that was used for generation
                - 'error' (str, optional): Error message if generation failed
                
        Raises:
            Exception: If project generation fails due to AI model errors,
                      file system issues, or invalid parameters
                      
        Example:
            >>> result = await generator.generate_project(
            ...     description="A REST API for managing tasks",
            ...     technologies=["python", "fastapi", "sqlite"],
            ...     model_info={"provider": "openai", "model": "gpt-4"},
            ...     output_dir=Path("./task_api")
            ... )
            >>> print(f"Created {result['files_created']} files")
        """
        start_time = time.time()
        
        try:
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Get appropriate client
            if model_info['provider'] == 'ollama':
                # Use host-aware client if a specific base_url is selected by the model selector
                base_url = model_info.get('base_url')
                client = OllamaClient(self.config, self.logger, base_url=base_url)
            else:
                client = self.openai_client
            
            # Generate project structure and files
            result = await self._generate_with_client(
                client, description, technologies, model_info, output_dir
            )
            
            generation_time = time.time() - start_time
            
            return {
                'success': True,
                'output_dir': str(output_dir.absolute()),
                'files_created': result['files_created'],
                'generation_time': generation_time,
                'instructions': result.get('instructions', []),
                'model_used': f"{model_info['provider']}:{model_info['model']}"
            }
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'generation_time': time.time() - start_time
            }
    
    async def _generate_with_client(self, client, description: str, technologies: List[str], 
                                  model_info: Dict[str, str], output_dir: Path) -> Dict[str, Any]:
        """Generate code using specified client"""
        
        # Build prompt based on complexity
        prompt = self._build_project_prompt(description, technologies)
        
        # Generate project plan first (disable code-only behavior for Ollama)
        if isinstance(client, OllamaClient):
            plan_response = await client.generate(
                model=model_info['model'],
                prompt=f"{prompt}\n\nFirst, create a JSON project plan with file structure and descriptions.",
                system_prompt="You are an expert software architect. Respond with well-structured JSON only.",
                code_only=False
            )
        else:
            plan_response = await client.generate(
                model=model_info['model'],
                prompt=f"{prompt}\n\nFirst, create a JSON project plan with file structure and descriptions.",
                system_prompt="You are an expert software architect. Respond with well-structured JSON only."
            )
        
        try:
            # Parse project plan
            plan = json.loads(self._extract_json_from_response(plan_response))
            self.logger.debug(f"Project plan: {json.dumps(plan, indent=2)}")
        except:
            # Fallback to simple structure
            plan = self._create_fallback_plan(description, technologies)
        
        # Generate each file
        files_created = 0
        instructions = []
        
        for file_info in plan.get('files', []):
            file_path = output_dir / file_info['path']
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate file content
            file_prompt = self._build_file_prompt(
                file_info, description, technologies, plan
            )
            
            # For file content, request code-only behavior on Ollama
            if isinstance(client, OllamaClient):
                content_response = await client.generate(
                    model=model_info['model'],
                    prompt=file_prompt,
                    system_prompt="You are an expert programmer. Generate clean, production-ready code with comments.",
                    code_only=True
                )
            else:
                content_response = await client.generate(
                    model=model_info['model'],
                    prompt=file_prompt,
                    system_prompt="You are an expert programmer. Generate clean, production-ready code with comments."
                )
            
            # Extract and save code
            # Prefer language by extension, not the plan-provided type
            inferred_language = self._get_language_from_extension(Path(file_info['path']).suffix)
            file_content = self._extract_code_from_response(content_response, inferred_language.lower())
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_content)
            
            files_created += 1
            self.logger.info(f"Generated: {file_path}")
        
        # Generate setup instructions (disable code-only behavior on Ollama)
        instructions_prompt = f"""
        Based on this project: {description}
        Technologies: {', '.join(technologies)}
        Files created: {[f['path'] for f in plan.get('files', [])]}
        
        Provide 3-5 clear setup and run instructions for the user.
        """
        
        if isinstance(client, OllamaClient):
            instructions_response = await client.generate(
                model=model_info['model'],
                prompt=instructions_prompt,
                system_prompt="Provide clear, actionable setup instructions as a simple list.",
                code_only=False
            )
        else:
            instructions_response = await client.generate(
                model=model_info['model'],
                prompt=instructions_prompt,
                system_prompt="Provide clear, actionable setup instructions as a simple list."
            )
        
        instructions = self._parse_instructions(instructions_response)
        
        return {
            'files_created': files_created,
            'instructions': instructions,
            'plan': plan
        }

    def _build_project_prompt(self, description: str, technologies: List[str]) -> str:
        """Build comprehensive project prompt"""
        tech_str = ', '.join(technologies) if technologies else 'appropriate technologies'
        
        return f"""
        Create a complete software project based on this description:
        {description}
        
        Technologies to use: {tech_str}
        
        Requirements:
        - Create a well-structured project with proper file organization
        - Include necessary configuration files
        - Add README.md with setup instructions
        - Include basic tests if applicable
        - Generate clean, documented code
        - Follow best practices and conventions
        """
    
    def _build_file_prompt(self, file_info: Dict, description: str, 
                          technologies: List[str], plan: Dict) -> str:
        """Build prompt for individual file generation"""
        file_extension = Path(file_info['path']).suffix.lower()
        
        # Determine file type and language
        language = self._get_language_from_extension(file_extension)
        
        return f"""
        Generate ONLY the code content for file: {file_info['path']}
        
        IMPORTANT INSTRUCTIONS:
        - Generate ONLY executable code, no explanations or documentation outside the code
        - Do NOT include markdown formatting, tables, or descriptive text
        - Do NOT use ```code``` blocks or any markdown syntax
        - Start directly with the code (imports, declarations, etc.)
        - Include necessary comments INSIDE the code using proper comment syntax
        - Make the code production-ready and complete
        
        File purpose: {file_info.get('description', 'Core file')}
        Language: {language}
        Project: {description}
        Technologies: {', '.join(technologies)}
        
        File requirements:
        - Follow {language} best practices and conventions
        - Include all necessary imports and dependencies
        - Add clear comments using {language} comment syntax
        - Make it production-ready and complete
        - Ensure it integrates with other project files
        
        GENERATE ONLY THE RAW {language.upper()} CODE - NO OTHER TEXT:
        """
    
    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from LLM response"""
        # Try to find JSON block
        if '```json' in response:
            start = response.find('```json') + 7
            end = response.find('```', start)
            return response[start:end].strip()
        elif '```' in response:
            start = response.find('```') + 3
            end = response.find('```', start)
            return response[start:end].strip()
        else:
            # Try to find JSON-like content
            start = response.find('{')
            end = response.rfind('}') + 1
            if start != -1 and end > start:
                return response[start:end]
            return response.strip()
    
    def _extract_code_from_response(self, response: str, file_type: str) -> str:
        """Extract clean code from LLM response, removing explanatory text"""
        
        # First, try to extract from code blocks
        if '```' in response:
            # Find all code blocks
            code_blocks = []
            lines = response.split('\n')
            in_code_block = False
            current_block = []
            current_lang = None
            target_lang = file_type.lower()
            
            for line in lines:
                if line.strip().startswith('```'):
                    if in_code_block:
                        # End of code block
                        if current_block:
                            block_text = '\n'.join(current_block)
                            code_blocks.append((current_lang, block_text))
                        current_block = []
                        current_lang = None
                        in_code_block = False
                    else:
                        # Start of code block, optionally capture language
                        in_code_block = True
                        fence = line.strip().lstrip('`')
                        parts = fence.split()
                        current_lang = parts[1].lower() if len(parts) > 1 else None
                elif in_code_block:
                    current_block.append(line)
            
            # If we found code blocks, prefer matching language, else largest
            if code_blocks:
                matching = [b for lang, b in code_blocks if lang and target_lang and lang.startswith(target_lang)]
                if matching:
                    return max(matching, key=len).strip()
                return max((b for _, b in code_blocks), key=len).strip()
        
        # If no code blocks, return as-is
        return response.strip()
    
    def _clean_response_text(self, text: str) -> str:
        """Remove common non-code text patterns"""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip lines that are clearly explanatory
            if any(pattern in line.lower() for pattern in [
                'below is', 'here is', 'here\'s', 'this is', 'this file',
                'the following', 'above code', 'this code', 'explanation:',
                'note:', 'important:', 'features:', 'requirements:',
                '| feature |', '|---------|', 'implementation |'
            ]):
                continue
                
            # Skip markdown headers and tables
            if line.startswith('#') or line.startswith('|') or line.startswith('*'):
                continue
                
            # Skip empty lines at the start
            if not cleaned_lines and not line:
                continue
                
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _contains_explanatory_text(self, text: str) -> bool:
        """Check if text contains explanatory content mixed with code"""
        explanatory_patterns = [
            'below is', 'here is', 'this file', 'the following',
            'features implemented', 'requirements', 'description',
            '| feature |', 'implementation', 'note that'
        ]
        
        first_lines = text.split('\n')[:5]
        first_part = ' '.join(first_lines).lower()
        
        return any(pattern in first_part for pattern in explanatory_patterns)
    
    def _extract_code_heuristically(self, text: str, file_type: str) -> str:
        """Extract code using heuristics based on file type"""
        lines = text.split('\n')
        
        # Find the first line that looks like code
        code_start = 0
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Python file detection
            if file_type == 'python' and (
                line.startswith('import ') or 
                line.startswith('from ') or
                line.startswith('def ') or
                line.startswith('class ') or
                line.startswith('#!/usr/bin/env python') or
                line.startswith('"""') or
                line.startswith('# ')
            ):
                code_start = i
                break
                
            # JavaScript/HTML file detection
            elif file_type in ['javascript', 'html'] and (
                line.startswith('<!DOCTYPE') or
                line.startswith('<html') or
                line.startswith('function') or
                line.startswith('const ') or
                line.startswith('let ') or
                line.startswith('var ') or
                line.startswith('// ')
            ):
                code_start = i
                break
                
            # CSS file detection
            elif file_type == 'css' and (
                '/*' in line or '{' in line or line.endswith(':')
            ):
                code_start = i
                break
                
            # Generic code detection
            elif any(char in line for char in ['{', '}', '(', ')', '=', ';']):
                code_start = i
                break
        
        # Extract from code start to end, removing trailing explanatory text
        code_lines = lines[code_start:]
        
        # Remove trailing explanatory content
        final_lines = []
        for line in code_lines:
            if any(pattern in line.lower() for pattern in [
                'this code', 'the above', 'features include', 'to use this'
            ]):
                break
            final_lines.append(line)
        
        return '\n'.join(final_lines).strip()
    
    def _get_language_from_extension(self, extension: str) -> str:
        """Get programming language from file extension"""
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.html': 'HTML',
            '.css': 'CSS',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.txt': 'text',
            '.sh': 'Bash',
            '.sql': 'SQL',
            '.go': 'Go',
            '.rs': 'Rust',
            '.java': 'Java',
            '.cpp': 'C++',
            '.c': 'C',
            '.php': 'PHP',
            '.rb': 'Ruby'
        }
        return extension_map.get(extension.lower(), 'text')
    
    def _create_fallback_plan(self, description: str, technologies: List[str]) -> Dict:
        """Create basic project structure when AI planning fails"""
        files = [
            {'path': 'README.md', 'description': 'Project documentation', 'type': 'markdown'},
            {'path': 'requirements.txt', 'description': 'Python dependencies', 'type': 'text'},
            {'path': 'main.py', 'description': 'Main application file', 'type': 'python'}
        ]
        
        # Add tech-specific files
        if 'fastapi' in [t.lower() for t in technologies]:
            files.extend([
                {'path': 'app.py', 'description': 'FastAPI application', 'type': 'python'},
                {'path': 'models.py', 'description': 'Data models', 'type': 'python'}
            ])
        
        if 'react' in [t.lower() for t in technologies]:
            files.extend([
                {'path': 'package.json', 'description': 'Node.js dependencies', 'type': 'json'},
                {'path': 'src/App.js', 'description': 'React main component', 'type': 'javascript'}
            ])
        
        return {
            'name': 'Generated Project',
            'description': description,
            'technologies': technologies,
            'files': files
        }
    
    def _parse_instructions(self, response: str) -> List[str]:
        """Parse setup instructions from LLM response"""
        instructions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Remove numbering and bullets
            line = re.sub(r'^\d+\.\s*', '', line)
            line = re.sub(r'^[-*]\s*', '', line)
            
            if line and len(line) > 10:  # Filter out very short lines
                instructions.append(line)
        
        # Limit to reasonable number
        return instructions[:6]
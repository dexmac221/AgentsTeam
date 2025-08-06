#!/usr/bin/env python3
"""
Fixed Project Generator using enhanced prompting and code extraction
This script will create a clean system monitoring FastAPI application
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

class FixedProjectGenerator:
    def __init__(self):
        self.config = Config()
        self.config.set('ollama.base_url', 'http://192.168.1.62:11434')
        self.logger = setup_logger()
        self.client = OllamaClient(self.config, self.logger)
        
    async def generate_clean_file(self, model: str, filename: str, description: str, 
                                 language: str, additional_requirements: str = "") -> str:
        """Generate clean code file without explanatory text"""
        
        system_prompt = f"""You are an expert {language} developer. Generate ONLY clean, executable {language} code.

STRICT RULES:
- Output ONLY the raw {language} code
- NO explanations, descriptions, or markdown
- NO ```code``` blocks or formatting
- NO tables or feature lists
- Start directly with code (imports, declarations, etc.)
- Include comments INSIDE the code using {language} comment syntax
- Make code production-ready and complete"""

        user_prompt = f"""Create the file: {filename}

Description: {description}

Requirements:
- Production-ready {language} code
- Include all necessary imports and dependencies
- Add clear comments using {language} comment syntax
- Follow {language} best practices
{additional_requirements}

GENERATE ONLY THE RAW {language.upper()} CODE:"""

        response = await self.client.generate(model, user_prompt, system_prompt)
        
        # Clean the response
        cleaned = self.clean_code_response(response)
        return cleaned
    
    def clean_code_response(self, response: str) -> str:
        """Aggressively clean the response to get only code"""
        lines = response.split('\n')
        cleaned_lines = []
        skip_patterns = [
            'below is', 'here is', 'here\'s', 'this is', 'this file',
            'the following', 'above code', 'this code', 'explanation:',
            'note:', 'important:', 'features:', 'requirements:',
            '| feature |', '|---------|', 'implementation |', 'usage:',
            'how to use', 'example:', 'install:', 'run:', 'start:'
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
                
            # Detect start of actual code
            if not in_code:
                if (line.strip().startswith('import ') or 
                    line.strip().startswith('from ') or
                    line.strip().startswith('#!/') or
                    line.strip().startswith('def ') or
                    line.strip().startswith('class ') or
                    line.strip().startswith('async def ') or
                    line.strip().startswith('"""') or
                    line.strip().startswith('<!DOCTYPE') or
                    line.strip().startswith('<html') or
                    line.strip().startswith('function ') or
                    line.strip().startswith('const ') or
                    line.strip().startswith('let ') or
                    line.strip().startswith('var ') or
                    line.strip().startswith('{') or
                    (line.strip().startswith('#') and line.strip().startswith('#!/')) or
                    (line.strip() and any(char in line for char in ['=', ':', '{', '}', '(', ')']))):
                    in_code = True
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        # Remove trailing explanatory text
        if 'this code' in result.lower().split('\n')[-3:]:
            lines = result.split('\n')
            for i in range(len(lines) - 1, -1, -1):
                if any(pattern in lines[i].lower() for pattern in ['this code', 'the above', 'to use']):
                    result = '\n'.join(lines[:i]).strip()
                    break
        
        return result

async def generate_system_monitor():
    """Generate the system monitoring FastAPI application with clean code"""
    
    generator = FixedProjectGenerator()
    
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
        # Create directories
        os.makedirs("templates", exist_ok=True)
        os.makedirs("static", exist_ok=True)
        
        # 1. Generate main FastAPI application
        print("🚀 Generating main.py...")
        main_code = await generator.generate_clean_file(
            model=model,
            filename="main.py",
            description="FastAPI application for system monitoring with GPU, CPU, memory, disk, network monitoring",
            language="Python",
            additional_requirements="""
- Use FastAPI with async endpoints
- Include WebSocket for real-time updates
- Add CORS middleware
- Serve static files and templates
- Include health check endpoint
- Use Jinja2 for templates
- Add proper error handling and logging
- Import system_monitor module for monitoring functions"""
        )
        
        with open("main.py", "w") as f:
            f.write(main_code)
        print("✅ Generated main.py")
        
        # 2. Generate system monitoring module
        print("🔧 Generating system_monitor.py...")
        monitor_code = await generator.generate_clean_file(
            model=model,
            filename="system_monitor.py",
            description="System monitoring functions for GPU, CPU, memory, disk, network and processes",
            language="Python",
            additional_requirements="""
- Use psutil for system monitoring
- Use subprocess to call nvidia-smi for GPU info
- Include async functions where appropriate
- Add error handling for missing nvidia-smi
- Return data as dictionaries for JSON serialization
- Include functions: get_gpu_info, get_cpu_info, get_memory_info, get_disk_info, get_network_info, get_top_processes, get_system_info"""
        )
        
        with open("system_monitor.py", "w") as f:
            f.write(monitor_code)
        print("✅ Generated system_monitor.py")
        
        # 3. Generate HTML template
        print("🎨 Generating templates/index.html...")
        html_code = await generator.generate_clean_file(
            model=model,
            filename="templates/index.html",
            description="Modern responsive HTML dashboard for system monitoring with Bootstrap 5",
            language="HTML",
            additional_requirements="""
- Use Bootstrap 5 from CDN
- Include Font Awesome icons
- Add cards for GPU, CPU, Memory, Disk, Network status
- Include table for top processes
- Add WebSocket JavaScript for real-time updates
- Include Chart.js for graphs
- Make mobile responsive
- Add progress bars for usage percentages
- Include custom CSS link and JS link"""
        )
        
        with open("templates/index.html", "w") as f:
            f.write(html_code)
        print("✅ Generated templates/index.html")
        
        # 4. Generate CSS
        print("💅 Generating static/style.css...")
        css_code = await generator.generate_clean_file(
            model=model,
            filename="static/style.css",
            description="Custom CSS styles for the system monitoring dashboard",
            language="CSS",
            additional_requirements="""
- Modern dark theme with professional colors
- Card hover effects and animations
- Progress bar styling
- Status indicators (green/yellow/red)
- Responsive design improvements
- Custom button styles
- Table styling improvements
- Mobile-first design"""
        )
        
        with open("static/style.css", "w") as f:
            f.write(css_code)
        print("✅ Generated static/style.css")
        
        # 5. Generate JavaScript
        print("⚡ Generating static/app.js...")
        js_code = await generator.generate_clean_file(
            model=model,
            filename="static/app.js",
            description="JavaScript for WebSocket connection and real-time dashboard updates",
            language="JavaScript",
            additional_requirements="""
- WebSocket connection with auto-reconnect
- Functions to update DOM elements with system data
- Chart.js integration for real-time graphs
- Error handling for connection issues
- Auto-refresh functionality
- Mobile-friendly interactions
- Update progress bars, tables, and status indicators"""
        )
        
        with open("static/app.js", "w") as f:
            f.write(js_code)
        print("✅ Generated static/app.js")
        
        # 6. Generate requirements.txt
        print("📦 Generating requirements.txt...")
        requirements_code = await generator.generate_clean_file(
            model=model,
            filename="requirements.txt",
            description="Python dependencies for FastAPI system monitoring application",
            language="text",
            additional_requirements="""
- Include FastAPI, uvicorn, psutil, jinja2, python-multipart
- Include websockets for WebSocket support
- Add aiofiles for static file serving
- Include any other necessary dependencies
- Use specific versions for stability"""
        )
        
        with open("requirements.txt", "w") as f:
            f.write(requirements_code)
        print("✅ Generated requirements.txt")
        
        # 7. Generate startup script
        print("🚀 Generating run.py...")
        run_code = await generator.generate_clean_file(
            model=model,
            filename="run.py",
            description="Python startup script with command line arguments for the system monitor",
            language="Python",
            additional_requirements="""
- Use argparse for command line arguments
- Support --host, --port, --reload, --log-level options
- Check system requirements and dependencies
- Start uvicorn server with proper configuration
- Include help text and error handling"""
        )
        
        with open("run.py", "w") as f:
            f.write(run_code)
        print("✅ Generated run.py")
        
        # 8. Generate README
        print("📚 Generating README.md...")
        readme_code = await generator.generate_clean_file(
            model=model,
            filename="README.md",
            description="README documentation for FastAPI System Monitor project",
            language="Markdown",
            additional_requirements="""
- Include project description and features
- Add installation and setup instructions
- Include usage examples and API documentation
- Add troubleshooting section
- Include screenshots description and configuration options"""
        )
        
        with open("README.md", "w") as f:
            f.write(readme_code)
        print("✅ Generated README.md")
        
        print("\n🎉 Clean System Monitor project generated successfully!")
        print(f"✅ Generated using model: {model}")
        print("\nNext steps:")
        print("1. pip install -r requirements.txt")
        print("2. python run.py")
        print("3. Open http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Error generating project: {e}")

if __name__ == "__main__":
    asyncio.run(generate_system_monitor())

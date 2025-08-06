#!/usr/bin/env python3
"""
Project Generator using gpt-oss:20b model
This script will create a comprehensive FastAPI system monitoring application
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

async def generate_system_monitor():
    """Generate the system monitoring FastAPI application"""
    
    # Setup
    config = Config()
    config.set('ollama.base_url', 'http://192.168.1.62:11434')
    logger = setup_logger()
    client = OllamaClient(config, logger)
    
    # Check if gpt-oss:20b is available
    model = "gpt-oss:20b"
    is_available = await client.check_model_available(model)
    if not is_available:
        print(f"❌ Model {model} not available. Trying gpt-oss:latest...")
        model = "gpt-oss:latest"
        is_available = await client.check_model_available(model)
        if not is_available:
            print("❌ No gpt-oss model available!")
            return
    
    print(f"✅ Using model: {model}")
    
    system_prompt = """You are an expert Python developer specializing in FastAPI, system monitoring, and web interfaces. 
Create production-ready, well-documented code with proper error handling and modern practices.
Focus on creating a comprehensive system monitoring application with GPU status using nvidia-smi, CPU, memory, and network monitoring.
The interface should be modern and responsive using Bootstrap 5."""

    # Generate main FastAPI application
    print("🚀 Generating main FastAPI application...")
    app_prompt = """Create a comprehensive FastAPI application for system monitoring with the following features:

1. **GPU Monitoring**: Use nvidia-smi to get GPU status, temperature, memory usage, utilization
2. **CPU Monitoring**: Get CPU usage, load average, core count, frequency
3. **Memory Monitoring**: RAM usage, swap usage, available memory
4. **Disk Monitoring**: Disk usage, read/write statistics
5. **Network Monitoring**: Network interface statistics, bandwidth usage
6. **Process Monitoring**: Top processes by CPU/memory usage
7. **System Info**: OS info, uptime, hostname

Requirements:
- FastAPI with async endpoints
- Jinja2 templates for the web interface
- WebSocket for real-time updates
- Static files serving
- Bootstrap 5 responsive design
- Error handling and logging
- CORS support
- Health check endpoint

Create the main.py file with all API endpoints and WebSocket handler.
Include comprehensive error handling and proper HTTP status codes.
Make it production-ready with logging and configuration."""

    try:
        main_app_code = await client.generate(model, app_prompt, system_prompt)
        
        # Save main.py
        with open("main.py", "w") as f:
            f.write(main_app_code)
        print("✅ Generated main.py")
        
        # Generate system monitoring modules
        print("🔧 Generating system monitoring modules...")
        
        modules_prompt = """Create a Python module called 'system_monitor.py' that provides comprehensive system monitoring functions:

1. **GPU Functions**:
   - get_gpu_info(): Use nvidia-smi to get GPU status, temperature, memory, utilization
   - parse_nvidia_smi_output(): Parse nvidia-smi XML/JSON output
   
2. **CPU Functions**:
   - get_cpu_info(): CPU usage per core, load average, frequency
   - get_cpu_temperature(): CPU temperature if available
   
3. **Memory Functions**:
   - get_memory_info(): RAM/swap usage, available memory
   
4. **Disk Functions**:
   - get_disk_info(): Disk usage for all mounted drives
   - get_disk_io(): Read/write statistics
   
5. **Network Functions**:
   - get_network_info(): Network interface statistics
   - get_network_speed(): Network speed and bandwidth usage
   
6. **Process Functions**:
   - get_top_processes(): Top processes by CPU/memory
   
7. **System Functions**:
   - get_system_info(): OS info, uptime, hostname, kernel version

Use libraries like psutil, subprocess for nvidia-smi, and proper error handling.
Make all functions async where appropriate.
Include detailed docstrings and type hints."""

        system_monitor_code = await client.generate(model, modules_prompt, system_prompt)
        
        with open("system_monitor.py", "w") as f:
            f.write(system_monitor_code)
        print("✅ Generated system_monitor.py")
        
        # Generate HTML template
        print("🎨 Generating HTML template...")
        
        template_prompt = """Create a modern, responsive HTML template called 'index.html' for the system monitoring dashboard:

Features needed:
1. **Bootstrap 5** responsive design
2. **Real-time updates** via WebSocket
3. **Cards layout** for different monitoring sections:
   - GPU Status (temperature, memory, utilization)
   - CPU Status (usage, load, temperature)
   - Memory Status (RAM, swap)
   - Disk Status (usage, I/O)
   - Network Status (interfaces, speed)
   - Top Processes table
   - System Information

4. **Interactive elements**:
   - Refresh button
   - Auto-refresh toggle
   - Time interval selector
   - Dark/light theme toggle

5. **Charts and visualizations**:
   - Progress bars for usage percentages
   - Real-time charts using Chart.js
   - Color-coded status indicators

6. **Mobile responsive** design
7. **Professional appearance** with proper spacing and typography
8. **Real-time status indicators** (green/yellow/red for different thresholds)

Include JavaScript for WebSocket connection and DOM updates.
Use Font Awesome icons for visual appeal.
Make it look professional and modern like a enterprise monitoring dashboard."""

        template_code = await client.generate(model, template_prompt, system_prompt)
        
        # Create templates directory
        os.makedirs("templates", exist_ok=True)
        with open("templates/index.html", "w") as f:
            f.write(template_code)
        print("✅ Generated templates/index.html")
        
        # Generate CSS and JavaScript
        print("💅 Generating static files...")
        
        static_prompt = """Create a comprehensive CSS file called 'style.css' with custom styles for the system monitoring dashboard:

Requirements:
1. **Modern design** with professional color scheme
2. **Dark theme support** with CSS variables
3. **Custom card styles** with hover effects
4. **Progress bar animations**
5. **Responsive design** improvements
6. **Status indicators** (green/yellow/red colors)
7. **Chart container styling**
8. **Table improvements** with zebra striping
9. **Button animations and hover effects**
10. **Loading spinners and transitions**
11. **Typography improvements**
12. **Mobile-first responsive design**

Include CSS for:
- Custom color palette
- Card animations
- Status badges
- Progress bars
- Tables
- Buttons
- Navigation
- Dark/light theme variables
- Media queries for mobile devices"""

        css_code = await client.generate(model, static_prompt, system_prompt)
        
        # Create static directory
        os.makedirs("static", exist_ok=True)
        with open("static/style.css", "w") as f:
            f.write(css_code)
        print("✅ Generated static/style.css")
        
        # Generate JavaScript
        js_prompt = """Create a comprehensive JavaScript file called 'app.js' for the system monitoring dashboard:

Features needed:
1. **WebSocket connection** management with auto-reconnect
2. **Real-time data updates** from FastAPI WebSocket
3. **Chart.js integration** for real-time charts:
   - CPU usage over time
   - Memory usage over time
   - GPU temperature over time
   - Network bandwidth over time

4. **DOM manipulation functions**:
   - Update progress bars
   - Update status indicators
   - Update tables (processes)
   - Update system info cards

5. **User interface controls**:
   - Auto-refresh toggle
   - Refresh interval selector
   - Manual refresh button
   - Dark/light theme toggle
   - Fullscreen mode

6. **Error handling**:
   - WebSocket connection errors
   - API request failures
   - Display error messages to user

7. **Performance optimization**:
   - Efficient DOM updates
   - Memory management for charts
   - Throttled updates

8. **Mobile support**:
   - Touch-friendly controls
   - Responsive chart sizing

Include proper error handling, connection management, and user feedback.
Use modern ES6+ JavaScript features.
Make it production-ready with proper error handling and logging."""

        js_code = await client.generate(model, js_prompt, system_prompt)
        
        with open("static/app.js", "w") as f:
            f.write(js_code)
        print("✅ Generated static/app.js")
        
        # Generate requirements.txt
        print("📦 Generating requirements.txt...")
        
        requirements_prompt = """Create a comprehensive requirements.txt file for the FastAPI system monitoring application.

Include all necessary dependencies:
1. **FastAPI** and related packages (uvicorn, jinja2, python-multipart)
2. **System monitoring** libraries (psutil)
3. **WebSocket** support
4. **CORS** middleware
5. **Static files** serving
6. **Logging** and configuration
7. **Testing** libraries (pytest, httpx)
8. **Development** tools (black, flake8)

Specify exact versions for production stability.
Include comments explaining what each package is for."""

        requirements_code = await client.generate(model, requirements_prompt, system_prompt)
        
        with open("requirements.txt", "w") as f:
            f.write(requirements_code)
        print("✅ Generated requirements.txt")
        
        # Generate README
        print("📚 Generating README.md...")
        
        readme_prompt = """Create a comprehensive README.md file for the FastAPI System Monitor application.

Include:
1. **Project description** and features
2. **Prerequisites** (Python, nvidia-smi if using GPU monitoring)
3. **Installation instructions** step by step
4. **Usage examples** and commands
5. **API documentation** with endpoint descriptions
6. **WebSocket documentation**
7. **Configuration options**
8. **Screenshots/features description**
9. **Troubleshooting** common issues
10. **Contributing** guidelines
11. **License** information

Make it professional and comprehensive like a production application.
Include code examples and command-line usage."""

        readme_code = await client.generate(model, readme_prompt, system_prompt)
        
        with open("README.md", "w") as f:
            f.write(readme_code)
        print("✅ Generated README.md")
        
        # Generate startup script
        print("🚀 Generating startup script...")
        
        startup_prompt = """Create a Python startup script called 'run.py' for the system monitoring application:

Features:
1. **Command-line arguments** parsing:
   - --host (default: 0.0.0.0)
   - --port (default: 8000)
   - --reload (development mode)
   - --log-level (INFO, DEBUG, WARNING, ERROR)
   - --workers (number of workers)

2. **Environment setup**:
   - Check Python version
   - Verify required dependencies
   - Check nvidia-smi availability
   - Create directories if needed

3. **Configuration validation**:
   - Check system permissions
   - Validate monitoring capabilities
   - Test nvidia-smi if GPU monitoring enabled

4. **Uvicorn server startup** with proper configuration
5. **Error handling** and user-friendly messages
6. **Help text** and usage examples

Make it production-ready with proper error handling and logging setup."""

        startup_code = await client.generate(model, startup_prompt, system_prompt)
        
        with open("run.py", "w") as f:
            f.write(startup_code)
        print("✅ Generated run.py")
        
        print("\n🎉 System Monitor project generated successfully!")
        print("\nGenerated files:")
        print("  📄 main.py - FastAPI application")
        print("  🔧 system_monitor.py - System monitoring functions")
        print("  🎨 templates/index.html - Web interface")
        print("  💅 static/style.css - Custom styles")
        print("  ⚡ static/app.js - JavaScript functionality")
        print("  📦 requirements.txt - Dependencies")
        print("  📚 README.md - Documentation")
        print("  🚀 run.py - Startup script")
        
        print(f"\n✅ Generated using model: {model}")
        print("\nNext steps:")
        print("1. pip install -r requirements.txt")
        print("2. python run.py")
        print("3. Open http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Error generating project: {e}")

if __name__ == "__main__":
    asyncio.run(generate_system_monitor())

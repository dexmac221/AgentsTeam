#!/usr/bin/env python3
"""
Setup script for AgentsTeam CLI
"""

from setuptools import setup, find_packages

setup(
    name="agentsteam-cli",
    version="1.0.0",
    description="Simple CLI for AI-powered code generation using Ollama and OpenAI",
    author="AgentsTeam",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.9.0",
    ],
    entry_points={
        "console_scripts": [
            "agentsteam=cli.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
"""
Project Complexity Analyzer - Intelligent project complexity assessment.

This module analyzes project descriptions and requirements to determine the
appropriate complexity level and recommend the best AI model for generation.
It uses keyword analysis, technology stack assessment, and pattern recognition
to categorize projects as simple, medium, or complex.

The analyzer helps optimize resource usage by recommending local models for
simple projects and cloud models for complex ones, improving both performance
and cost efficiency.
"""

import re
from typing import List
from ..utils.logger import Logger

class ProjectAnalyzer:
    """
    Intelligent project complexity analyzer for optimal AI model selection.
    
    This class analyzes project descriptions and technology requirements to
    determine the appropriate complexity level and recommend the best AI model
    for code generation. It uses sophisticated keyword analysis and pattern
    recognition to optimize resource usage and generation quality.
    
    The analyzer categorizes projects into three complexity levels:
    - Simple: Basic CRUD apps, static sites, simple scripts
    - Medium: APIs, dashboards, real-time features, authentication
    - Complex: Microservices, ML pipelines, distributed systems
    
    Attributes:
        logger (Logger): Logging utility for debugging and monitoring
    """
    
    def __init__(self, logger: Logger):
        """
        Initialize the project analyzer.
        
        Args:
            logger (Logger): Logging utility for debugging and monitoring
        """
        self.logger = logger
    
    def analyze_complexity(self, description: str, technologies: List[str]) -> str:
        """
        Analyze project description and technology stack to determine complexity.
        
        Uses keyword analysis, technology assessment, and pattern recognition
        to categorize projects into complexity levels. This helps determine
        whether to use local models (for simple projects) or cloud models
        (for complex projects).
        
        Args:
            description (str): Natural language description of the project
            technologies (List[str]): List of technologies/frameworks to be used
            
        Returns:
            str: Complexity level - one of 'simple', 'medium', or 'complex'
            
        Example:
            >>> analyzer = ProjectAnalyzer(logger)
            >>> complexity = analyzer.analyze_complexity(
            ...     "A microservices architecture with ML pipeline",
            ...     ["kubernetes", "tensorflow", "kafka"]
            ... )
            >>> print(complexity)  # Output: "complex"
        """
        
        score = 0
        description_lower = description.lower()
        tech_lower = [tech.lower() for tech in technologies]
        
        # Simple indicators (score 0-10)
        simple_keywords = [
            'simple', 'basic', 'hello world', 'crud', 'todo', 'blog',
            'calculator', 'counter', 'form', 'landing page'
        ]
        
        # Medium complexity indicators (score 10-20)
        medium_keywords = [
            'authentication', 'auth', 'database', 'api', 'rest', 'graphql',
            'dashboard', 'admin', 'user management', 'file upload',
            'search', 'pagination', 'real-time', 'websocket'
        ]
        
        # Complex indicators (score 20+)
        complex_keywords = [
            'microservices', 'distributed', 'machine learning', 'ml', 'ai',
            'blockchain', 'cryptocurrency', 'kubernetes', 'docker swarm',
            'event driven', 'message queue', 'kafka', 'elasticsearch',
            'big data', 'analytics', 'data pipeline', 'etl',
            'recommendation system', 'neural network', 'tensorflow',
            'computer vision', 'nlp', 'natural language'
        ]
        
        # Advanced enterprise indicators (score 30+)
        enterprise_keywords = [
            'enterprise', 'multi-tenant', 'scalable architecture',
            'high availability', 'fault tolerant', 'load balancer',
            'cdn', 'caching layer', 'monitoring', 'observability',
            'ci/cd', 'devops', 'infrastructure', 'terraform'
        ]
        
        # Count keyword matches
        for keyword in simple_keywords:
            if keyword in description_lower:
                score += 1
                
        for keyword in medium_keywords:
            if keyword in description_lower:
                score += 10
                
        for keyword in complex_keywords:
            if keyword in description_lower:
                score += 20
                
        for keyword in enterprise_keywords:
            if keyword in description_lower:
                score += 30
        
        # Technology stack analysis
        tech_complexity_map = {
            # Simple techs
            'html': 1, 'css': 1, 'javascript': 2, 'python': 2,
            'flask': 3, 'fastapi': 3, 'express': 3,
            
            # Medium complexity techs  
            'react': 8, 'vue': 8, 'angular': 10, 'node.js': 8,
            'postgresql': 10, 'mongodb': 10, 'redis': 12,
            'docker': 15, 'nginx': 12,
            
            # Complex techs
            'kubernetes': 25, 'tensorflow': 25, 'pytorch': 25,
            'kafka': 20, 'elasticsearch': 20, 'rabbitmq': 15,
            'graphql': 15, 'grpc': 20, 'prometheus': 20,
            
            # Enterprise techs
            'terraform': 30, 'ansible': 25, 'jenkins': 20,
            'aws': 15, 'gcp': 15, 'azure': 15
        }
        
        for tech in tech_lower:
            tech_score = tech_complexity_map.get(tech, 5)
            score += tech_score
        
        # Description length and detail analysis
        word_count = len(description.split())
        if word_count > 50:
            score += 10
        elif word_count > 100:
            score += 20
        
        # Multiple service indicators
        service_indicators = ['service', 'component', 'module', 'layer']
        service_count = sum(description_lower.count(indicator) for indicator in service_indicators)
        if service_count > 3:
            score += 15
        
        # Requirements complexity
        requirement_patterns = [
            r'(\d+)\s*requirements?',
            r'(\d+)\s*features?',
            r'(\d+)\s*components?'
        ]
        
        for pattern in requirement_patterns:
            matches = re.findall(pattern, description_lower)
            for match in matches:
                count = int(match)
                if count > 5:
                    score += count * 2
        
        # Determine final complexity
        if score <= 15:
            complexity = 'simple'
        elif score <= 40:
            complexity = 'medium'
        else:
            complexity = 'complex'
        
        self.logger.debug(f"Complexity analysis: score={score}, level={complexity}")
        self.logger.debug(f"Description: {description[:100]}...")
        self.logger.debug(f"Technologies: {technologies}")
        
        return complexity
    
    def estimate_generation_time(self, complexity: str, model_provider: str) -> float:
        """Estimate code generation time in seconds"""
        base_times = {
            'simple': {'ollama': 10, 'openai': 5},
            'medium': {'ollama': 30, 'openai': 15},
            'complex': {'ollama': 90, 'openai': 45}
        }
        
        return base_times.get(complexity, {}).get(model_provider, 30)
    
    def estimate_file_count(self, complexity: str) -> int:
        """Estimate number of files to be generated"""
        estimates = {
            'simple': (2, 6),
            'medium': (8, 15),
            'complex': (15, 30)
        }
        
        min_files, max_files = estimates.get(complexity, (5, 10))
        return (min_files + max_files) // 2
""" Multi-Agent Parallel Project Builder"""
import os
import json
import re
import time
import threading
import concurrent.futures
from pathlib import Path
from groq_client import GroqClient

class ProjectBuilder:
    def __init__(self, output_dir="."):
        self.output_dir = Path(output_dir)
        self.orchestrator = GroqClient(model="openai/gpt-oss-120b")
        self.frontend_agent = GroqClient(model="openai/gpt-oss-20b")
        self.backend_agent = GroqClient(model="openai/gpt-oss-20b")
        self.config_agent = GroqClient(model="openai/gpt-oss-120b")
        self.generator = GroqClient(model="openai/gpt-oss-20b")
    
    def build_project(self, user_request: str):
        """Main entry point - build entire project"""
        print(f"\n{'='*60}")
        print(f"🤖 QANWAS - AUTONOMOUS PROJECT BUILDER")
        print(f"Request: {user_request}")
        print(f"{'='*60}\n")
        
        # Step 1: Architect plans the project
        print("[1/4] 🧠 Architect planning project structure...")
        project_plan = self.plan_project(user_request)
        
        # Step 2: Show plan
        self.display_plan(project_plan)
        
        # Step 3: Generate files in PARALLEL
        print(f"\n[2/4] 📝 Generating {len(project_plan['files'])} files in parallel...")
        generated_files = self.generate_files_parallel(project_plan)
        
        # Step 4: Validate and auto-fix
        print(f"\n[3/4] 🔍 Validating project...")
        generated_files = self.validate_and_fix(user_request, generated_files)
        
        print(f"\n{'='*60}")
        print(f"🎉 PROJECT COMPLETE!")
        print(f"Location: {self.output_dir.absolute()}")
        print(f"{'='*60}\n")
    
    def generate_files_parallel(self, plan: dict) -> list:
        """Generate files using 3 parallel agents"""
        
        # Group files by type
        frontend_files = [f for f in plan['files'] if f['type'] == 'frontend']
        backend_files = [f for f in plan['files'] if f['type'] == 'backend']
        config_files = [f for f in plan['files'] if f['type'] in ['config', 'docs']]
        
        print(f"\n  📁 Distributing work to agents:")
        if frontend_files:
            print(f"    🎨 Frontend Agent (20B): {len(frontend_files)} files")
            for f in frontend_files:
                print(f"       - {f['path']}")
        if backend_files:
            print(f"    ⚙️  Backend Agent (20B): {len(backend_files)} files")
            for f in backend_files:
                print(f"       - {f['path']}")
        if config_files:
            print(f"    🔧 Config Agent (120B): {len(config_files)} files")
            for f in config_files:
                print(f"       - {f['path']}")
        
        print(f"\n  🚀 Launching parallel agents...\n")
        
        all_files = []
        
        # Use ThreadPoolExecutor for parallel execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            if frontend_files:
                futures['frontend'] = executor.submit(
                    self._generate_group,
                    frontend_files,
                    plan,
                    "frontend",
                    self.frontend_agent
                )
            
            if backend_files:
                futures['backend'] = executor.submit(
                    self._generate_group,
                    backend_files,
                    plan,
                    "backend",
                    self.backend_agent
                )
            
            if config_files:
                futures['config'] = executor.submit(
                    self._generate_group,
                    config_files,
                    plan,
                    "config",
                    self.config_agent
                )
            
            # Collect results as they complete
            for category, future in futures.items():
                try:
                    files = future.result()
                    all_files.extend(files)
                    print(f"\n  ✅ {category.upper()} agent completed: {len(files)} files")
                except Exception as e:
                    print(f"\n  ❌ {category} agent failed: {e}")
        
        return all_files
    
    def _generate_group(self, files: list, plan: dict, category: str, agent: GroqClient) -> list:
        """Generate a group of files using one agent"""
        generated = []
        
        for i, file_spec in enumerate(files, 1):
            print(f"  [{category}] [{i}/{len(files)}] Generating {file_spec['path']}...")
            
            # Special prompt for README
            if file_spec['path'].lower().endswith('readme.md'):
                prompt = f"""You are the {category} specialist. Generate a README.md for this project:

Project: {plan['project_name']}
Description: {plan.get('description', 'N/A')}
Tech stack: {', '.join(plan.get('tech_stack', []))}
Files in project: {', '.join([f['path'] for f in plan['files']])}

The README MUST include:
1. Project title and description
2. What the project does
3. Installation/setup instructions
4. HOW TO START/RUN the project (exact commands)
5. Basic usage examples
6. Project structure overview

Use proper markdown formatting."""
                max_tokens = 4000
            else:
                prompt = f"""You are the {category} specialist. Generate this file:

Project: {plan['project_name']}
File: {file_spec['path']}
Type: {file_spec['type']}
Purpose: {file_spec['description']}

Generate COMPLETE, production-ready code. Include all imports, proper error handling, and comments.
Do NOT truncate. Output the FULL file content."""
                max_tokens = 4000
            
            # Generate silently (parallel)
            content = agent.generate_silent(prompt, max_tokens=max_tokens, temperature=0.2)
            
            # Check if empty
            if not content or len(content.strip()) == 0:
                print(f"  ⚠️ [{category}] Empty, retrying...")
                content = agent.generate_silent(prompt, max_tokens=max_tokens, temperature=0.3)
            
            # Write file immediately
            filepath = self.output_dir / file_spec['path']
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(content)
            
            print(f"  ✓ [{category}] Created {file_spec['path']} ({len(content)} chars)")
            
            generated.append({
                'path': file_spec['path'],
                'description': file_spec['description'],
                'type': file_spec['type'],
                'content': content
            })
            
            time.sleep(0.5)  # Small delay to avoid rate limits
        
        return generated
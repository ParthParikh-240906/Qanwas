"""V5: Autonomous Project Builder"""
import os
import json
import re
from pathlib import Path
from groq_client import GroqClient

class ProjectBuilder:
    def __init__(self, output_dir="."):
        self.output_dir = Path(output_dir)
        self.orchestrator = GroqClient(model="openai/gpt-oss-120b")
        self.generator = GroqClient(model="openai/gpt-oss-20b")
    
    def build_project(self, user_request: str):
        """Main entry point - build entire project"""
        print(f"\n{'='*60}")
        print(f"🤖 AUTONOMOUS PROJECT BUILDER")
        print(f"Request: {user_request}")
        print(f"{'='*60}\n")
        
        # Step 1: Architect plans the project
        print("[1/4] 🧠 Architect planning project structure...")
        project_plan = self.plan_project(user_request)
        
        # Step 2: Show plan
        self.display_plan(project_plan)
        
        # Step 3: Generate each file
        print(f"\n[2/4] 📝 Generating {len(project_plan['files'])} files...")
        generated_files = self.generate_files(project_plan)
        
        # Step 4: Write files to disk
        print(f"\n[3/4] 💾 Writing files to disk...")
        self.write_files(generated_files)
        
        # Step 5: Final review
        print(f"\n[4/4] ✅ Final review...")
        self.final_review(generated_files)
        
        print(f"\n{'='*60}")
        print(f"🎉 PROJECT COMPLETE!")
        print(f"Location: {self.output_dir.absolute()}")
        print(f"{'='*60}\n")
    
    def plan_project(self, user_request: str) -> dict:
        """GPT-OSS-120B plans the entire project"""
        prompt = f"""You are an expert software architect. Plan a project for this request:

"{user_request}"

Think about the BEST architecture. Consider:
- What files are needed?
- What's the most efficient structure?
- What technologies to use?
- How components interact?

Return a JSON object with:
{{
    "project_name": "name",
    "description": "brief description",
    "tech_stack": ["technology1", "technology2"],
    "files": [
        {{
            "path": "relative/path/to/file",
            "description": "what this file does",
            "type": "frontend/backend/config/docs"
        }},
        ...
    ]
}}

Include ALL necessary files - frontend, backend, configs, README, etc.
Be specific about file paths and purposes.

Return ONLY the JSON, no other text."""
        
        response = self.orchestrator.generate(prompt, max_tokens=2000, temperature=0.3)
        
        # Parse JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Fallback plan
        return {
            "project_name": "project",
            "description": user_request,
            "tech_stack": ["python"],
            "files": [
                {"path": "main.py", "description": "Main file", "type": "backend"},
                {"path": "README.md", "description": "Documentation", "type": "docs"}
            ]
        }
    
    def display_plan(self, plan: dict):
        """Show the project plan"""
        print(f"\n  Project: {plan['project_name']}")
        print(f"  Description: {plan.get('description', 'N/A')}")
        print(f"  Tech stack: {', '.join(plan.get('tech_stack', []))}")
        print(f"  Files to create: {len(plan['files'])}")
        print(f"\n  File structure:")
        for file in plan['files']:
            indent = "    " + "  " * (file['path'].count('/'))
            print(f"    {indent}├── {file['path']}")
            print(f"    {indent}    └── {file['description']}")
    
    def generate_files(self, plan: dict) -> list:
        """Generate each file using GPT-OSS-20B"""
        generated_files = []
        
        for i, file_spec in enumerate(plan['files'], 1):
            print(f"\n  [{i}/{len(plan['files'])}] Generating {file_spec['path']}...")
            
            prompt = f"""Generate the complete file for:

Project: {plan['project_name']}
Description: {plan['description']}
Tech stack: {', '.join(plan.get('tech_stack', []))}
File path: {file_spec['path']}
File type: {file_spec['type']}
File purpose: {file_spec['description']}

Other files in project:
{self._format_other_files(plan['files'], file_spec)}

Generate COMPLETE, PRODUCTION-READY code.
Include all necessary imports, proper error handling, and comments.

Output ONLY the file content, no explanations."""
            
            content = self.generator.generate(prompt, max_tokens=4000, temperature=0.2)
            
            generated_files.append({
                'path': file_spec['path'],
                'description': file_spec['description'],
                'type': file_spec['type'],
                'content': content
            })
            
            print(f"  ✓ Generated {len(content)} chars")
        
        return generated_files
    
    def _format_other_files(self, all_files: list, current_file: dict) -> str:
        """Format other files for context"""
        others = [f for f in all_files if f['path'] != current_file['path']]
        return "\n".join([f"- {f['path']}: {f['description']}" for f in others])
    
    def write_files(self, generated_files: list):
        """Write generated files to disk"""
        for file in generated_files:
            filepath = self.output_dir / file['path']
            
            # Create directories if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(filepath, 'w') as f:
                f.write(file['content'])
            
            print(f"  ✓ Created {filepath}")
    
    def final_review(self, generated_files: list):
        """GPT-OSS-120B reviews the complete project"""
        files_summary = "\n".join([
            f"- {f['path']} ({len(f['content'])} chars)"
            for f in generated_files
        ])
        
        prompt = f"""Review this project structure:

Files created:
{files_summary}

Check:
1. Are all files complete?
2. Do they work together?
3. Any missing dependencies?
4. Any obvious bugs?

Provide brief feedback."""
        
        review = self.orchestrator.generate(prompt, max_tokens=1000, temperature=0.3)
        print(f"\n  Review: {review[:500]}...")
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

IMPORTANT: For full-stack applications, ALWAYS include:
- Frontend files (HTML, CSS, JS)
- Backend files (Python/Node)
- Config files (requirements.txt, package.json)
- README.md

Return ONLY valid JSON (no markdown, no explanations):
{{"project_name": "name", "description": "brief", "tech_stack": ["tech1", "tech2"], "files": [{{"path": "path/to/file", "description": "what it does", "type": "frontend/backend/config/docs"}}]}}

Be specific. Include 5-10 files for a full-stack app."""
        
        response = self.orchestrator.generate(prompt, max_tokens=2000, temperature=0.3)
        
        # Debug print
        print(f"  [debug] Raw response length: {len(response)}")
        print(f"  [debug] First 200 chars: {response[:200]}")
        
        # Better JSON extraction - try multiple methods
        import json
        import re
        
        # Method 1: Direct JSON parse
        try:
            return json.loads(response)
        except:
            pass
        
        # Method 2: Find JSON between { }
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        # Method 3: Find JSON array
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                files = json.loads(json_match.group())
                return {"project_name": "project", "files": files}
            except:
                pass
        
        print("  [warn] JSON parsing failed, using enhanced fallback")
        
        # Enhanced fallback for full-stack
        return {
            "project_name": "fullstack-app",
            "description": user_request,
            "tech_stack": ["python", "html", "css", "javascript"],
            "files": [
                {"path": "backend/main.py", "description": "Backend API server", "type": "backend"},
                {"path": "backend/requirements.txt", "description": "Python dependencies", "type": "config"},
                {"path": "frontend/index.html", "description": "Frontend HTML", "type": "frontend"},
                {"path": "frontend/style.css", "description": "Frontend styles", "type": "frontend"},
                {"path": "frontend/app.js", "description": "Frontend JavaScript", "type": "frontend"},
                {"path": "README.md", "description": "Project documentation", "type": "docs"}
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
        """Generate each file using GPT-OSS-20B with real-time display"""
        generated_files = []
        
        for i, file_spec in enumerate(plan['files'], 1):
            print(f"\n  [{i}/{len(plan['files'])}] Generating {file_spec['path']}...")
            print(f"  {'─'*50}")
            
            prompt = f"""Generate the complete code for this file:

Project: {plan['project_name']}
File: {file_spec['path']}
Type: {file_spec['type']}
Purpose: {file_spec['description']}

Output the COMPLETE file content. If this is code, include all imports and full implementation.
If this is documentation, write comprehensive docs.
Do NOT skip this file. Provide actual content."""
            
            # Stream generation - show content as it comes
            print(f"  📄 {file_spec['path']}")
            print(f"  {'─'*50}")
            
            content = self.generator.generate_stream(prompt, max_tokens=4000, temperature=0.2)
            
            # Check if empty
            if not content or len(content.strip()) == 0:
                print(f"  ⚠️ Empty response, retrying...")
                content = self.generator.generate(prompt, max_tokens=4000, temperature=0.3)
            
            if not content or len(content.strip()) == 0:
                print(f"  ⚠️ Still empty, creating placeholder")
                content = self._create_placeholder(file_spec)
            
            generated_files.append({
                'path': file_spec['path'],
                'description': file_spec['description'],
                'type': file_spec['type'],
                'content': content
            })
            
            print(f"\n  ✓ Generated {len(content)} chars")
        
        return generated_files

    def _create_placeholder(self, file_spec: dict) -> str:
        """Create placeholder content based on file type"""
        path = file_spec['path']
        
        if path.endswith('.py'):
            return f"""# {file_spec['description']}

def main():
    print("Hello from {path}")

if __name__ == "__main__":
    main()
"""
        elif path.endswith('.html'):
            return """<!DOCTYPE html>
<html>
<head>
    <title>Project</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <h1>Hello World</h1>
    <script src="app.js"></script>
</body>
</html>
"""
        elif path.endswith('.md'):
            return f"# {file_spec['description']}\n\nProject documentation placeholder.\n"
        else:
            return f"# {file_spec['description']}\n"

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

    def modify_project(self, modification_request: str):
        """Modify existing project based on user request"""
        print(f"\n{'='*60}")
        print(f"🔧 PROJECT MODIFICATION")
        print(f"Request: {modification_request}")
        print(f"{'='*60}\n")
        
        # Step 1: Analyze current project
        print("[1/3] 📊 Analyzing current project...")
        current_files = self._scan_project()
        
        if not current_files:
            print("  [error] No files found in current directory")
            return
        
        print(f"  Found {len(current_files)} files")
        for f in current_files[:10]:
            print(f"    - {f}")
        
        # Step 2: Plan modification
        print(f"\n[2/3] 🧠 Planning modifications...")
        plan = self._plan_modification(modification_request, current_files)
        
        print(f"\n  Changes to make:")
        for change in plan['changes']:
            print(f"    - {change['action']}: {change['file']}")
        
        # Step 3: Execute modifications
        print(f"\n[3/3] ⚡ Executing modifications...")
        self._execute_modifications(plan, current_files)
        
        print(f"\n{'='*60}")
        print(f"✅ MODIFICATION COMPLETE!")
        print(f"{'='*60}\n")
    
    def _scan_project(self) -> list:
        """Scan current directory for existing files"""
        files = []
        for root, dirs, filenames in os.walk('.'):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for filename in filenames:
                filepath = os.path.join(root, filename)
                files.append(filepath)
        return files
    
    def _plan_modification(self, request: str, current_files: list) -> dict:
        """Use GPT-OSS-120B to plan modifications"""
        files_summary = "\n".join(current_files[:20])
        
        prompt = f"""You are modifying an existing project.

Current files:
{files_summary}

Modification request: {request}

Plan the changes needed. Return JSON:
{{
    "changes": [
        {{
            "action": "modify/create/delete",
            "file": "path/to/file",
            "description": "what to change",
            "new_content": "complete new content if create/modify"
        }}
    ]
}}

Only include files that need changes. Be specific."""
        
        response = self.orchestrator.generate(prompt, max_tokens=3000, temperature=0.3)
        
        # Parse JSON
        import json
        import re
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except:
                pass
        
        return {"changes": []}
    
    def _execute_modifications(self, plan: dict, current_files: list):
        """Execute the planned modifications"""
        for i, change in enumerate(plan['changes'], 1):
            print(f"\n  [{i}/{len(plan['changes'])}] {change['action']}: {change['file']}")
            
            if change['action'] == 'create':
                # Generate new file
                prompt = f"""Create this new file for the project:

File: {change['file']}
Purpose: {change['description']}

Generate complete file content."""
                
                content = self.generator.generate_stream(prompt, max_tokens=3000)
                
                # Write file
                filepath = self.output_dir / change['file']
                filepath.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath, 'w') as f:
                    f.write(content)
                print(f"  ✓ Created {filepath}")
            
            elif change['action'] == 'modify':
                # Read existing file
                filepath = self.output_dir / change['file']
                if filepath.exists():
                    current_content = filepath.read_text()
                    
                    prompt = f"""Modify this existing file:

File: {change['file']}
Current content:
{current_content}

Change needed: {change['description']}

Output the COMPLETE new file content."""
                    
                    new_content = self.generator.generate_stream(prompt, max_tokens=4000)
                    
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    print(f"  ✓ Modified {filepath}")
                else:
                    print(f"  ⚠️ File not found: {change['file']}")
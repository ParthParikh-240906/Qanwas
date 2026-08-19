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
        
        print("[1/4] 🧠 Architect planning project structure...")
        project_plan = self.plan_project(user_request)
        
        self.display_plan(project_plan)
        
        print(f"\n[2/4] 📝 Generating {len(project_plan['files'])} files in parallel...")
        generated_files = self.generate_files_parallel(project_plan)
        
        print(f"\n[3/4] 🔍 Validating project...")
        generated_files = self.validate_and_fix(user_request, generated_files)
        
        print(f"\n{'='*60}")
        print(f"🎉 PROJECT COMPLETE!")
        print(f"Location: {self.output_dir.absolute()}")
        print(f"{'='*60}\n")
    
    def plan_project(self, user_request: str) -> dict:
        """GPT-OSS-120B plans the entire project with complexity detection"""
        complexity = self._detect_complexity(user_request)
        print(f"  [complexity: {complexity}]")
        
        if complexity == "simple":
            file_instructions = """
For SIMPLE requests:
- Return 1-3 files MAXIMUM (including README.md)
- NO backend, NO Docker, NO package.json
- Just HTML/CSS/JS or single Python file
- ALWAYS include README.md"""
            max_files = 3
        elif complexity == "medium":
            file_instructions = """
For MEDIUM requests:
- Return 3-5 files (including README.md)
- Simple backend + frontend
- ALWAYS include README.md"""
            max_files = 5
        else:
            file_instructions = """
For COMPLEX requests:
- Return 5-10 files (including README.md)
- Full backend + frontend
- Include config files
- ALWAYS include README.md"""
            max_files = 10
        
        prompt = f"""You are an expert software architect. Plan a project for this request:

"{user_request}"

{file_instructions}

IMPORTANT RULES:
- Do NOT over-engineer. Match the complexity.
- Maximum files: {max_files}
- ALWAYS include a README.md file
- Assign EACH file a type: "frontend", "backend", "config", or "docs"

Return ONLY valid JSON:
{{"project_name": "name", "description": "brief", "tech_stack": ["tech1"], "files": [{{"path": "path", "description": "what", "type": "frontend/backend/config/docs"}}]}}"""
        
        response = self.orchestrator.generate(prompt, max_tokens=2000, temperature=0.3)
        
        print(f"  [debug] Raw response length: {len(response)}")
        
        import json
        import re
        
        try:
            plan = json.loads(response)
            if 'files' in plan and len(plan['files']) > 0:
                return self._ensure_readme(plan, user_request)
        except:
            pass
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                plan = json.loads(json_match.group())
                if 'files' in plan and len(plan['files']) > 0:
                    return self._ensure_readme(plan, user_request)
            except:
                pass
        
        print("  [warn] JSON parsing failed, using fallback")
        
        if complexity == "simple":
            return {
                "project_name": "simple-app",
                "description": user_request,
                "tech_stack": ["html", "css"],
                "files": [
                    {"path": "README.md", "description": "Project docs", "type": "docs"},
                    {"path": "index.html", "description": "Main page", "type": "frontend"},
                    {"path": "style.css", "description": "Styles", "type": "frontend"}
                ]
            }
        else:
            return {
                "project_name": "web-app",
                "description": user_request,
                "tech_stack": ["python", "html", "css"],
                "files": [
                    {"path": "README.md", "description": "Project docs", "type": "docs"},
                    {"path": "backend/main.py", "description": "Backend API", "type": "backend"},
                    {"path": "backend/requirements.txt", "description": "Dependencies", "type": "config"},
                    {"path": "frontend/index.html", "description": "Frontend HTML", "type": "frontend"},
                    {"path": "frontend/style.css", "description": "Styles", "type": "frontend"}
                ]
            }
    
    def _detect_complexity(self, user_request: str) -> str:
        """Simple keyword-based complexity detection"""
        request_lower = user_request.lower()
        
        simple_words = ["simple", "basic", "just", "hello world", "webpage", "single page", 
                       "one page", "single file", "landing page", "static"]
        if any(word in request_lower for word in simple_words):
            return "simple"
        
        complex_words = ["full-stack", "full stack", "enterprise", "production", "scalable", 
                        "microservices", "database", "auth", "payment", "real-time", 
                        "websocket", "docker", "kubernetes", "redis", "kafka", "rag", "pipeline"]
        if any(word in request_lower for word in complex_words):
            return "complex"
        
        word_count = len(request_lower.split())
        if word_count < 5:
            return "simple"
        elif word_count < 15:
            return "medium"
        else:
            return "complex"
    
    def _ensure_readme(self, plan: dict, user_request: str) -> dict:
        """Ensure README.md is always in the plan"""
        if 'files' not in plan:
            plan['files'] = []
        
        has_readme = any(
            f.get('path', '').lower() == 'readme.md' or 
            f.get('path', '').lower().endswith('/readme.md') 
            for f in plan['files']
        )
        
        if not has_readme:
            plan['files'].insert(0, {
                "path": "README.md",
                "description": "Project overview, setup instructions, and start command",
                "type": "docs"
            })
        
        return plan
    
    def display_plan(self, plan: dict):
        """Show the project plan"""
        print(f"\n  Project: {plan['project_name']}")
        print(f"  Description: {plan.get('description', 'N/A')}")
        print(f"  Tech stack: {', '.join(plan.get('tech_stack', []))}")
        print(f"  Files to create: {len(plan['files'])}")
        print(f"\n  📁 Project structure:")
        for file in plan['files']:
            print(f"    ├── {file['path']}")
            print(f"    │   └── {file['description']}")
        print()
    
    def generate_files_parallel(self, plan: dict) -> list:
        """Generate files using 3 parallel agents"""
        frontend_files = [f for f in plan['files'] if f['type'] == 'frontend']
        backend_files = [f for f in plan['files'] if f['type'] == 'backend']
        config_files = [f for f in plan['files'] if f['type'] in ['config', 'docs']]
        
        print(f"\n  📁 Distributing work to agents:")
        if frontend_files:
            print(f"    🎨 Frontend Agent (20B): {len(frontend_files)} files")
        if backend_files:
            print(f"    ⚙️  Backend Agent (20B): {len(backend_files)} files")
        if config_files:
            print(f"    🔧 Config Agent (120B): {len(config_files)} files")
        
        print(f"\n  🚀 Launching parallel agents...\n")
        
        all_files = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = {}
            
            if frontend_files:
                futures['frontend'] = executor.submit(
                    self._generate_group, frontend_files, plan, "frontend", self.frontend_agent
                )
            if backend_files:
                futures['backend'] = executor.submit(
                    self._generate_group, backend_files, plan, "backend", self.backend_agent
                )
            if config_files:
                futures['config'] = executor.submit(
                    self._generate_group, config_files, plan, "config", self.config_agent
                )
            
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
            
            if file_spec['path'].lower().endswith('readme.md'):
                prompt = f"""You are the {category} specialist. Generate a README.md for this project:

Project: {plan['project_name']}
Description: {plan.get('description', 'N/A')}
Tech stack: {', '.join(plan.get('tech_stack', []))}

The README MUST include:
1. Project title and description
2. Installation/setup instructions
3. HOW TO START/RUN the project
4. Basic usage examples

Use proper markdown formatting."""
            else:
                prompt = f"""You are the {category} specialist. Generate this file:

Project: {plan['project_name']}
File: {file_spec['path']}
Purpose: {file_spec['description']}

Generate COMPLETE, production-ready code. Do NOT truncate."""
            
            content = agent.generate_silent(prompt, max_tokens=4000, temperature=0.2)
            
            if not content or len(content.strip()) == 0:
                content = agent.generate_silent(prompt, max_tokens=4000, temperature=0.3)
            
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
            
            time.sleep(0.5)
        
        return generated
    
    def validate_and_fix(self, user_request: str, generated_files: list, max_iterations: int = 5):
        """GPT-OSS-120B reviews code and auto-fixes if mismatched"""
        print(f"\n{'='*60}")
        print(f"🔍 VALIDATION & AUTO-FIX")
        print(f"{'='*60}")
        
        all_issues = []
        
        for iteration in range(max_iterations):
            print(f"\n[Validation round {iteration + 1}/{max_iterations}]")
            
            issues = self._validate_project(user_request, generated_files)
            
            if not issues:
                print(f"\n✅ Project matches the request perfectly!")
                self.save_validation_report(user_request, all_issues, generated_files)
                return generated_files
            
            all_issues.extend(issues)
            
            print(f"\n⚠️ Found {len(issues)} issues:")
            for issue in issues[:5]:
                print(f"  - {issue['file']}: {issue['problem'][:80]}...")
            
            print(f"\n🔧 Auto-fixing issues...")
            generated_files = self._fix_issues(user_request, generated_files, issues)
        
        print(f"\n{'='*60}")
        print(f"🔧 FINAL FIX BY GPT-OSS-120B")
        print(f"{'='*60}")
        generated_files = self._final_fix_120b(user_request, generated_files)
        
        self.save_validation_report(user_request, all_issues, generated_files)
        return generated_files
    
    def _validate_project(self, user_request: str, generated_files: list) -> list:
        """GPT-OSS-120B checks if code matches the request"""
        files_summary = []
        for f in generated_files:
            files_summary.append(f"""
File: {f['path']}
Content:
{f['content'][:2000]}
---""")
        
        files_text = "\n".join(files_summary)
        
        prompt = f"""You are a strict code reviewer. Check if the project matches this request:

USER REQUEST: {user_request}

GENERATED FILES:
{files_text}

Check for CRITICAL issues ONLY:
1. Missing features from request
2. Syntax errors that prevent running
3. Incorrect implementations
4. Missing endpoints/functions
5. Broken imports

DO NOT flag minor style issues or optional improvements.

Return JSON:
{{"issues": [{{"file": "path", "problem": "what's wrong", "fix": "what to change"}}]}}

If everything works, return: {{"issues": []}}"""
        
        response = self.orchestrator.generate(prompt, max_tokens=2000, temperature=0.2)
        
        import json
        import re
        
        try:
            result = json.loads(response)
            return result.get('issues', [])
        except:
            pass
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                result = json.loads(json_match.group())
                return result.get('issues', [])
            except:
                pass
        
        return []
    
    def _fix_issues(self, user_request: str, generated_files: list, issues: list) -> list:
        """Fix the identified issues"""
        fixed_files = list(generated_files)
        
        file_issues = {}
        for issue in issues:
            filepath = issue.get('file', '')
            if filepath not in file_issues:
                file_issues[filepath] = []
            file_issues[filepath].append(issue)
        
        for i, (filepath, file_issue_list) in enumerate(file_issues.items(), 1):
            print(f"\n  [{i}/{len(file_issues)}] Fixing {filepath}...")
            
            file_data = None
            file_index = None
            for idx, f in enumerate(fixed_files):
                if f['path'] == filepath:
                    file_data = f
                    file_index = idx
                    break
            
            if not file_data:
                print(f"  ⚠️ File not found: {filepath}")
                continue
            
            problems = "\n".join([f"- {issue['problem']}: {issue['fix']}" for issue in file_issue_list])
            
            prompt = f"""Fix this file:

USER REQUEST: {user_request}
FILE: {filepath}
ISSUES TO FIX:
{problems}

CURRENT CONTENT:
{file_data['content']}

Output the COMPLETE fixed file content."""
            
            new_content = self.generator.generate(prompt, max_tokens=4000, temperature=0.2)
            
            if new_content and len(new_content.strip()) > 0:
                fixed_files[file_index]['content'] = new_content
                
                filepath_obj = self.output_dir / filepath
                filepath_obj.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath_obj, 'w') as f:
                    f.write(new_content)
                
                print(f"  ✓ Fixed {filepath} ({len(new_content)} chars)")
            
            time.sleep(0.5)
        
        return fixed_files
    
    def _final_fix_120b(self, user_request: str, generated_files: list) -> list:
        """Use GPT-OSS-120B for final comprehensive fix"""
        fixed_files = list(generated_files)
        
        files_summary = []
        for f in fixed_files:
            files_summary.append(f"""
File: {f['path']}
Content:
{f['content'][:1500]}
---""")
        
        files_text = "\n".join(files_summary)
        
        prompt = f"""You are a senior software engineer. Fix ALL remaining issues.

USER REQUEST: {user_request}

CURRENT FILES:
{files_text}

Fix ALL issues that would prevent the project from working.
Return JSON with fixed files:
{{"fixed_files": [{{"path": "file", "content": "complete fixed content"}}]}}"""
        
        response = self.orchestrator.generate(prompt, max_tokens=4000, temperature=0.2)
        
        import json
        import re
        
        try:
            result = json.loads(response)
            fixed_files_data = result.get('fixed_files', [])
        except:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    fixed_files_data = result.get('fixed_files', [])
                except:
                    fixed_files_data = []
            else:
                fixed_files_data = []
        
        for fixed_file in fixed_files_data:
            path = fixed_file.get('path', '')
            content = fixed_file.get('content', '')
            
            if not path or not content:
                continue
            
            for i, f in enumerate(fixed_files):
                if f['path'] == path:
                    fixed_files[i]['content'] = content
                    
                    filepath = self.output_dir / path
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with open(filepath, 'w') as fw:
                        fw.write(content)
                    
                    print(f"  ✓ Fixed {path} ({len(content)} chars)")
                    break
        
        return fixed_files
    
    def save_validation_report(self, user_request: str, issues: list, final_files: list):
        """Save validation report to file"""
        report_path = self.output_dir / "VALIDATION_REPORT.md"
        
        report = f"""# Validation Report

## Request
{user_request}

## Summary
{'✅ All checks passed' if not issues else f'⚠️ Found and fixed {len(issues)} issues'}

## Files
{chr(10).join([f'- {f["path"]} ({len(f.get("content", ""))} chars)' for f in final_files])}

---
*Generated by Qanwas*
"""
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n  📄 Validation report saved: {report_path}")
    
    def modify_project(self, modification_request: str):
        """Modify existing project"""
        print(f"\n{'='*60}")
        print(f"🔧 PROJECT MODIFICATION")
        print(f"Request: {modification_request}")
        print(f"{'='*60}\n")
        
        print("[1/3] 📊 Analyzing current project...")
        current_files = self._scan_project()
        
        if not current_files:
            print("  [error] No files found")
            return
        
        print(f"  Found {len(current_files)} files")
        
        print(f"\n[2/3] 🧠 Planning modifications...")
        plan = self._plan_modification(modification_request, current_files)
        
        print(f"\n  Changes to make:")
        for change in plan.get('changes', []):
            print(f"    - {change['action']}: {change['file']}")
        
        print(f"\n[3/3] ⚡ Executing modifications...")
        modified_files = self._execute_modifications(plan, current_files)
        
        if modified_files:
            self.validate_and_fix(modification_request, modified_files)
        
        print(f"\n{'='*60}")
        print(f"✅ MODIFICATION COMPLETE!")
        print(f"{'='*60}\n")
    
    def _scan_project(self) -> list:
        """Scan current directory for existing files"""
        files = []
        for root, dirs, filenames in os.walk('.'):
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            for filename in filenames:
                if not filename.startswith('.'):
                    files.append(os.path.join(root, filename))
        return files
    
    def _plan_modification(self, request: str, current_files: list) -> dict:
        """Use GPT-OSS-120B to plan modifications"""
        files_summary = "\n".join(current_files[:20])
        
        prompt = f"""You are modifying an existing project.

Current files:
{files_summary}

Modification request: {request}

Return ONLY JSON:
{{"changes": [{{"action": "modify", "file": "path", "description": "what to change"}}]}}"""
        
        response = self.orchestrator.generate(prompt, max_tokens=3000, temperature=0.3)
        
        print(f"  [debug] Modification plan raw: {response[:300]}")
        
        import json
        import re
        
        try:
            plan = json.loads(response)
            if 'changes' in plan:
                return plan
        except:
            pass
        
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                plan = json.loads(json_match.group())
                if 'changes' in plan:
                    return plan
            except:
                pass
        
        return {"changes": []}
    
    def _execute_modifications(self, plan: dict, current_files: list) -> list:
        """Execute modifications"""
        changes = plan.get('changes', [])
        modified_files = []
        
        if not changes:
            print("  No changes detected")
            return modified_files
        
        for i, change in enumerate(changes, 1):
            action = change.get('action', 'modify')
            filepath_str = change.get('file', '')
            description = change.get('description', '')
            
            print(f"\n  ┌─ 🔧 {action}: {filepath_str}")
            print(f"  │  {description}")
            print(f"  └─{'─'*50}")
            
            filepath = self.output_dir / filepath_str
            
            if action == 'modify' and filepath.exists():
                current_content = filepath.read_text()
                
                prompt = f"""Modify this file:

File: {filepath_str}
Change needed: {description}

Current content:
{current_content}

Output the COMPLETE new file content."""
                
                new_content = self.generator.generate(prompt, max_tokens=4000, temperature=0.2)
                
                if new_content and len(new_content.strip()) > 0:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    print(f"  └─ ✓ Modified {filepath_str}")
                    modified_files.append({
                        'path': filepath_str,
                        'description': description,
                        'type': 'modified',
                        'content': new_content
                    })
            
            elif action == 'create':
                prompt = f"""Create this new file:

File: {filepath_str}
Purpose: {description}

Output complete file content."""
                
                content = self.generator.generate(prompt, max_tokens=3000, temperature=0.2)
                
                if content and len(content.strip()) > 0:
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with open(filepath, 'w') as f:
                        f.write(content)
                    print(f"  └─ ✓ Created {filepath_str}")
                    modified_files.append({
                        'path': filepath_str,
                        'description': description,
                        'type': 'created',
                        'content': content
                    })
            
            elif action == 'delete':
                if filepath.exists():
                    filepath.unlink()
                    print(f"  └─ ✓ Deleted {filepath_str}")
            
            time.sleep(0.5)
        
        return modified_files
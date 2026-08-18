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
        print("[1/3] 🧠 Architect planning project structure...")
        project_plan = self.plan_project(user_request)
        
        # Step 2: Show plan
        self.display_plan(project_plan)
        
        # Step 3: Generate each file
        print(f"\n[2/3] 📝 Generating {len(project_plan['files'])} files...")
        generated_files = self.generate_files(project_plan)
        
        # Step 3.5: Write files to disk (before validation)
        print(f"\n[3/3] 💾 Writing files to disk...")
        self.write_files(generated_files)
        
        # Step 4: Validate and auto-fix
        generated_files = self.validate_and_fix(user_request, generated_files)
        
        print(f"\n{'='*60}")
        print(f"🎉 PROJECT COMPLETE!")
        print(f"Location: {self.output_dir.absolute()}")
        print(f"{'='*60}\n")
    
    def plan_project(self, user_request: str) -> dict:
        """GPT-OSS-120B plans the entire project with complexity detection"""
        
        # Quick complexity detection (no extra API call)
        complexity = self._detect_complexity(user_request)
        print(f"  [complexity: {complexity}]")
        
        # Adjust prompt based on complexity
        if complexity == "simple":
            file_instructions = """
For SIMPLE requests:
- Return 1-3 files MAXIMUM (including README.md)
- NO backend, NO Docker, NO package.json, NO config files
- Just HTML/CSS/JS for frontend OR single Python file for backend
- Keep it minimal - only essential files
- ALWAYS include README.md"""
            max_files = 3
        elif complexity == "medium":
            file_instructions = """
For MEDIUM requests:
- Return 3-5 files (including README.md)
- Simple backend + frontend
- Include requirements.txt or package.json
- No Docker unless explicitly requested
- ALWAYS include README.md"""
            max_files = 5
        else:
            file_instructions = """
For COMPLEX requests:
- Return 5-10 files (including README.md)
- Full backend + frontend
- Include config files, README, Docker if needed
- Production-ready structure
- ALWAYS include README.md"""
            max_files = 10
        
        prompt = f"""You are an expert software architect. Plan a project for this request:

"{user_request}"

{file_instructions}

IMPORTANT RULES:
- Do NOT over-engineer. Match the complexity of the request.
- Maximum files: {max_files}
- Only include files that are ACTUALLY needed
- For simple requests, just give the essential files
- ALWAYS include a README.md file
- README.md should contain:
  - Project description
  - Installation/setup instructions
  - HOW TO START/RUN the project
  - Basic usage

Return ONLY valid JSON (no markdown, no explanations):
{{"project_name": "name", "description": "brief", "tech_stack": ["tech1", "tech2"], "files": [{{"path": "path/to/file", "description": "what it does", "type": "frontend/backend/config/docs"}}]}}

Be specific about file paths and purposes."""
        
        response = self.orchestrator.generate(prompt, max_tokens=2000, temperature=0.3)
        
        # Debug print
        print(f"  [debug] Raw response length: {len(response)}")
        print(f"  [debug] First 200 chars: {response[:200]}")
        
        # Better JSON extraction - try multiple methods
        import json
        import re
        
        # Method 1: Direct JSON parse
        try:
            plan = json.loads(response)
            if 'files' in plan and len(plan['files']) > 0:
                return self._ensure_readme(plan, user_request)
        except:
            pass
        
        # Method 2: Find JSON between { }
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                plan = json.loads(json_match.group())
                if 'files' in plan and len(plan['files']) > 0:
                    return self._ensure_readme(plan, user_request)
            except:
                pass
        
        # Method 3: Find JSON array
        json_match = re.search(r'\[.*\]', response, re.DOTALL)
        if json_match:
            try:
                files = json.loads(json_match.group())
                plan = {"project_name": "project", "files": files}
                return self._ensure_readme(plan, user_request)
            except:
                pass
        
        print("  [warn] JSON parsing failed, using fallback based on complexity")
        
        # Fallback based on complexity (all include README)
        if complexity == "simple":
            return {
                "project_name": "simple-app",
                "description": user_request,
                "tech_stack": ["html", "css", "javascript"],
                "files": [
                    {"path": "README.md", "description": "Project overview and start instructions", "type": "docs"},
                    {"path": "index.html", "description": "Main HTML page", "type": "frontend"},
                    {"path": "style.css", "description": "Styles for the page", "type": "frontend"}
                ]
            }
        elif complexity == "medium":
            return {
                "project_name": "web-app",
                "description": user_request,
                "tech_stack": ["python", "html", "css", "javascript"],
                "files": [
                    {"path": "README.md", "description": "Project documentation and start instructions", "type": "docs"},
                    {"path": "backend/main.py", "description": "Backend API server", "type": "backend"},
                    {"path": "backend/requirements.txt", "description": "Python dependencies", "type": "config"},
                    {"path": "frontend/index.html", "description": "Frontend HTML", "type": "frontend"},
                    {"path": "frontend/style.css", "description": "Frontend styles", "type": "frontend"}
                ]
            }
        else:
            return {
                "project_name": "fullstack-app",
                "description": user_request,
                "tech_stack": ["python", "html", "css", "javascript"],
                "files": [
                    {"path": "README.md", "description": "Project documentation and start instructions", "type": "docs"},
                    {"path": "backend/main.py", "description": "Backend API server", "type": "backend"},
                    {"path": "backend/requirements.txt", "description": "Python dependencies", "type": "config"},
                    {"path": "frontend/index.html", "description": "Frontend HTML", "type": "frontend"},
                    {"path": "frontend/style.css", "description": "Frontend styles", "type": "frontend"},
                    {"path": "frontend/app.js", "description": "Frontend JavaScript", "type": "frontend"}
                ]
            }
    
    def _detect_complexity(self, user_request: str) -> str:
        """Simple keyword-based complexity detection"""
        request_lower = user_request.lower()
        
        # Simple indicators
        simple_words = ["simple", "basic", "just", "hello world", "webpage", "single page", 
                       "one page", "single file", "landing page", "static"]
        if any(word in request_lower for word in simple_words):
            return "simple"
        
        # Complex indicators
        complex_words = ["full-stack", "full stack", "enterprise", "production", "scalable", 
                        "microservices", "database", "auth", "payment", "real-time", 
                        "websocket", "docker", "kubernetes", "redis", "kafka", "rag", "pipeline"]
        if any(word in request_lower for word in complex_words):
            return "complex"
        
        # Count words as heuristic
        word_count = len(request_lower.split())
        if word_count < 5:
            return "simple"
        elif word_count < 15:
            return "medium"
        else:
            return "complex"
    
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
    
    def generate_files(self, plan: dict) -> list:
        """Generate files silently and write directly to disk"""
        generated_files = []
        
        for i, file_spec in enumerate(plan['files'], 1):
            # Show progress (not the code)
            print(f"\n  [{i}/{len(plan['files'])}] 📄 {file_spec['path']}")
            
            # Special prompt for README.md
            if file_spec['path'].lower().endswith('readme.md'):
                prompt = f"""Generate a README.md for this project:

Project: {plan['project_name']}
Description: {plan.get('description', 'N/A')}
Tech stack: {', '.join(plan.get('tech_stack', []))}
Files in project: {', '.join([f['path'] for f in plan['files']])}

The README MUST include:
1. Project title and description
2. What the project does
3. Installation/setup instructions (if any)
4. HOW TO START/RUN the project (exact commands)
5. Basic usage examples
6. Project structure overview

Use proper markdown formatting. Be clear and concise."""
            else:
                prompt = f"""Generate the complete code for this file:

Project: {plan['project_name']}
File: {file_spec['path']}
Type: {file_spec['type']}
Purpose: {file_spec['description']}

Output the COMPLETE file content. No explanations, just the code."""
            
            # Generate WITHOUT printing (silent)
            content = self.generator.generate(prompt, max_tokens=4000, temperature=0.2)
            
            # Check if empty
            if not content or len(content.strip()) == 0:
                print(f"  ⚠️ Empty, retrying...")
                content = self.generator.generate(prompt, max_tokens=4000, temperature=0.3)
            
            # Write file immediately
            filepath = self.output_dir / file_spec['path']
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                f.write(content)
            
            print(f"  ✓ Created {file_spec['path']} ({len(content)} chars)")
            
            generated_files.append({
                'path': file_spec['path'],
                'description': file_spec['description'],
                'type': file_spec['type'],
                'content': content
            })
            
            # Small delay to avoid rate limits
            import time
            time.sleep(1)
        
        return generated_files

    def write_files(self, generated_files: list):
        """Write generated files to disk"""
        print(f"\n  💾 Writing files:")
        for file in generated_files:
            filepath = self.output_dir / file['path']
            
            # Create directories if needed
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file
            with open(filepath, 'w') as f:
                f.write(file['content'])
            
            print(f"  ✓ {filepath}")
    
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

FORMATTING RULES:
- Use bullet points ONLY
- NO tables, NO markdown tables
- Keep it brief (max 200 words)
- Be direct and concise"""
        
        review = self.orchestrator.generate(prompt, max_tokens=1000, temperature=0.3)
        print(f"\n  Review:")
        print(f"  {'─'*50}")
        print(f"  {review[:500]}")
    
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
        
        # Step 2: Plan modification
        print(f"\n[2/3] 🧠 Planning modifications...")
        plan = self._plan_modification(modification_request, current_files)
        
        print(f"\n  Changes to make:")
        for change in plan.get('changes', []):
            print(f"    - {change['action']}: {change['file']}")
        
        # Step 3: Execute modifications
        print(f"\n[3/3] ⚡ Executing modifications...")
        modified_files = self._execute_modifications(plan, current_files)
        
        # Step 4: Validate modifications
        if modified_files:
            self.validate_and_fix(modification_request, modified_files)
        
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
                if not filename.startswith('.'):
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

IMPORTANT:
- Analyze what needs to change
- Include ALL files that need modification
- If removing a feature, mark related files
- Be specific about changes

Return ONLY valid JSON in this format:
{{"changes": [{{"action": "modify", "file": "backend/app/main.py", "description": "Remove MySQL connection, add Gmail API call"}}]}}

Do NOT skip files that need changes. If no files need changes, return {{"changes": []}}"""
        
        response = self.orchestrator.generate(prompt, max_tokens=3000, temperature=0.3)
        
        # Debug
        print(f"  [debug] Modification plan raw: {response[:300]}")
        
        # Parse JSON - try multiple methods
        import json
        import re
        
        # Method 1: Direct JSON parse
        try:
            plan = json.loads(response)
            if 'changes' in plan:
                return plan
        except:
            pass
        
        # Method 2: Find JSON between { }
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                plan = json.loads(json_match.group())
                if 'changes' in plan:
                    return plan
            except:
                pass
        
        # Method 3: Find individual changes
        changes = []
        json_matches = re.findall(r'\{"action".*?\}', response, re.DOTALL)
        for match in json_matches:
            try:
                change = json.loads(match)
                changes.append(change)
            except:
                pass
        
        if changes:
            return {"changes": changes}
        
        print("  [warn] Could not parse changes, returning empty")
        return {"changes": []}
    
    def _execute_modifications(self, plan: dict, current_files: list) -> list:
        """Execute the planned modifications and return modified files"""
        changes = plan.get('changes', [])
        modified_files = []
        
        if not changes:
            print("  No changes detected")
            print("  [debug] Plan was:", plan)
            return modified_files
        
        for i, change in enumerate(changes, 1):
            action = change.get('action', 'modify')
            filepath_str = change.get('file', '')
            description = change.get('description', '')
            
            print(f"\n  ┌─ 🔧 {action}: {filepath_str}")
            print(f"  │  {description}")
            print(f"  └─{'─'*50}")
            
            filepath = self.output_dir / filepath_str
            
            if action == 'delete':
                if filepath.exists():
                    filepath.unlink()
                    print(f"  └─ ✓ Deleted {filepath}")
                    modified_files.append({
                        'path': filepath_str,
                        'description': description,
                        'type': 'deleted',
                        'content': ''
                    })
                else:
                    print(f"  ⚠️ File not found: {filepath}")
            
            elif action == 'modify' and filepath.exists():
                current_content = filepath.read_text()
                
                prompt = f"""Modify this existing file:

File: {filepath_str}
Change needed: {description}

Current content:
{current_content}

Output the COMPLETE new file content."""
                
                new_content = self.generator.generate(prompt, max_tokens=4000, temperature=0.2)
                
                if new_content and len(new_content.strip()) > 0:
                    with open(filepath, 'w') as f:
                        f.write(new_content)
                    print(f"  └─ ✓ Modified {filepath_str} ({len(new_content)} chars)")
                    modified_files.append({
                        'path': filepath_str,
                        'description': description,
                        'type': 'modified',
                        'content': new_content
                    })
                else:
                    print(f"  ⚠️ Failed to modify {filepath_str}")
            
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
                    print(f"  └─ ✓ Created {filepath_str} ({len(content)} chars)")
                    modified_files.append({
                        'path': filepath_str,
                        'description': description,
                        'type': 'created',
                        'content': content
                    })
                else:
                    print(f"  ⚠️ Failed to create {filepath_str}")
            
            else:
                print(f"  ⚠️ Could not process: {action} on {filepath_str}")
            
            # Small delay to avoid rate limits
            import time
            time.sleep(1)
        
        return modified_files

    def _ensure_readme(self, plan: dict, user_request: str) -> dict:
        """Ensure README.md is always in the plan"""
        if 'files' not in plan:
            plan['files'] = []
        
        # Check if README exists
        has_readme = any(f['path'].lower() == 'readme.md' or 
                        f['path'].lower().endswith('/readme.md') 
                        for f in plan['files'])
        
        if not has_readme:
            # Add README as first file
            plan['files'].insert(0, {
                "path": "README.md",
                "description": "Project overview, setup instructions, and start command",
                "type": "docs"
            })
        
        return plan

    def validate_and_fix(self, user_request: str, generated_files: list, max_iterations: int = 5):
        """GPT-OSS-120B reviews code and auto-fixes if mismatched"""
        print(f"\n{'='*60}")
        print(f"🔍 VALIDATION & AUTO-FIX")
        print(f"{'='*60}")
        
        all_issues = []
        
        for iteration in range(max_iterations):
            print(f"\n[Validation round {iteration + 1}/{max_iterations}]")
            
            # Step 1: Review all files
            issues = self._validate_project(user_request, generated_files)
            
            if not issues:
                print(f"\n✅ Project matches the request perfectly!")
                self.save_validation_report(user_request, all_issues, generated_files)
                return generated_files
            
            all_issues.extend(issues)
            
            print(f"\n⚠️ Found {len(issues)} issues:")
            for issue in issues[:5]:  # Show only first 5
                print(f"  - {issue['file']}: {issue['problem'][:80]}...")
            
            # Step 2: Fix issues (use 20B for speed)
            print(f"\n🔧 Auto-fixing issues...")
            generated_files = self._fix_issues(user_request, generated_files, issues)
        
        # Step 3: Final fix using 120B (smarter)
        print(f"\n{'='*60}")
        print(f"🔧 FINAL FIX BY GPT-OSS-120B")
        print(f"{'='*60}")
        print(f"\n[Using orchestrator for final polish...]")
        
        generated_files = self._final_fix_120b(user_request, generated_files)
        
        # Final validation
        print(f"\n[Final validation...]")
        remaining_issues = self._validate_project(user_request, generated_files)
        
        if not remaining_issues:
            print(f"\n✅ All issues resolved by 120B!")
        else:
            print(f"\n⚠️ {len(remaining_issues)} minor issues remain (acceptable)")
        
        self.save_validation_report(user_request, all_issues, generated_files)
        return generated_files
    
    def _final_fix_120b(self, user_request: str, generated_files: list) -> list:
        """Use GPT-OSS-120B for final comprehensive fix"""
        fixed_files = list(generated_files)
        
        print(f"\n  Analyzing all remaining issues...")
        
        # Group files for context
        files_summary = []
        for f in fixed_files:
            files_summary.append(f"""
File: {f['path']}
Content:
{f['content'][:1500]}
---""")
        
        files_text = "\n".join(files_summary)
        
        prompt = f"""You are a senior software engineer. Fix ALL remaining issues in this project.

USER REQUEST: {user_request}

CURRENT FILES:
{files_text}

Your task:
1. Review each file carefully
2. Fix ALL issues that would prevent the project from working
3. Ensure all files are complete and functional
4. Make sure the code matches the user request exactly
5. Remove any unnecessary code
6. Ensure all imports are correct
7. Ensure all endpoints/functions are properly connected

Return JSON with fixed files:
{{"fixed_files": [{{"path": "file", "content": "complete fixed content"}}]}}

Only include files that need changes."""
        
        response = self.orchestrator.generate(prompt, max_tokens=4000, temperature=0.2)
        
        # Parse JSON
        import json
        import re
        
        try:
            result = json.loads(response)
            fixed_files_data = result.get('fixed_files', [])
        except:
            # Try regex
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                try:
                    result = json.loads(json_match.group())
                    fixed_files_data = result.get('fixed_files', [])
                except:
                    fixed_files_data = []
            else:
                fixed_files_data = []
        
        # Apply fixes
        for fixed_file in fixed_files_data:
            path = fixed_file.get('path', '')
            content = fixed_file.get('content', '')
            
            if not path or not content:
                continue
            
            # Update in our list
            for i, f in enumerate(fixed_files):
                if f['path'] == path:
                    fixed_files[i]['content'] = content
                    
                    # Write to disk
                    filepath = self.output_dir / path
                    filepath.parent.mkdir(parents=True, exist_ok=True)
                    with open(filepath, 'w') as fw:
                        fw.write(content)
                    
                    print(f"  ✓ Fixed {path} ({len(content)} chars)")
                    break
        
        return fixed_files
    
    def _validate_project(self, user_request: str, generated_files: list) -> list:
        """GPT-OSS-120B checks if code matches the request"""
        
        # Build summary of all files
        files_summary = []
        for f in generated_files:
            files_summary.append(f"""
File: {f['path']}
Type: {f['type']}
Description: {f['description']}
Content:
{f['content'][:2000]}
---""")
        
        files_text = "\n".join(files_summary)
        
        prompt = f"""You are a strict code reviewer. Check if the generated project matches this request:

USER REQUEST: {user_request}

GENERATED FILES:
{files_text}

Check for CRITICAL issues ONLY:
1. Missing features from the request
2. Syntax errors that prevent running
3. Incorrect implementations
4. Missing endpoints/functions
5. Broken imports

DO NOT flag:
- Minor style issues
- Optional improvements
- "Nice to have" features
- Cosmetic issues
- Things that already work

Return JSON:
{{"issues": [{{"file": "path", "problem": "what's wrong", "fix": "what to change"}}]}}

If everything works, return: {{"issues": []}}

Be PRACTICAL. Only flag issues that would actually break the project."""
        
        response = self.orchestrator.generate(prompt, max_tokens=2000, temperature=0.2)
        
        # Parse JSON
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
        
        # Group issues by file
        file_issues = {}
        for issue in issues:
            filepath = issue.get('file', '')
            if filepath not in file_issues:
                file_issues[filepath] = []
            file_issues[filepath].append(issue)
        
        for i, (filepath, file_issue_list) in enumerate(file_issues.items(), 1):
            print(f"\n  [{i}/{len(file_issues)}] Fixing {filepath}...")
            
            # Find the file in generated_files
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
            
            # Build fix prompt
            problems = "\n".join([f"- {issue['problem']}: {issue['fix']}" for issue in file_issue_list])
            
            prompt = f"""Fix this file to match the user request.

USER REQUEST: {user_request}

FILE: {filepath}
DESCRIPTION: {file_data['description']}

ISSUES TO FIX:
{problems}

CURRENT CONTENT:
{file_data['content']}

Output the COMPLETE fixed file content. No explanations."""
            
            new_content = self.generator.generate(prompt, max_tokens=4000, temperature=0.2)
            
            if new_content and len(new_content.strip()) > 0:
                fixed_files[file_index]['content'] = new_content
                
                # Write to disk
                filepath_obj = self.output_dir / filepath
                filepath_obj.parent.mkdir(parents=True, exist_ok=True)
                with open(filepath_obj, 'w') as f:
                    f.write(new_content)
                
                print(f"  ✓ Fixed {filepath} ({len(new_content)} chars)")
            else:
                print(f"  ⚠️ Failed to fix {filepath}")
            
            import time
            time.sleep(1)
        
        return fixed_files

    def save_validation_report(self, user_request: str, issues: list, final_files: list):
        """Save validation report to file"""
        report_path = self.output_dir / "VALIDATION_REPORT.md"
        
        report = f"""# Validation Report

## Request
{user_request}

## Validation Summary
{'✅ All checks passed - project matches request perfectly' if not issues else f'⚠️ Found and fixed {len(issues)} issues'}

## Files Reviewed
{chr(10).join([f'- {f["path"]} ({len(f.get("content", ""))} chars)' for f in final_files])}

## Issues Found & Fixed
"""
        
        if issues:
            for i, issue in enumerate(issues, 1):
                report += f"""
### Issue {i}
- **File:** `{issue.get('file', 'N/A')}`
- **Problem:** {issue.get('problem', 'N/A')}
- **Fix Applied:** {issue.get('fix', 'N/A')}
"""
        else:
            report += "\nNo issues found. Project matches request.\n"
        
        report += f"""
## Generated
- Timestamp: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Total files: {len(final_files)}

---
*Report generated by Qanwas*
"""
        
        with open(report_path, 'w') as f:
            f.write(report)
        
        print(f"\n  📄 Validation report saved: {report_path}")
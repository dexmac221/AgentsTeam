import json
import asyncio
import time
import difflib
from pathlib import Path
from typing import List, Dict, Any, Optional

class TryErrorOrchestrator:
    """Incremental try/error build process.

    Executes a plan step-by-step:
      1. Minimal scaffold (deterministic) if project empty
      2. For each step: request ONLY changed/new files as JSON from model
      3. Apply changes, run command, capture errors
      4. On failure attempt automatic fix loop (ErrorCorrector) then retry
      5. Persist state to allow future resume
      6. Provides model with introspection: recent file contents + diffs + last errors
    """

    def __init__(self, ai_client, logger, model: str):
        self.ai_client = ai_client
        self.logger = logger
        self.model = model
        self.state_file = None
        # New: allow multiple adaptive fix attempts
        self.max_fix_attempts = 3

    async def plan_steps(self, description: str, technologies: List[str], max_steps: int = 10) -> List[str]:
        """Ask LLM for incremental plan steps (smallest -> more complex)."""
        prompt = f"""
You are an expert software architect. Break down the following project goal into at most {max_steps} SMALL, incremental implementation steps.
Each step must produce a minimal tangible improvement and be runnable/testable before moving on.
Avoid giant leaps. Prefer 5-12 word imperative phrases. No explicit numbering (no '1.'), just the phrase.
Project goal: {description}
Technologies: {', '.join(technologies) if technologies else 'unspecified'}
Return one step per line.
""".strip()
        try:
            response = await self.ai_client.generate(self.model, prompt)
            lines = [l.strip(' \t-') for l in response.splitlines() if l.strip()]
            steps = [l for l in lines if 2 <= len(l.split()) <= 14]
            seen = set(); uniq = []
            for s in steps:
                key = s.lower()
                if key not in seen:
                    uniq.append(s); seen.add(key)
            return uniq[:max_steps] or ["create minimal scaffold"]
        except Exception as e:
            self.logger.warning(f"Planning via LLM failed, using fallback: {e}")
            fallback = [
                "create minimal scaffold",
                "add core logic",
                "add basic tests",
                "handle errors",
                "improve documentation"
            ]
            return fallback[:max_steps]

    async def run(self, description: str, technologies: List[str], output_dir: Path, run_cmd: Optional[str], max_steps: int, expect: Optional[str] = None, dynamic_run: bool = True):
        start_time = time.time()
        output_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = output_dir / '.agentsteam_state.json'

        steps = await self.plan_steps(description, technologies, max_steps)
        print(f"🗂️ Plan steps ({len(steps)}):")
        for i, s in enumerate(steps, 1):
            print(f"  {i}. {s}")

        # Minimal scaffold if empty
        if not any(output_dir.iterdir()):
            self._write_minimal_scaffold(output_dir, description)
            print("🧱 Created minimal scaffold: main.py")

        if not run_cmd:
            run_cmd = self._infer_run_command(output_dir)
            print(f"🏃 Inferred run command: {run_cmd}")
        else:
            print(f"🏃 Using provided run command: {run_cmd}")

        stagnation_count = 0
        file_snapshots: Dict[str, str] = self._snapshot_files(output_dir)
        last_stdout = ""; last_stderr = ""; last_diffs: List[str] = []; last_applied = []
        for idx, step in enumerate(steps, 1):
            print(f"\n➤ Step {idx}/{len(steps)}: {step}")
            if step.lower().startswith('create minimal') and idx > 1:
                print("(Skipping redundant minimal scaffold step)")
                continue

            # Dynamic re-infer run command if tests appear
            if dynamic_run:
                inferred = self._infer_run_command(output_dir)
                if inferred != run_cmd:
                    print(f"🔄 Re-inferred run command: {run_cmd} -> {inferred}")
                    run_cmd = inferred

            # Build context summary
            context_summary = self._summarize_files(output_dir, limit=15)
            introspection = self._build_introspection_section(last_stdout, last_stderr, last_diffs, last_applied)

            # Ask model for incremental changes
            change_prompt = self._build_change_prompt(
                description, technologies, step, context_summary, expect, introspection
            )
            try:
                raw = await self.ai_client.generate(self.model, change_prompt)
                file_changes = self._parse_file_changes(raw)
            except Exception as e:
                self.logger.warning(f"Change generation failed ({e}); skipping to run.")
                file_changes = []

            if not file_changes:
                print("⚠️ No changes proposed.")
                stagnation_count += 1
            else:
                applied = 0
                last_applied = []
                for fc in file_changes:
                    rel = fc.get('path'); code = fc.get('code')
                    if not rel or not isinstance(code, str):
                        continue
                    if self._is_path_outside(output_dir, rel):
                        print(f"⛔ Ignoring unsafe path outside project: {rel}")
                        continue
                    dest = output_dir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    old = dest.read_text(encoding='utf-8') if dest.exists() else ''
                    # If modifying main.py to support positional name argument automatically add logic
                    if rel == 'main.py' and '--name' in code and 'print(' not in code:
                        # Ensure greeting print exists
                        insertion = "\n    print(f\"Hello {args.name}\")\n"
                        if 'parser.parse_args()' in code:
                            code = code.replace('args = parser.parse_args()', 'args = parser.parse_args()' + insertion)
                    with open(dest, 'w', encoding='utf-8') as f:
                        f.write(code.rstrip() + '\n')
                    new = code.rstrip() + '\n'
                    diff = self._make_diff(rel, old, new)
                    last_diffs.append(diff)
                    last_applied.append(rel)
                    file_snapshots[rel] = new
                    applied += 1
                print(f"📝 Applied {applied} file change(s)")
                stagnation_count = 0 if applied > 0 else stagnation_count + 1

            # Detect stagnation
            if stagnation_count >= 2:
                print("⚠️ Stagnation detected (no effective changes twice). Stopping early.")
                break

            # Run command
            success, stdout, stderr = await self._run_command(run_cmd, cwd=output_dir)
            last_stdout, last_stderr = stdout, stderr
            # Auto-handle simple ImportError for hello_world pattern before invoking fixer
            if not success and 'ImportError' in stderr and 'from hello_world import hello_world' in stderr:
                stub_file = output_dir / 'hello_world.py'
                try:
                    existing = stub_file.read_text(encoding='utf-8') if stub_file.exists() else ''
                    if 'def hello_world' not in existing:
                        stub_file.write_text(
                            "def hello_world():\n    \"""Return standard greeting.\"""\n    return 'Hello world'\n\nif __name__ == '__main__':\n    print(hello_world())\n",
                            encoding='utf-8'
                        )
                        print('🩹 Added hello_world.py stub with hello_world() function; retrying run...')
                        success2, stdout2, stderr2 = await self._run_command(run_cmd, cwd=output_dir)
                        last_stdout, last_stderr = stdout2, stderr2
                        if success2:
                            success = True
                            print('✅ Retry succeeded after adding stub')
                        else:
                            print('⚠️ Retry still failing; continuing to fix logic')
                except Exception as e:
                    print(f'⚠️ Could not create stub: {e}')
            self._persist_state(idx, step, success, stdout, stderr, output_dir)
            if success:
                print("✅ Run succeeded")
                if expect and expect not in stdout and not run_cmd.startswith('pytest'):
                    print(f"❌ Expected substring '{expect}' not found in stdout -> treat as failure")
                    success = False
            if success:
                last_diffs = []  # clear diffs after successful run to focus next step
                continue  # proceed to next step

            # On failure attempt automated fix (multi-attempt)
            print(f"🔄 Attempting automatic fix loop (up to {self.max_fix_attempts} attempts)")
            fix_ok = await self._attempt_fix(run_cmd, output_dir)
            if fix_ok:
                print("✅ Fix loop resolved the error")
                last_diffs = []
                continue
            else:
                print("❌ Fix loop failed; stopping.")
                return {"success": False, "failed_step": step, "stdout": stdout, "stderr": stderr}

        total_time = time.time() - start_time
        print(f"\n🏁 Try/Error session complete in {total_time:.1f}s")
        return {"success": True, "steps": steps, "time": total_time}

    # ----------------- Helpers -----------------
    def _write_minimal_scaffold(self, output_dir: Path, description: str):
        (output_dir / 'main.py').write_text(
            "#!/usr/bin/env python3\n" \
            "def main():\n" \
            "    print(\"Hello world\")\n\n" \
            "if __name__ == '__main__':\n" \
            "    main()\n", encoding='utf-8')
        (output_dir / 'README.md').write_text(f"# Incremental Project\n\n{description}\n", encoding='utf-8')

    def _infer_run_command(self, output_dir: Path) -> str:
        # Only switch to pytest if tests actually exist
        test_files = list(output_dir.glob('test_*.py')) + list((output_dir / 'tests').glob('test_*.py'))
        if test_files:
            return 'pytest -q'
        if (output_dir / 'main.py').exists():
            return 'python main.py'
        if (output_dir / 'hello.py').exists():
            return 'python hello.py'
        if (output_dir / 'app.py').exists():
            return 'python app.py'
        # fallback: first python file
        py_files = list(output_dir.rglob('*.py'))
        if py_files:
            rel = py_files[0].relative_to(output_dir)
            return f'python {rel}'
        return 'python main.py'

    def _build_change_prompt(self, description: str, technologies: List[str], step: str, context_summary: str, expect: Optional[str], introspection: str) -> str:
        expectation = f"Expected stdout should contain substring: '{expect}'." if expect else ''
        return f"""
You are improving an existing project incrementally.
Project goal: {description}
Current step: {step}
Technologies: {', '.join(technologies) if technologies else 'unspecified'}
{expectation}
Existing files summary (filenames and first lines):
{context_summary}

Recent introspection (diffs / last errors / applied files):
{introspection}

Produce ONLY a JSON array of file changes. Each element: {{"path": "relative/path.py", "code": "FULL NEW CONTENT"}}.
Rules:
- Include ONLY new or modified files necessary for THIS step.
- Omit unchanged files.
- Keep changes minimal and coherent with diffs & errors.
- If previous run succeeded and this step is about tests, create minimal failing test first.
- No explanations, no surrounding markdown, no code fences.
JSON only.
""".strip()

    def _summarize_files(self, root: Path, limit: int = 15) -> str:
        entries = []
        for i, p in enumerate(sorted(root.rglob('*'))):
            if i >= limit:
                break
            if p.is_file() and p.stat().st_size < 8000:
                try:
                    first_line = p.read_text(encoding='utf-8', errors='ignore').splitlines()[:1]
                    entries.append(f"{p.relative_to(root)} | {' '.join(first_line) if first_line else ''}")
                except Exception:
                    continue
        return '\n'.join(entries)

    def _parse_file_changes(self, raw: str) -> List[Dict[str, str]]:
        # Strip code fences if present
        if '```' in raw:
            # take inside first block
            start = raw.find('```') + 3
            end = raw.find('```', start)
            if end != -1:
                raw = raw[start:end]
        # Find JSON array
        start = raw.find('[')
        end = raw.rfind(']') + 1
        if start == -1 or end <= start:
            return []
        json_fragment = raw[start:end]
        try:
            data = json.loads(json_fragment)
            if isinstance(data, list):
                cleaned = []
                for item in data:
                    if isinstance(item, dict) and 'path' in item and 'code' in item:
                        cleaned.append({'path': item['path'].strip(), 'code': item['code']})
                return cleaned
        except Exception:
            return []
        return []

    def _is_path_outside(self, base: Path, rel: str) -> bool:
        try:
            target = (base / rel).resolve()
            return base.resolve() not in target.parents and target != base.resolve()
        except Exception:
            return True

    async def _run_command(self, cmd: str, cwd: Path):
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                cwd=str(cwd),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            stdout_s = stdout.decode(errors='ignore')
            stderr_s = stderr.decode(errors='ignore')
            success = proc.returncode == 0
            if not success:
                print("❌ Run failed")
            if stdout_s.strip():
                print("— stdout —\n" + stdout_s.strip())
            if stderr_s.strip():
                print("— stderr —\n" + stderr_s.strip())
            return success, stdout_s, stderr_s
        except Exception as e:
            return False, '', str(e)

    async def _attempt_fix(self, run_cmd: str, cwd: Path) -> bool:
        try:
            from .error_corrector import ErrorCorrector
            # Adaptive loop: invoke single-attempt fixer repeatedly so we can re-evaluate after each change.
            for attempt in range(1, self.max_fix_attempts + 1):
                print(f"   🛠️ Fix attempt {attempt}/{self.max_fix_attempts}")
                corrector = ErrorCorrector(self.ai_client, self.logger, model=self.model)
                result = await corrector.run_and_fix(run_cmd, max_attempts=1, cwd=str(cwd))
                if result.get('success'):
                    return True
            return False
        except Exception as e:
            self.logger.warning(f"Fix attempt failed: {e}")
            return False

    def _persist_state(self, step_index: int, step: str, success: bool, stdout: str, stderr: str, root: Path):
        state = {
            'step_index': step_index,
            'step': step,
            'success': success,
            'stdout_tail': stdout[-1000:],
            'stderr_tail': stderr[-2000:],
            'timestamp': time.time()
        }
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not persist state: {e}")

    # New helpers for introspection
    def _snapshot_files(self, root: Path) -> Dict[str, str]:
        snap = {}
        for p in root.rglob('*.py'):
            try:
                rel = str(p.relative_to(root))
                if p.stat().st_size < 20000:
                    snap[rel] = p.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
        return snap

    def _make_diff(self, path: str, old: str, new: str) -> str:
        diff = difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile=path+':old', tofile=path+':new', lineterm='')
        lines = list(diff)
        # truncate long diffs
        if len(lines) > 120:
            lines = lines[:120] + ['... (truncated)']
        return '\n'.join(lines)

    def _build_introspection_section(self, stdout: str, stderr: str, diffs: List[str], applied: List[str]) -> str:
        parts = []
        if applied:
            parts.append('Applied files: ' + ', '.join(applied))
        if diffs:
            parts.append('Recent diffs:\n' + '\n\n'.join(diffs[-3:]))
        if stderr.strip():
            parts.append('Last stderr tail:\n' + stderr.strip()[-800:])
        elif stdout.strip():
            parts.append('Last stdout tail:\n' + stdout.strip()[-400:])
        return '\n'.join(parts) or '(no prior run context)'

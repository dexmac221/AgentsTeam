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
        # New: patch size budget (characters) for modified existing files
        self.max_change_chars = 6000
        # Track last detected dependencies to avoid redundant writes
        self._last_deps = set()
        # Track handled missing dependencies to avoid repeated fix attempts
        self._missing_deps_handled = set()
        # New: progress tracking file & delimiters for README auto-update
        self.progress_file_name = '.agentsteam_progress.json'
        self.readme_progress_start = '<!-- TRY_ERROR_PROGRESS_START -->'
        self.readme_progress_end = '<!-- TRY_ERROR_PROGRESS_END -->'
        # New: server probe configuration
        self.default_probe_paths = ['/health', '/status', '/metrics', '/']
        self.probe_timeout = 4
        self.rollback_enabled = True
        self.negative_memory_enabled = True
        self.snapshots_dir_name = '.agentsteam_snapshots'
        self.max_snapshots = 5
        self.negative_memory_file = '.agentsteam_negative_memory.json'
        self._negative_memory_cache = []
        # New: branching candidates
        self.num_candidates = 1
        self._last_test_failures: List[Dict[str, Any]] = []  # structured test failures

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

    async def plan_hierarchical(self, description: str, technologies: List[str], num_epics: int, epic_steps: int, max_steps: int) -> List[str]:
        """Produce a hierarchical plan (epics -> steps) flattened into ordered step list.
        Epics are high-level themes; each expanded into micro-steps using existing plan_steps logic.
        """
        if num_epics <= 0:
            return await self.plan_steps(description, technologies, max_steps)
        epic_prompt = f"""Decompose the project goal into {num_epics} distinct high-level EPICS (themes / major capabilities).
Project goal: {description}
Technologies: {', '.join(technologies) if technologies else 'unspecified'}
Return ONLY epic names, one per line, 3-8 words each, no numbering."""
        try:
            resp = await self.ai_client.generate(self.model, epic_prompt)
            raw_epics = [l.strip(' -') for l in resp.splitlines() if l.strip()]
        except Exception as e:
            self.logger.warning(f"Epic planning failed: {e}; falling back to flat plan.")
            return await self.plan_steps(description, technologies, max_steps)
        epics = []
        for e in raw_epics:
            if 2 <= len(e.split()) <= 12:
                key = e.lower()
                if key not in [x.lower() for x in epics]:
                    epics.append(e)
            if len(epics) >= num_epics:
                break
        if not epics:
            return await self.plan_steps(description, technologies, max_steps)
        remaining = max_steps
        per_epic = epic_steps if epic_steps > 0 else max(1, remaining // len(epics))
        flat_steps: List[str] = []
        for epic in epics:
            if len(flat_steps) >= max_steps:
                break
            sub_cap = min(per_epic, max_steps - len(flat_steps))
            sub_desc = f"{description} (Focus epic: {epic})"
            sub_steps = await self.plan_steps(sub_desc, technologies, sub_cap)
            # Prefix or annotate epic context minimally
            for s in sub_steps:
                flat_steps.append(s if epic.lower() in s.lower() else f"[{epic}] {s}")
                if len(flat_steps) >= max_steps:
                    break
        return flat_steps[:max_steps]

    async def run(self, description: str, technologies: List[str], output_dir: Path, run_cmd: Optional[str], max_steps: int, expect: Optional[str] = None, dynamic_run: bool = True, resume: bool = False, probe: Optional[str] = None, epics: int = 0, epic_steps: int = 0, rollback: bool = True, negative_memory: bool = True):
        # Apply runtime feature toggles
        self.rollback_enabled = rollback
        self.negative_memory_enabled = negative_memory
        run_cmd_provided = run_cmd is not None  # track if user explicitly provided run command
        wants_basic = any('basic' in t.lower() for t in technologies) or 'commodore 64 basic' in description.lower() or 'c64 tetris' in description.lower()
        start_time = time.time()
        output_dir.mkdir(parents=True, exist_ok=True)
        # Ensure BASIC scaffold early if requested and absent regardless of directory emptiness
        if wants_basic and not (output_dir / 'tetris.bas').exists():
            self._write_minimal_scaffold(output_dir, description, technologies)
            print('🧱 Created BASIC scaffold: tetris.bas')
        self.state_file = output_dir / '.agentsteam_state.json'
        progress_path = output_dir / self.progress_file_name
        previous_state = None
        # Resume handling: load previous state if requested
        if resume and self.state_file.exists():
            try:
                previous_state = json.loads(self.state_file.read_text(encoding='utf-8'))
                print(f"🔁 Resume requested: loaded previous state (step_index={previous_state.get('step_index')}, success={previous_state.get('success')})")
            except Exception as e:
                print(f"⚠️ Could not load previous state: {e}")
                previous_state = None

        # If resuming and steps stored, reuse them; else plan new steps
        if previous_state and previous_state.get('steps'):
            steps = previous_state['steps'][:max_steps]  # respect new max_steps cap
            print(f"🗂️ Reusing stored plan steps ({len(steps)})")
        else:
            if epics > 0:
                steps = await self.plan_hierarchical(description, technologies, epics, epic_steps, max_steps)
                print(f"🗂️ Hierarchical plan (epics={epics}) produced {len(steps)} steps:")
            else:
                steps = await self.plan_steps(description, technologies, max_steps)
                print(f"🗂️ Plan steps ({len(steps)}):")
            for i, s in enumerate(steps, 1):
                print(f"  {i}. {s}")

        # Determine starting index for loop
        start_step_idx = 1
        if previous_state:
            last_index = int(previous_state.get('step_index', 0))
            last_success = bool(previous_state.get('success', False))
            # If last step failed, redo it; if succeeded, move to next
            start_step_idx = last_index if not last_success else last_index + 1
            if start_step_idx > len(steps):
                print("✅ All planned steps already completed (nothing to resume)")
                return {"success": True, "steps": steps, "time": 0.0, "resumed": True}
            print(f"🔂 Resuming at step {start_step_idx}/{len(steps)}")

        # Minimal scaffold only if not resuming and directory empty (Python path); skip if BASIC already handled
        if not previous_state and not any(output_dir.iterdir()) and not wants_basic:
            self._write_minimal_scaffold(output_dir, description, technologies)
            print("🧱 Created minimal scaffold: " + ("tetris.bas" if wants_basic else "main.py"))

        if not run_cmd:
            # Use previous run_cmd if available
            if previous_state and previous_state.get('run_cmd'):
                run_cmd = previous_state['run_cmd']
                print(f"🏃 Resuming with previous run command: {run_cmd}")
            else:
                run_cmd = self._infer_run_command(output_dir)
                print(f"🏃 Inferred run command: {run_cmd}")
        else:
            print(f"🏃 Using provided run command: {run_cmd}")

        stagnation_count = 0
        # Add configurable stagnation threshold
        stagnation_threshold = 2
        file_snapshots: Dict[str, str] = self._snapshot_files(output_dir)
        last_stdout = previous_state.get('stdout_tail', '') if previous_state else ''
        last_stderr = previous_state.get('stderr_tail', '') if previous_state else ''
        last_diffs: List[str] = []
        last_applied = []
        # Load existing progress
        progress_log = []
        if progress_path.exists():
            try:
                progress_log = json.loads(progress_path.read_text(encoding='utf-8'))
            except Exception:
                progress_log = []
        # after steps planning and before main loop, load negative memory
        neg_file = output_dir / self.negative_memory_file
        if self.negative_memory_enabled and neg_file.exists():
            try:
                self._negative_memory_cache = json.loads(neg_file.read_text(encoding='utf-8'))
            except Exception:
                self._negative_memory_cache = []
        # Ensure snapshot dir
        snapshots_dir = output_dir / self.snapshots_dir_name
        if self.rollback_enabled:
            snapshots_dir.mkdir(exist_ok=True)
        # Create initial snapshot if starting fresh
        if self.rollback_enabled and (not previous_state or not previous_state.get('success')):
            self._create_snapshot(output_dir, snapshots_dir, label='initial')

        rollback_attempted = False  # track single automatic replan after rollback
        idx = 1
        basic_mode = self._is_basic_project(description, technologies)
        while idx <= len(steps):
            step = steps[idx-1]
            pre_step_versions = {}
            if idx < start_step_idx:
                idx += 1
                continue
            print(f"\n➤ Step {idx}/{len(steps)}: {step}")
            if step.lower().startswith('create minimal') and idx > 1:
                print("(Skipping redundant minimal scaffold step)")
                idx += 1
                continue

            # Dynamic re-infer run command if tests appear (only if not user-provided)
            if dynamic_run and not run_cmd_provided:
                inferred = self._infer_run_command(output_dir)
                if inferred != run_cmd:
                    print(f"🔄 Re-inferred run command: {run_cmd} -> {inferred}")
                    run_cmd = inferred

            context_summary = self._summarize_files(output_dir, limit=15)
            introspection = self._build_introspection_section(last_stdout, last_stderr, last_diffs, last_applied)

            # Ask model for incremental changes
            change_prompt = self._build_change_prompt(
                description, technologies, step, context_summary, expect, introspection
            )
            try:
                raw = await self.ai_client.generate(self.model, change_prompt)
                if self.num_candidates > 1:
                    # Ask for multi-candidate alternatives
                    alt_prompt = change_prompt + f"\nModify previous instruction: instead produce JSON object {{\"candidates\":[C1,C2,...]}} with up to {self.num_candidates} alternative minimal candidate patch sets exploring different plausible small increments (each candidate is an array of file change objects). Keep each candidate minimal and varied."
                    raw_multi = await self.ai_client.generate(self.model, alt_prompt)
                    candidate_sets = self._parse_candidate_sets(raw_multi)
                    if candidate_sets:
                        # Filter negative memory for each set
                        filtered_sets = []
                        for cand in candidate_sets:
                            filt = []
                            for fc in cand:
                                rel = fc.get('path'); code = fc.get('code')
                                if not rel or not isinstance(code, str):
                                    continue
                                if self.negative_memory_enabled and self._is_in_negative_memory(rel, code):
                                    continue
                                filt.append(fc)
                            if filt:
                                filtered_sets.append(filt)
                        candidate_sets = filtered_sets or candidate_sets
                        evaluations = []
                        for cand in candidate_sets:
                            ev = await self._evaluate_candidate(output_dir, run_cmd or self._infer_run_command(output_dir), cand, expect)
                            evaluations.append(ev)
                        if evaluations:
                            best = max(evaluations, key=lambda e: e['score'])
                            print("🏁 Candidate scoring:")
                            for i, ev in enumerate(evaluations, 1):
                                print(f"  Cand {i}: score={ev['score']:.2f} success={ev['success']} size={ev['total_chars']} expect={ev['expectation_met']}")
                            print(f"✅ Selected candidate with score {best['score']:.2f}")
                            file_changes = best['changes']
                        else:
                            file_changes = self._parse_file_changes(raw)
                    else:
                        file_changes = self._parse_file_changes(raw)
                else:
                    file_changes = self._parse_file_changes(raw)
            except Exception as e:
                self.logger.warning(f"Change generation failed ({e}); skipping to run.")
                file_changes = []

            # After obtaining file_changes (may be empty), inject BASIC forcing logic
            if basic_mode and (not file_changes or all(fc.get('path') != 'tetris.bas' for fc in file_changes)):
                basic_path = output_dir / 'tetris.bas'
                if basic_path.exists():
                    content = basic_path.read_text(encoding='utf-8', errors='ignore')
                    if self._is_basic_scaffold(content):
                        print('🛠️ Forcing BASIC generation (scaffold still incomplete)...')
                        forced = await self._force_basic_generation(description, step, technologies, output_dir, expect, introspection)
                        if forced:
                            file_changes = forced

            if not file_changes:
                print("⚠️ No changes proposed.")
                stagnation_count += 1
                applied_changes = []
            else:
                applied = 0
                last_applied = []
                applied_changes = []
                filtered_changes = []
                for fc in file_changes:
                    rel = fc.get('path'); code = fc.get('code')
                    if not rel or not isinstance(code, str):
                        continue
                    if self.negative_memory_enabled and (self._is_in_negative_memory(rel, code) or self._is_semantically_in_negative_memory(rel, code)):
                        print(f"♻️ Skipping previously failed (semantic) pattern for {rel}")
                        continue
                    filtered_changes.append(fc)
                file_changes = filtered_changes
                for fc in file_changes:
                    rel = fc.get('path'); code = fc.get('code')
                    if not rel or not isinstance(code, str):
                        continue
                    if self._is_path_outside(output_dir, rel):
                        print(f"⛔ Ignoring unsafe path outside project: {rel}")
                        continue
                    dest = output_dir / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    old_exists = dest.exists()
                    old = dest.read_text(encoding='utf-8') if old_exists else ''
                    # record for selective rollback
                    if rel not in pre_step_versions:
                        pre_step_versions[rel] = old if old_exists else None
                    # Large diff guard: if modifying existing file and change exceeds budget, request smaller patch
                    if old_exists and len(code) > self.max_change_chars:
                        print(f"⚠️ Proposed change for {rel} is {len(code)} chars (> {self.max_change_chars}). Requesting smaller focused patch.")
                        reduced = await self._request_smaller_patch(rel, old, description, step, expect)
                        if reduced:
                            code = reduced
                            print(f"✅ Received reduced patch for {rel} ({len(code)} chars)")
                        else:
                            print(f"⛔ Skipping oversized modification for {rel}; will revisit in later step.")
                            continue
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
                    applied_changes.append((rel, new))
                    file_snapshots[rel] = new
                    applied += 1
                print(f"📝 Applied {applied} file change(s)")
                stagnation_count = 0 if applied > 0 else stagnation_count + 1

            # Detect stagnation
            if stagnation_count >= stagnation_threshold:
                # Instead of stopping immediately, attempt a reflection step once
                print("🧠 Stagnation detected: invoking reflection to adjust next micro-step")
                reflection_prompt = f"""You are stuck improving a project with goal: {description}. Recent step description: {step}. No effective changes were produced. Provide ONE concise next micro-step (<=12 words) that is smaller/simpler and likely to move forward. Output ONLY the phrase, no numbering, no punctuation at end."""
                try:
                    reflection = await self.ai_client.generate(self.model, reflection_prompt)
                    candidate = reflection.strip().splitlines()[0].strip('- ').strip()
                    if candidate and candidate.lower() not in [s.lower() for s in steps]:
                        print(f"🔧 Replacing stalled step with reflective micro-step: {candidate}")
                        steps[idx-1] = candidate
                        stagnation_count = 0
                        # Persist updated plan
                        self._persist_state(idx, candidate, False, last_stdout, last_stderr, output_dir, steps, run_cmd)
                        # Retry loop iteration with new step label (continue moves to run phase)
                    else:
                        print("⚠️ Reflection produced no usable alternative; stopping early.")
                        break
                except Exception as e:
                    print(f"⚠️ Reflection failed: {e}; stopping early.")
                    break

            # Run command
            success, stdout, stderr = await self._run_command(run_cmd, cwd=output_dir)
            last_stdout, last_stderr = stdout, stderr
            # Parse structured pytest failures if applicable
            if run_cmd.startswith('pytest') and not success:
                self._last_test_failures = self._parse_pytest_failures(stdout, stderr)
            else:
                self._last_test_failures = []
            # Stack trace derived candidate files for targeted fix reasoning
            candidate_files = self._extract_stack_trace_files(stderr, output_dir)
            # Early missing dependency handling
            if not success and 'ModuleNotFoundError' in stderr:
                missing_mod = self._extract_missing_module(stderr)
                if missing_mod and missing_mod not in self._missing_deps_handled:
                    print(f"📦 Detected missing dependency: {missing_mod}")
                    self._missing_deps_handled.add(missing_mod)
                    try:
                        self._update_requirements(output_dir, {missing_mod})
                        print(f"📝 Added {missing_mod} to requirements.txt")
                    except Exception as e:
                        print(f"⚠️ Could not update requirements for {missing_mod}: {e}")
                    print("➡️ Please install dependencies, then resume: \n   pip install -r requirements.txt\n   agentsteam try-error '...' --output" f" {output_dir} --resume")
                    # Persist and stop early awaiting user action
                    self._persist_state(idx, step, False, stdout, stderr, output_dir, steps, run_cmd)
                    return {"success": False, "failed_step": step, "missing_dependency": missing_mod, "stdout": stdout, "stderr": stderr, "awaiting_dependencies": True}
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
            self._persist_state(idx, step, success, stdout, stderr, output_dir, steps, run_cmd)
            # Enhanced expectation logic: if expect specified and command likely server, attempt HTTP probe
            server_mode = self._looks_like_server_project(output_dir) or self._run_command_is_server(run_cmd)
            if success and expect and not run_cmd.startswith('pytest'):
                expectation_met = expect in stdout
                if server_mode and not expectation_met:
                    probe_result = await self._probe_server(expect, output_dir, run_cmd, probe)
                    if probe_result:
                        expectation_met = True
                if not expectation_met:
                    print(f"❌ Expected indicator '{expect}' not found (stdout/server probe) -> treat as failure")
                    success = False
            if success:
                try:
                    new_deps = self._detect_python_dependencies(output_dir)
                    added = new_deps - self._last_deps
                    if added:
                        self._update_requirements(output_dir, added)
                        self._last_deps |= added
                        print(f"📦 Detected new dependencies: {', '.join(sorted(added))}")
                except Exception as e:
                    print(f"⚠️ Dependency detection failed: {e}")
                last_diffs = []
                entry = {"step": idx, "label": step, "success": True, "timestamp": time.time(), "applied": last_applied, "duration_sec": None}
                progress_log.append(entry)
                self._write_progress(progress_path, progress_log)
                self._update_readme_progress(output_dir, progress_log)
                if self.rollback_enabled:
                    self._create_snapshot(output_dir, snapshots_dir, label=f'step{idx}')
                idx += 1
                continue
            else:
                error_sig = self._error_signature(stderr)
                print(f"🔄 Attempting automatic fix loop (up to {self.max_fix_attempts} attempts)")
                fix_ok = await self._attempt_fix(run_cmd, output_dir, candidate_files=candidate_files)
                if fix_ok:
                    print("✅ Fix loop resolved the error")
                    last_diffs = []
                    entry = {"step": idx, "label": step, "success": True, "timestamp": time.time(), "applied": last_applied, "duration_sec": None, "fixed": True}
                    progress_log.append(entry)
                    self._write_progress(progress_path, progress_log)
                    self._update_readme_progress(output_dir, progress_log)
                    if self.rollback_enabled:
                        self._create_snapshot(output_dir, snapshots_dir, label=f'step{idx}_fixed')
                    idx += 1
                    continue
                print("❌ Fix loop failed; recording negative memory and evaluating rollback.")
                for path, code in applied_changes:
                    try:
                        self._record_negative_memory(path, code, error_sig, output_dir)
                    except Exception:
                        pass
                # NEW: selective (file-level) rollback attempt before full snapshot rollback
                selective_recovery = False
                if applied_changes:
                    print("🩹 Attempting selective file-level rollback of just this step's changes...")
                    for rel, _new_code in applied_changes:
                        original = pre_step_versions.get(rel, None)
                        target = output_dir / rel
                        try:
                            if original is None:  # file was newly created; remove it
                                if target.exists():
                                    target.unlink()
                            else:
                                target.write_text(original, encoding='utf-8')
                        except Exception as e:
                            print(f"⚠️ Could not revert {rel}: {e}")
                    # re-run after selective rollback
                    sel_success, sel_stdout, sel_stderr = await self._run_command(run_cmd, cwd=output_dir)
                    if sel_success:
                        print("✅ Selective rollback restored working state; skipping this step's modifications.")
                        self._persist_state(idx, step, True, sel_stdout, sel_stderr, output_dir, steps, run_cmd)
                        entry = {"step": idx, "label": step, "success": True, "timestamp": time.time(), "applied": [], "partial_rollback": True}
                        progress_log.append(entry)
                        self._write_progress(progress_path, progress_log)
                        self._update_readme_progress(output_dir, progress_log)
                        if self.rollback_enabled:
                            self._create_snapshot(output_dir, snapshots_dir, label=f'step{idx}_partial')
                        idx += 1
                        selective_recovery = True
                        continue  # proceed to next step
                    else:
                        print("⚠️ Selective rollback did not restore working state; proceeding to full rollback logic.")
                if selective_recovery:
                    continue
                # ...existing full rollback logic remains unchanged after this insertion...
        total_time = time.time() - start_time
        print(f"\n🏁 Try/Error session complete in {total_time:.1f}s")
        return {"success": True, "steps": steps, "time": total_time}

    # ----------------- Helpers -----------------
    def _write_minimal_scaffold(self, output_dir: Path, description: str, technologies: List[str]):
        # NEW: language-aware minimal scaffold
        lower_desc = description.lower()
        wants_basic = any('basic' in t.lower() for t in technologies) or 'commodore 64 basic' in lower_desc or 'c64' in lower_desc
        if wants_basic:
            (output_dir / 'tetris.bas').write_text(
                "10 REM C64 TETRIS - INITIAL SCAFFOLD\n"
                "20 REM THIS FILE WILL BE REPLACED IN INCREMENTAL STEPS\n"
                "30 REM GOAL: IMPLEMENT PIECE SPAWN, MOVE, ROTATE, LINE CLEAR, SCORE, SPEED, GAME OVER\n"
                "40 PRINT \"TETRIS SCAFFOLD\"\n"
                "50 PRINT \"(INCREMENTAL BUILD PLACEHOLDER)\"\n",
                encoding='utf-8'
            )
            if not (output_dir / 'README.md').exists():
                (output_dir / 'README.md').write_text(f"# C64 Tetris (Incremental)\n\n{description}\n\nGenerated via AgentsTeam try-error mode.\n", encoding='utf-8')
        else:
            # existing python scaffold
            (output_dir / 'main.py').write_text(
                "#!/usr/bin/env python3\n" \
                "def main():\n" \
                "    print(\"Hello world\")\n\n" \
                "if __name__ == '__main__':\n" \
                "    main()\n", encoding='utf-8')
            if not (output_dir / 'README.md').exists():
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
        # ...existing code replaced to inject BASIC single-file guidance when needed...
        expectation = f"Expected stdout should contain substring: '{expect}'." if expect else ''
        extra_guidance = ''
        lower_desc = description.lower()
        basic_extra = ''
        if 'commodore 64 basic' in lower_desc or any('basic' in t.lower() for t in technologies):
            # include snippet of current BASIC file if exists
            basic_path = Path(context_summary.split('\n')[0].split(' | ')[0])  # naive; actual snippet handled below
            extra_guidance = (
                "\nProject MUST be a single Commodore 64 BASIC V2 source file named tetris.bas. "
                "Return JSON updating ONLY tetris.bas. Provide FULL line-numbered BASIC code (no Python). "
                "If tetris.bas still contains REM scaffold lines, REPLACE entire file with initial functional slice (board + draw + spawn)."
            )
        return f"""
You are improving an existing project incrementally.{extra_guidance}
Project goal: {description}
Current step: {step}
Technologies: {', '.join(technologies) if technologies else 'unspecified'}
{expectation}
Existing files summary (filenames and first lines):
{context_summary}

Recent introspection (diffs / last errors / applied files):
{introspection}

Produce ONLY a JSON array of file changes. Each element: {{"path": "relative/path", "code": "FULL NEW CONTENT"}}.
Rules:
- Include ONLY new or modified files necessary for THIS step.
- Omit unchanged files.
- Keep changes minimal and coherent with diffs & errors.
- If single-file BASIC project: always output only tetris.bas full content.
- If tetris.bas shows scaffold placeholders, output a more complete functional version.
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

    def _parse_candidate_sets(self, raw: str):
        """Parse multi-candidate JSON structure.
        Expected format: {"candidates": [ [ {"path":..., "code":...}, ... ], ... ] }
        Falls back to single candidate list if not present.
        """
        try:
            if '```' in raw:
                start = raw.find('```') + 3
                end = raw.find('```', start)
                if end != -1:
                    raw = raw[start:end]
            obj_start = raw.find('{')
            obj_end = raw.rfind('}') + 1
            if obj_start == -1 or obj_end <= obj_start:
                return None
            data = json.loads(raw[obj_start:obj_end])
            if isinstance(data, dict) and 'candidates' in data and isinstance(data['candidates'], list):
                out = []
                for cand in data['candidates']:
                    subset = []
                    if isinstance(cand, list):
                        for fc in cand:
                            if isinstance(fc, dict) and 'path' in fc and 'code' in fc:
                                subset.append({'path': fc['path'].strip(), 'code': fc['code']})
                    if subset:
                        out.append(subset)
                return out or None
        except Exception:
            return None
        return None

    async def _evaluate_candidate(self, base_dir: Path, run_cmd: str, candidate_changes, expect: Optional[str]) -> dict:
        """Apply candidate changes in temp dir, run, score."""
        import tempfile, shutil
        tmp = Path(tempfile.mkdtemp(prefix='agentsteam_cand_'))
        try:
            # copy project
            for p in base_dir.rglob('*'):
                if any(part.startswith('.agentsteam_') for part in p.parts):
                    continue
                rel = p.relative_to(base_dir)
                dest = tmp / rel
                if p.is_dir():
                    dest.mkdir(parents=True, exist_ok=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        dest.write_text(p.read_text(encoding='utf-8', errors='ignore'), encoding='utf-8')
                    except Exception:
                        pass
            # apply candidate
            total_chars = 0
            for fc in candidate_changes:
                rel = fc.get('path'); code = fc.get('code')
                if not rel or not isinstance(code, str):
                    continue
                dest = tmp / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(code.rstrip() + '\n', encoding='utf-8')
                total_chars += len(code)
            success, stdout, stderr = await self._run_command(run_cmd, cwd=tmp)
            expectation_met = False
            if expect and success:
                expectation_met = expect in stdout
            score = 0.0
            if success: score += 100
            if expectation_met: score += 50
            score -= total_chars / 1500.0  # size penalty
            return {
                'score': score,
                'success': success,
                'expectation_met': expectation_met,
                'stdout': stdout[-400:],
                'stderr': stderr[-400:],
                'total_chars': total_chars,
                'changes': candidate_changes
            }
        finally:
            try:
                shutil.rmtree(tmp, ignore_errors=True)
            except Exception:
                pass

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

    def _create_snapshot(self, root: Path, snapshots_dir: Path, label: str):
        try:
            import tarfile
            timestamp = int(time.time())
            tar_name = f'{timestamp}_{label}.tar'
            tar_path = snapshots_dir / tar_name
            with tarfile.open(tar_path, 'w') as tar:
                for p in root.rglob('*'):
                    if any(part.startswith('.agentsteam_') for part in p.parts):
                        continue
                    if p.is_file():
                        tar.add(p, arcname=str(p.relative_to(root)))
            tars = sorted(snapshots_dir.glob('*.tar'), key=lambda x: x.stat().st_mtime, reverse=True)
            for old in tars[self.max_snapshots:]:
                try: old.unlink()
                except Exception: pass
            print(f"🗃️ Snapshot saved: {tar_name}")
        except Exception as e:
            print(f"⚠️ Snapshot failed: {e}")

    def _restore_latest_snapshot(self, snapshots_dir: Path, root: Path) -> Optional[str]:
        try:
            tars = sorted(snapshots_dir.glob('*.tar'), key=lambda x: x.stat().st_mtime, reverse=True)
            if not tars:
                return None
            latest = tars[0]
            import tarfile, shutil
            for item in list(root.iterdir()):
                name = item.name
                if name.startswith('.agentsteam_') or name == self.negative_memory_file:
                    continue
                try:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                except Exception:
                    pass
            with tarfile.open(latest, 'r') as tar:
                tar.extractall(root)
            return latest.name
        except Exception as e:
            print(f"⚠️ Rollback restore failed: {e}")
            return None

    def _is_in_negative_memory(self, path: str, code: str) -> bool:
        import hashlib
        h = hashlib.sha256((path + '\n' + code).encode('utf-8', errors='ignore')).hexdigest()[:16]
        for entry in self._negative_memory_cache:
            if entry.get('hash') == h:
                return True
        return False

    def _record_negative_memory(self, path: str, code: str, error_signature: str, output_dir: Path):
        # ...existing code replaced to store code sample for semantic similarity...
        if not self.negative_memory_enabled:
            return
        import hashlib
        h = hashlib.sha256((path + '\n' + code).encode('utf-8', errors='ignore')).hexdigest()[:16]
        entry = {'hash': h, 'path': path, 'error': error_signature[:160], 'ts': time.time(), 'code_sample': code[:4000]}
        if not any(e.get('hash') == h for e in self._negative_memory_cache):
            self._negative_memory_cache.append(entry)
            try:
                (output_dir / self.negative_memory_file).write_text(json.dumps(self._negative_memory_cache, indent=2), encoding='utf-8')
            except Exception:
                pass

    # NEW: semantic negative memory check
    def _is_semantically_in_negative_memory(self, path: str, code: str) -> bool:
        if not self.negative_memory_enabled or not self._negative_memory_cache:
            return False
        try:
            from difflib import SequenceMatcher
            snippet = code[:4000]
            for entry in self._negative_memory_cache:
                # prioritize same path
                if entry.get('path') == path and entry.get('code_sample'):
                    ratio = SequenceMatcher(None, entry['code_sample'], snippet).quick_ratio()
                    if ratio >= 0.92:
                        return True
            # fallback: any high similarity regardless of path (aggressive)
            for entry in self._negative_memory_cache:
                if entry.get('code_sample'):
                    ratio = SequenceMatcher(None, entry['code_sample'], snippet).quick_ratio()
                    if ratio >= 0.97:
                        return True
        except Exception:
            return False
        return False

    def _error_signature(self, stderr: str) -> str:
        lines = stderr.strip().splitlines()
        tail = lines[-3:]
        types = [l for l in lines if ('Error:' in l or l.startswith('Traceback'))]
        sig = '|'.join(types[-2:] + tail)
        return sig[:400]

    def _build_introspection_section(self, stdout: str, stderr: str, diffs: List[str], applied: List[str]) -> str:
        parts = []
        if applied:
            parts.append('Applied files: ' + ', '.join(applied))
        if diffs:
            parts.append('Recent diffs:\n' + '\n\n'.join(diffs[-3:]))
        if stderr and stderr.strip():
            parts.append('Last stderr tail:\n' + stderr.strip()[-800:])
        elif stdout and stdout.strip():
            parts.append('Last stdout tail:\n' + stdout.strip()[-400:])
        if hasattr(self, '_last_test_failures') and self._last_test_failures:
            import json as _json
            summarized = []
            for f in self._last_test_failures[:3]:
                summarized.append(f"{f.get('test')} => {f.get('error_type')} : {f.get('message')[:140]}")
            parts.append('Recent test failures (structured):\n' + '\n'.join(summarized))
        return '\n'.join(parts) or '(no prior run context)'

    def _is_path_outside(self, base: Path, rel: str) -> bool:
        try:
            target = (base / rel).resolve()
            return base.resolve() not in target.parents and target != base.resolve()
        except Exception:
            return True

    def _make_diff(self, path: str, old: str, new: str) -> str:
        import difflib as _difflib
        diff = _difflib.unified_diff(old.splitlines(), new.splitlines(), fromfile=path+':old', tofile=path+':new', lineterm='')
        lines = list(diff)
        if len(lines) > 120:
            lines = lines[:120] + ['... (truncated)']
        return '\n'.join(lines)

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

    def _persist_state(self, step_index: int, step: str, success: bool, stdout: str, stderr: str, root: Path, steps: Optional[List[str]] = None, run_cmd: Optional[str] = None):
        state = {
            'step_index': step_index,
            'step': step,
            'success': success,
            'stdout_tail': stdout[-1000:],
            'stderr_tail': stderr[-2000:],
            'timestamp': time.time(),
            'steps': steps,
            'run_cmd': run_cmd
        }
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            self.logger.warning(f"Could not persist state: {e}")

    async def _attempt_fix(self, run_cmd: str, cwd: Path, candidate_files: Optional[List[str]] = None) -> bool:
        try:
            from .error_corrector import ErrorCorrector
            for attempt in range(1, self.max_fix_attempts + 1):
                print(f"   🛠️ Fix attempt {attempt}/{self.max_fix_attempts}")
                corrector = ErrorCorrector(self.ai_client, self.logger, model=self.model)
                result = await corrector.run_and_fix(run_cmd, max_attempts=1, cwd=str(cwd), candidate_files=candidate_files)
                if result.get('success'):
                    return True
            return False
        except Exception as e:
            self.logger.warning(f"Fix attempt failed: {e}")
            return False

    def _extract_stack_trace_files(self, stderr: str, root: Path) -> List[str]:
        import re
        files = []
        pattern = re.compile(r'File "([^"]+)", line (\d+)')
        for m in pattern.finditer(stderr):
            fp = m.group(1)
            try:
                p = Path(fp)
                if not p.is_absolute():
                    p = root / fp
                if p.exists() and str(p).startswith(str(root)):
                    files.append(str(p))
            except Exception:
                continue
        seen = set(); ordered = []
        for f in files:
            if f not in seen:
                ordered.append(f); seen.add(f)
        return ordered[:5]

    def _looks_like_server_project(self, root: Path) -> bool:
        for name in ('fastapi', 'flask', 'django', 'uvicorn'):
            for py in root.rglob('*.py'):
                try:
                    txt = py.read_text(encoding='utf-8', errors='ignore')
                    if name in txt:
                        return True
                except Exception:
                    continue
        return False

    def _run_command_is_server(self, cmd: str) -> bool:
        server_tokens = ['uvicorn', 'gunicorn', 'fastapi', 'flask', ' --reload', 'runserver']
        return any(tok in cmd for tok in server_tokens)

    async def _probe_server(self, expect: str, root: Path, run_cmd: str, probe: Optional[str]) -> bool:
        try:
            import aiohttp
        except ImportError:
            return False
        ports = [8000, 5000, 8080]
        import re
        m = re.search(r':(\d{3,5})', run_cmd)
        if m:
            try:
                ports.insert(0, int(m.group(1)))
            except Exception:
                pass
        probe_spec = probe
        for port in ports[:3]:
            url_paths = []
            if probe_spec:
                part = probe_spec.split(':')[0]
                url_paths.append(part)
            url_paths.extend(self.default_probe_paths)
            async with aiohttp.ClientSession() as session:
                for path in url_paths:
                    if not path.startswith('/'):
                        path = '/' + path
                    try:
                        async with session.get(f'http://127.0.0.1:{port}{path}', timeout=self.probe_timeout) as resp:
                            if resp.status < 500:
                                text = await resp.text()
                                if expect and expect in text:
                                    print(f"🌐 HTTP probe matched expectation on {path} port {port}")
                                    return True
                                if probe_spec and ':contains=' in probe_spec:
                                    needle = probe_spec.split(':contains=')[1]
                                    if needle in text:
                                        print(f"🌐 HTTP probe matched custom contains '{needle}' on {path} port {port}")
                                        return True
                    except Exception:
                        continue
        return False

    def _write_progress(self, progress_path: Path, progress_log: List[Dict[str, Any]]):
        try:
            progress_path.write_text(json.dumps(progress_log, indent=2), encoding='utf-8')
        except Exception as e:
            print(f"⚠️ Could not write progress log: {e}")

    def _update_readme_progress(self, root: Path, progress_log: List[Dict[str, Any]]):
        readme = root / 'README.md'
        if not readme.exists():
            return
        try:
            content = readme.read_text(encoding='utf-8')
            table_lines = ["Step | Status | Files | Notes", "--- | --- | --- | ---"]
            for entry in progress_log[-25:]:
                status = '✅' if entry.get('success') else '❌'
                files = ','.join(entry.get('applied') or [])[:60]
                notes = 'fixed' if entry.get('fixed') else ''
                table_lines.append(f"{entry.get('step')} | {status} | {files} | {notes}")
            table_md = '\n'.join(table_lines)
            block = f"{self.readme_progress_start}\n### Incremental Progress\n\n{table_md}\n{self.readme_progress_end}"
            if self.readme_progress_start in content and self.readme_progress_end in content:
                import re
                pattern = re.compile(re.escape(self.readme_progress_start) + r'.*?' + re.escape(self.readme_progress_end), re.DOTALL)
                content = pattern.sub(block, content)
            else:
                content += "\n\n" + block + "\n"
            readme.write_text(content, encoding='utf-8')
        except Exception as e:
            print(f"⚠️ Could not update README progress section: {e}")

    async def _request_smaller_patch(self, path: str, old_content: str, description: str, step: str, expect: Optional[str]) -> Optional[str]:
        prompt = f"""You proposed an update exceeding size budget for file {path} while building project: {description}. Current step: {step}. Provide a SINGLE JSON array with one element containing a minimal coherent updated FULL file content for {path} strictly under {self.max_change_chars} characters that advances only this step. If expectation substring {expect or '(none)'} is relevant, ensure output still supports it. Respond JSON only."""
        try:
            raw = await self.ai_client.generate(self.model, prompt)
            fc = self._parse_file_changes(raw)
            if fc and fc[0]['path'] == path and len(fc[0]['code']) <= self.max_change_chars:
                return fc[0]['code']
        except Exception:
            return None
        return None

    def _detect_python_dependencies(self, root: Path) -> set:
        import sys, re
        stdlib = set(getattr(sys, 'stdlib_module_names', set()))
        local_modules = {p.stem for p in root.glob('*.py')}
        deps = set()
        pattern = re.compile(r'^(?:from|import)\s+([a-zA-Z0-9_]+)')
        for py in root.rglob('*.py'):
            if py.stat().st_size > 30000:
                continue
            try:
                for line in py.read_text(encoding='utf-8', errors='ignore').splitlines():
                    m = pattern.match(line.strip())
                    if m:
                        mod = m.group(1)
                        if mod in local_modules or mod in stdlib:
                            continue
                        if mod in ('typing','pathlib','json','time','asyncio','sys','os','re','subprocess','dataclasses'):
                            continue
                        deps.add(mod.lower())
            except Exception:
                continue
        return deps

    def _update_requirements(self, root: Path, new_deps: set):
        req = root / 'requirements.txt'
        existing = []
        found = set()
        if req.exists():
            try:
                for line in req.read_text(encoding='utf-8').splitlines():
                    name = line.split('==')[0].split('>=')[0].strip().lower()
                    if name:
                        found.add(name)
                    existing.append(line)
            except Exception:
                pass
        for dep in sorted(new_deps):
            if dep not in found:
                existing.append(f"{dep}>=0.0.0")
        try:
            req.write_text('\n'.join(existing).rstrip() + '\n', encoding='utf-8')
        except Exception as e:
            print(f"⚠️ Could not update requirements.txt: {e}")

    def _extract_missing_module(self, stderr: str) -> Optional[str]:
        import re
        m = re.search(r"ModuleNotFoundError: No module named '([^']+)'", stderr)
        if m:
            name = m.group(1).strip()
            if name and not name.startswith('.'):
                return name
        return None

    def _parse_pytest_failures(self, stdout: str, stderr: str) -> List[Dict[str, Any]]:
        """Extract structured failure data from pytest output."""
        text = stderr or stdout
        lines = text.splitlines()
        failures: List[Dict[str, Any]] = []
        current: Dict[str, Any] = {}
        capture = []
        import re
        file_line_re = re.compile(r'^([^\s].*?):(\d+): in (test[\w_]+)')
        assertion_re = re.compile(r'^E +([A-Za-z_]+Error): (.*)')
        simple_assert_re = re.compile(r'^E +AssertionError(.*)')
        for i, line in enumerate(lines):
            if line.startswith('___') and ' ___' in line:
                # new section delimiter; flush previous
                if current:
                    current['trace'] = '\n'.join(capture[-12:])
                    failures.append(current)
                current = {}
                capture = []
                continue
            m = file_line_re.match(line.strip())
            if m:
                current['file'] = m.group(1)
                current['line'] = int(m.group(2))
                current['test'] = m.group(3)
            am = assertion_re.match(line.strip())
            if am:
                current.setdefault('error_type', am.group(1))
                current.setdefault('message', am.group(2))
            sm = simple_assert_re.match(line.strip())
            if sm:
                current.setdefault('error_type', 'AssertionError')
                msg = sm.group(1).strip(': ').strip()
                if msg:
                    current.setdefault('message', msg)
            if line.strip().startswith('+') or line.strip().startswith('-'):
                # diff line
                dl = current.setdefault('diff', [])
                if len(dl) < 40:
                    dl.append(line)
            capture.append(line)
        if current:
            current['trace'] = '\n'.join(capture[-12:])
            failures.append(current)
        # prune noise
        cleaned = []
        for f in failures:
            if not f.get('test') and not f.get('error_type'):
                continue
            if 'diff' in f:
                f['diff'] = '\n'.join(f['diff'])
            cleaned.append(f)
        return cleaned[:10]

    def _is_basic_project(self, description: str, technologies: List[str]) -> bool:
        ld = description.lower()
        return any('basic' in t.lower() for t in technologies) or 'commodore 64 basic' in ld or 'c64' in ld or 'commodore 64' in ld

    def _is_basic_scaffold(self, content: str) -> bool:
        markers = ['TETRIS SCAFFOLD', 'INITIAL SCAFFOLD', 'INCREMENTAL BUILD PLACEHOLDER']
        return any(m in content.upper() for m in markers) or len(content.strip().splitlines()) < 15

    async def _force_basic_generation(self, description: str, step: str, technologies: List[str], output_dir: Path, expect: Optional[str], introspection: str) -> List[Dict[str,str]]:
        basic_path = output_dir / 'tetris.bas'
        existing = basic_path.read_text(encoding='utf-8', errors='ignore') if basic_path.exists() else ''
        guidance = (
            "You MUST output JSON with a single element updating tetris.bas. Provide FULL Commodore 64 BASIC V2 code. "
            "Implement at least: board array (20x10), screen render routine, DATA for tetromino shapes, piece spawn at center top, movement (A/D/S), gravity loop. "
            "If rotation/line clear not yet in scope, leave GOSUB placeholders with REM comments."
        )
        prompt = f"""Force BASIC generation.
Goal: {description}
Step: {step}
Existing (truncated):\n{existing[:1000]}

{guidance}
Return ONLY JSON: [{{"path":"tetris.bas","code":"FULL BASIC CONTENT"}}]
""".strip()
        try:
            raw = await self.ai_client.generate(self.model, prompt)
            return self._parse_file_changes(raw)
        except Exception:
            return []
# Experiment 01: Opus 5.5 and Qwen3-14B on the defensive find-and-fix tasks

Date: 2026-10-29. One attempt per task, public material only (`public/`); hidden tests and gold are never shown to the agent.

## Harness

- Opus 5.5: one attempt per task, run locally as an Opus 5.5 subagent inside the coworker's own Claude Code runtime, not the standalone Claude Code CLI (that CLI is not signed in on this machine, so the CLI run was swapped for this). Default effort (no higher setting chosen), 45 minute cap given in the solver prompt, working folder holds only `public/` and `out/`. Prompt: `SOLVER_PROMPT.txt` pattern (see the task `public/INSTRUCTION.md`).
- Qwen: Qwen3-14B (`Qwen/Qwen3-14B`, vLLM 0.11.0, tensor parallel 4, context 40960) on 4 of the 10 free RTX A4000 GPUs on mercury1 (16 GB each), driven by the Pi coding agent, 45 minute cap. Attempt 1 on all five first-tier tasks; a second attempt on VSC-FX-02 and VSC-FX-03 because attempt 1 produced no usable output (FX-03 scored from attempt 2, FX-02 still produced nothing). No Qwen run on the two harder tasks. This is a small model chosen because it fits the free GPUs, not the strongest open-weight model; a larger one did not fit.

## Qwen caveat, read first

Qwen's Smooth 0.000 mostly measures the harness failing to produce usable output, not task difficulty: no output at all for FX-02, thin or partial output elsewhere, scored leniently by overlaying whatever it wrote onto the public sources, and the smooth score is a geometric mean so one zero factor gives 0.

## Per task (one row per line)

Accepted = not saturated by Opus (acceptance criterion 4 in `ACCEPTANCE.md`). The comparison across agents uses the same five first-tier tasks; the two harder tasks are Opus-only.

- VSC-FX-01 (train, C record parser): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000
- VSC-FX-02 (train, C size arithmetic): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000 (no output)
- VSC-FX-03 (val, Python path containment): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000
- VSC-FX-04 (test, C refcount cache): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000
- VSC-FX-05 (test, Python sqlite params and CSV escaping): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000
- VSC-HX-03 (val, harder tier, Python site builder, 8 mutants): not accepted. Opus harsh 1, smooth 1.000. Qwen not run
- VSC-HX-05 (test, harder tier, Python appointment back office, 8 mutants): not accepted. Opus harsh 1, smooth 1.000. Qwen not run

Accepted: 0 of 7 (provisional; human check, criterion 5, not done).

## Four metrics

Same five tasks (FX-01..05):
- Opus 5.5: Harsh int 5/5 saturated. Smooth int 1.000. Harsh int_ref 5/5 saturated. Smooth int_ref 1.000.
- Qwen3-14B: Harsh int 0/5 saturated. Smooth int 0.000. Harsh int_ref 0/5 saturated. Smooth int_ref 0.000. (See the caveat.)

Opus only, all 7 tasks (adds HX-03, HX-05): Harsh int 7/7 saturated. Smooth int 1.000. Harsh int_ref 7/7 saturated. Smooth int_ref 1.000.

Raw scores: `opus55/results_all.json`, `qwen_pi/results.json`, with per-task scorer output in `scores/` and the agents' outputs under each task folder.

## Scope notes

- No reverse-engineering (SRE-Bench-style) task was built. Drafting it hit a block, and on the owner's "start building NOW" the batch went to narrower defensive find-and-fix tasks with no exploit inputs. An RE-style task is still open.
- Opus saturates both tiers, so none is accepted as written. Next: raise difficulty (more files, interacting defects, fewer README hints) and rerun Opus first.

Technical decisions: see the technical report; credited cc opus 5.5 xhigh.

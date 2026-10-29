# Experiment 01: Opus 5.5 and Qwen3-32B-AWQ on the defensive find-and-fix tasks

Date: 2026-10-29. One attempt per task on the same 7 tasks, 45 minute cap, public material only (`public/`); hidden tests and gold are never shown to the agent.

- Opus 5.5: default effort, run through an agent harness rather than the standalone CLI.
- Qwen3-32B-AWQ (open weight, the largest model that loaded on the free GPUs; the Qwen3-Coder-30B FP8 build fails to load with tensor parallel 4 on 16 GB cards: "output_size of gate's and up's weight = 192 is not divisible by weight quantization block_n = 128"): driven by the Pi coding agent, scored strictly with each task's own scorer on exactly what the model wrote, no overlay. Its 0.000 smooth scores come from partial patches that do not build, so they measure weak output as much as task difficulty. A second 32B run (`qwen32b_awq_pi/`, lenient overlay scoring) and an earlier Qwen3-14B run (`qwen_pi/`, 5 tasks) give the same verdict and are secondary.

## Per task (one row per line)

Accepted = not saturated by Opus (acceptance criterion 4 in `ACCEPTANCE.md`). Qwen reasons are from the strict run; all five factors are 0.00 on every task.

- VSC-FX-01 (train, C record parser): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000 (patched build failed)
- VSC-FX-02 (train, C size arithmetic): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000 (no output: named a nonexistent file and stopped)
- VSC-FX-03 (val, Python path containment): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000 (patched build failed, 0 of 3 mutants killed)
- VSC-FX-04 (test, C refcount cache): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000 (patched build failed)
- VSC-FX-05 (test, Python sqlite params and CSV escaping): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000 (patch had no `build.sh`)
- VSC-HX-03 (val, harder tier, Python site builder, 8 mutants): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000 (patched build failed, 0 of 8 mutants killed)
- VSC-HX-05 (test, harder tier, Python appointment back office, 8 mutants): not accepted. Opus harsh 1, smooth 1.000. Qwen harsh 0, smooth 0.000 (patch had no `build.sh`, 0 of 8 mutants killed)

Accepted: 0 of 7 (provisional; human check, criterion 5, not done).

## Four metrics, same 7 tasks

- Opus 5.5: Harsh int 7/7 saturated. Smooth int 1.000. Harsh int_ref 7/7 saturated. Smooth int_ref 1.000.
- Qwen3-32B-AWQ (strict): Harsh int 0/7 saturated. Smooth int 0.000. Harsh int_ref 0/7 saturated. Smooth int_ref 0.000.

Raw scores and model outputs: `opus55/`, `qwen32b_awq_pi_strict_mercury/` (headline), `qwen32b_awq_pi/`, `qwen_pi/`.

## Scope notes

- No reverse-engineering (SRE-Bench-style) task was built. Drafting it hit a block, and on the owner's "start building NOW" the batch went to narrower defensive find-and-fix tasks with no exploit inputs. An RE-style task is still open.
- Opus saturates both tiers, so none is accepted as written. Next: raise difficulty (more files, interacting defects, fewer README hints) and rerun Opus first.

Technical decisions: see the technical report; credited cc opus 5.5 xhigh.

# Experiment 01: Claude Code (Opus 5.5) and an open-weight model on the defensive find-and-fix tasks

Date: 2026-10-29. One attempt per task, default effort, public material only (`public/`), hidden tests/gold never shown to the agent.

## Accepted per task (acceptance rule in `ACCEPTANCE.md`, criterion 4: not saturated by a frontier agent)

One row per line. Accepted = 0 for every task as written: Claude Code with Opus 5.5 scored 1.0 on every factor, so the tasks are saturated.

- VSC-FX-01 (C record parser): not accepted (Opus harsh 1)
- VSC-FX-02 (C size arithmetic): not accepted (Opus harsh 1)
- VSC-FX-03 (Python path containment): not accepted (Opus harsh 1)
- VSC-FX-04 (C refcount cache): not accepted (Opus harsh 1)
- VSC-FX-05 (Python sqlite params / CSV escaping): not accepted (Opus harsh 1)
- VSC-HX-03 (harder tier, 8 mutants): not accepted (Opus harsh 1)
- VSC-HX-05 (harder tier, 8 mutants): not accepted (Opus harsh 1)

Accepted: 0 of 7 (provisional; criteria 1-3 pass, 5 human check not done).

## Four metrics

Claude Code, Opus 5.5 (7 tasks): Harsh int 7/7 saturated (harsh 1 on all), Smooth int 1.000, Harsh int_ref 7/7 saturated, Smooth int_ref 1.000.

Open-weight model, Pi harness, Qwen3-Coder-30B-A3B-Instruct (FP8) on free mercury1 GPUs (5 first-tier tasks; an earlier Qwen3-14B try is in the logs): Harsh int 0/5 saturated, Smooth int 0.000, Harsh int_ref 0/5 saturated, Smooth int_ref 0.000.

Note on the open-weight run: the smooth score is a geometric mean, so a single zero factor gives 0. Qwen mostly produced weak patches (they pass part of the reference tests on FX-01 and FX-04 but its own tests do not distinguish the original from the patch) and nothing for FX-02 (no `out/`). Scored leniently by overlaying whatever it wrote on the public sources (`qwen_pi/`). The open-weight harness run is a weak signal about task difficulty; it is real but low-quality.

## Reading

The frontier agent saturates both tiers, so the tasks need to get harder before any is accepted (more files, subtler interaction between defects, fewer hints in the public README). Next batch: raise difficulty, rerun Opus first.

Technical decisions: see the technical report; credited cc opus 5.5 xhigh.

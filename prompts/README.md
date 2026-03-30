# Prompts

Structured prompts used with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) for autonomous implementation of cheias.pt.

These documents serve as technical decision records and implementation guides. Each prompt captures the reasoning, constraints, and acceptance criteria for a specific phase of the project. They are preserved here as process documentation — showing not just what was built, but how and why.

## Reading order

1. `creative-direction-plan-v2.md` — Architecture decisions with evidence from production geospatial repos
2. `phase-0-vite-port.md` → `phase-1-data-layers.md` — Build phases
3. `P2-A-core-systems.md` → `P2-B-chapters.md` — Chapter implementation
4. `how-to-load-data-to-eoapi.md` — Data pipeline operations guide

## What these are

Each prompt was given to Claude Code as a complete implementation brief. The prompts define scope boundaries ("What NOT to do"), specify exact file paths and data formats, and include verification steps. This workflow enabled rapid, high-quality iteration on a complex geospatial project.

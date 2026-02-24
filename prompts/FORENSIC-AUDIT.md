# FORENSIC AUDIT: Design Intent vs. Delivered Product

## Why this audit exists

The cheias.pt QA review (QA-DIAGNOSTICS.md) revealed that every chapter has significant visualization failures. This is not about finding individual bugs. This is about understanding how a detailed, prescriptive design document produced a build that contradicts its own narrative at multiple levels.

The question is: **where in the chain from design → sprint prompt → agent execution → delivered code did the story's requirements get lost, simplified, or contradicted?**

## Your task

Read the documents below IN ORDER. Do not write any code. Produce only a diagnostic report.

## Phase 1: Establish the design contract

Read the primary design document:
`~/.vaults/root/2nd-Brain/Projects/cheias-pt/discovery/12-design-document.md`

For EACH chapter (0-9), extract the design document's **exact specifications**:
- What visualization type was prescribed? (heatmap, animation, river lines, polygons, etc.)
- What temporal behavior was specified? (scroll-controlled animation, static snapshot, multi-frame)
- What data source was mapped to the chapter?
- What emotional/narrative purpose does the chapter serve in the arc?
- What specific design language was used? (e.g., "rivers swelling — thickening lines that animate as discharge increases")

Build a table: Chapter | Design Spec | Visualization Type | Temporal Behavior | Narrative Role

## Phase 2: Trace the translation to sprint instructions

Read the sprint prompt that agents executed:
`prompts/sprint-02-wire-data.md`

For EACH chapter, compare the sprint prompt instructions against the design document specs:
- Where does the sprint prompt faithfully translate the design document?
- Where does it simplify, compromise, or contradict the design document?
- What explicit overrides exist? (e.g., does the sprint prompt say "prefer X over Y" where the design doc said Y?)
- What design requirements were silently dropped between design doc and sprint prompt?
- What new constraints were introduced that weren't in the design doc?

Build a table: Chapter | Design Spec | Sprint Instruction | Delta (faithful / simplified / contradicted / dropped)

**Pay special attention to:**
- The design doc's prescription for soil moisture as "animation shows the ground progressively filling" vs. what the sprint says
- The design doc's prescription for river discharge as "line thickness on the basins.geojson river network" and "rivers swelling — thickening lines" vs. what the sprint says
- The design doc's prescription for Chapter 7 as "ALL consequences overlaid on precondition conditions" vs. what the sprint assigns
- The design doc's prescription for Chapter 8 as "precondition index at a pre-storm date" vs. what actually renders
- Whether the sprint prompt preserves the design doc's temporal sequence (the backbone of the story) or collapses it into static snapshots

## Phase 3: Trace execution against sprint instructions

Read the CLAUDE.md file (the build instructions agents see):
`CLAUDE.md`

Then read ALL source files in `src/`:
- `story-config.js` — chapter declarations
- `layer-manager.js` — layer definitions and wiring
- `chapter-wiring.js` — data-driven chapter logic
- `temporal-player.js` — temporal animation system
- `data-loader.js` — data fetching and caching
- `scroll-observer.js` — scroll detection
- `map-controller.js` — map initialization
- `exploration-mode.js` — free navigation mode
- `main.js` — orchestration

For EACH chapter, answer:
- Does the code implement what the sprint prompt specified?
- Where does the code deviate from even the (already degraded) sprint instructions?
- Are there runtime errors, missing data paths, or broken wiring?
- What's the actual layer type used? (circle, fill, heatmap, line, symbol?)
- Is temporal animation connected or disconnected?
- Are layer assignments correct per the sprint's teammate ownership?

## Phase 4: Trace the data pipeline

Verify the data exists and is valid:
- `data/frontend/` — list all files, sizes, structure. Do they match what sprint-02 Teammate 1 was asked to produce?
- `data/flood-extent/` — are PMTiles valid? Test by checking if the source is registered and the layer renders.
- `data/consequences/events.geojson` — are all 42 events present? What types? Does every type have a color mapping in layer-manager?
- Check for the green dot issue: what event type maps to green? Is there a color mapping gap?

## Phase 5: Identify the degradation cascade

This is the core analysis. Map the full chain for each chapter:

```
Design document prescription
    ↓ [Translation to sprint prompt — what was lost?]
Sprint prompt instruction
    ↓ [Agent execution — what was misimplemented?]
Delivered code
    ↓ [Runtime behavior — what fails to render?]
QA result (what the user sees)
```

For each chapter, identify:
1. **Design→Sprint losses:** requirements that were simplified or dropped when writing the sprint prompt
2. **Sprint→Code losses:** instructions that agents didn't implement correctly
3. **Code→Runtime failures:** code that exists but doesn't work (broken paths, wrong data, missing wiring)

Which category contains the MOST failures? This tells us whether the problem is:
- (a) Bad translation of design to sprint (the prompt was wrong)
- (b) Bad agent execution (the prompt was right but agents didn't follow it)
- (c) Integration failures (individual pieces work but aren't connected)

## Phase 6: The temporal backbone question

The design document builds the entire narrative on temporal progression:
- Ch3: soil filling Dec→Jan (scroll-animated)
- Ch4: storms arriving Jan 25→Feb 12 (sequential)
- Ch5: rivers rising in response (temporal discharge curves)
- Ch7: all layers at peak (synthesis moment)
- Ch8: precondition index BEFORE storms (the predictive proof)

Answer specifically:
- Does `temporal-player.js` actually work? Is it called? Does it update map state?
- Is scroll position mapped to temporal frame index in any chapter?
- Does the date label in Chapter 3 change because the data changes, or is it cosmetic?
- Is Chapter 8 showing the wrong timestep? Which timestep IS it showing?
- Could the Ch7/Ch8 issue be that both are showing the same data at different timesteps, but the timestep selection is wrong for one or both?

## Phase 7: The visualization type question

The design document specifies:
- Soil moisture: "interpolated to a heatmap" / "animation shows the ground progressively filling"
- Discharge: "line thickness on the basins.geojson river network" / "rivers swelling — thickening lines"
- Precondition: basins colored by index value (choropleth on basin polygons)

The sprint-02 prompt says:
- "Prefer circle layers over heatmaps for the point grids"
- Discharge as "circles with proportional radius"

Answer:
- Why did the sprint prompt override the design doc's visualization types?
- Was "prefer circle layers over heatmaps" a performance concern? A complexity concern? An explicit decision or an accidental downgrade?
- What would it take to implement the design doc's actual specifications (heatmap, river lines)?

## Output

Write your findings to `FORENSIC-REPORT.md` in the project root with these sections:

1. **Design Contract Summary** — what the design doc prescribed per chapter (table)
2. **Sprint Translation Audit** — where the sprint prompt deviated from design (table with deltas)
3. **Execution Audit** — where code deviated from sprint instructions (table with deltas)
4. **Degradation Cascade** — the full chain per chapter showing where each requirement was lost
5. **Root Cause Analysis** — which level (design→sprint, sprint→code, code→runtime) contains the primary failures
6. **The Temporal Question** — specific diagnosis of why the timeline doesn't work
7. **The Visualization Question** — specific diagnosis of why dot grids replaced heatmaps/lines
8. **Recommendations** — what needs to change structurally for Sprint 02 to succeed

Be specific. Cite file names, line numbers, exact text from documents. Do not speculate when you can verify by reading the code. The goal is a precise map of where intent became disconnected from execution.

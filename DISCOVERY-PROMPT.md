# cheias.pt — Phase 0: Discovery

> **Purpose:** Research what we DON'T already know to make informed architecture decisions for cheias.pt — a flood monitoring platform for Portugal.
>
> **Method:** Designed for Claude Code. Use an agents team for Tasks 1–5 (independent, parallelisable). Task 6 synthesises. All outputs go to `discovery/`.
>
> **Critical:** We have extensive prior intelligence on DevSeed, their tech stack, their team, and the geospatial landscape. **Read the vault first, research what's missing.**

---

## Why This Project

Portugal has no citizen-facing flood monitoring platform. DevSeed's Lisbon team member Olaf Veerman built incendios.pt for fire data. We want to build the flood equivalent — cheias.pt — as both a public tool and a demonstration of GeoAgent capabilities (LLM-driven geospatial query and analysis).

Domain **cheias.pt** is registered and owned by us.

---

## Existing Intelligence (READ FIRST)

Months of research already exist in the Obsidian vault. Agents MUST read relevant files before doing any web research, to avoid duplicating work and to build on what we know.

### DevSeed & Geospatial Tech Stack
Already deeply mapped. Read before researching:

- **Tech matrix (people × technologies):**
  `~/.vaults/root/2nd-Brain/Projects/geospatial-tech-intelligence/tech-matrix.md`

- **Cloud-native geo deep-dive (STAC, COG, eoAPI, DuckDB, Zarr, etc.):**
  `~/.vaults/root/2nd-Brain/Projects/geospatial-tech-intelligence/domain-cloud-native-geo.md`

- **GeoAI & ML landscape (foundation models, GeoAgents, embeddings):**
  `~/.vaults/root/2nd-Brain/Projects/geospatial-tech-intelligence/domain-geoai-ml.md`

- **DevSeed operations & European strategy:**
  `~/.vaults/root/2nd-Brain/Projects/geospatial-tech-intelligence/domain-devseed-operations.md`

- **DevSeed company signals (LinkedIn, blog, public positioning):**
  `~/.vaults/root/2nd-Brain/Projects/geospatial-tech-intelligence/devseed-company-signals.md`

- **Positioning overlay (our skills vs field requirements):**
  `~/.vaults/root/2nd-Brain/Projects/geospatial-tech-intelligence/positioning-overlay.md`

- **24 individual people-tech profiles:**
  `~/.vaults/root/2nd-Brain/Projects/geospatial-tech-intelligence/people-tech/`

### DevSeed Recon
- **Company intelligence & blog recon:**
  `~/.vaults/root/2nd-Brain/Projects/DevSeed-Recon/`

### What We've Already Built
- **Working Sentinel-2 STAC/COG/MapLibre viewer:**
  `~/Documents/dev/geo-viz-deliverable/`
- **Custom STAC/COG skill:**
  `/mnt/skills/user/stac-cog-viewer/`
- **PROMOVE project notes:**
  `~/.vaults/root/2nd-Brain/Projects/Atlas-Regeneracao-PROMOVE.md`

---

## Team Tasks

Given the existing intelligence, the real gaps are: **flood-specific data sources** (Tasks 1–2), **how DevSeed patterns apply to flood monitoring specifically** (Task 3), **GeoAgent design applied to flood queries** (Task 4), and **competitive landscape for flood platforms** (Task 5).

### Task 1: Portuguese Flood Data Landscape
**Output:** `discovery/01-portuguese-data-sources.md`

This is entirely new research — we have no prior intelligence on Portuguese flood data.

Investigate: SNIRH (river levels, precipitation — snirh.apambiente.pt), APA (flood risk mapping, PGRI plans), IPMA (meteorology, warnings — ipma.pt), DGT (land use, flood-prone areas), Copernicus EMS activations for Portugal.

For each source: What data? Is there an API? What format? What latency? Test endpoints with curl where possible. Rate accessibility honestly — many Portuguese government data portals look good on paper but don't work.

### Task 2: Satellite & European Data for Flood Detection
**Output:** `discovery/02-satellite-european-data.md`

We know the STAC/COG ecosystem well (read `domain-cloud-native-geo.md` first). What we DON'T know is how it applies specifically to flood detection.

Focus on:
- **Sentinel-1 SAR flood detection:** What's the established approach? Thresholding, change detection, ML? Existing services or repos? Revisit time over Portugal? Latency from acquisition to STAC availability?
- **Sentinel-2 for floods:** NDWI formula and bands. The cloud cover problem during flood events.
- **GloFAS / EFAS:** API access, format, STAC compatibility, forecast horizon for Portuguese rivers.
- **Copernicus Data Space Ecosystem:** How it compares to Earth Search for flood use cases.
- **Foundation models for flood detection:** Read `domain-geoai-ml.md` first — then assess whether Clay, Prithvi, or others are relevant specifically for flood mapping from SAR/optical data.

### Task 3: DevSeed Patterns Applied to Flood Monitoring
**Output:** `discovery/03-devseed-patterns-for-floods.md`

We have extensive DevSeed intelligence (read `devseed-company-signals.md`, `domain-cloud-native-geo.md`, and `domain-devseed-operations.md` first). This task bridges that knowledge to the flood domain.

Focus on:
- **incendios.pt** specifically: Visit https://incendios.pt — how is it built? Data sources? Open source? What patterns can we reuse for floods?
- **eoAPI for real-time + archival:** Our vault documents eoAPI's architecture, but how would it handle the mix of real-time gauge data and archival satellite imagery that a flood platform needs?
- **Kevin Bullock's HydraAtlas:** Read his people-tech profile first, then research the app. What flood data patterns can we learn from?
- **Global Nature Watch as GeoAgent reference:** Read `domain-geoai-ml.md` for what we know. Any new public information on the architecture since Feb 2026?

### Task 4: GeoAgent Design for Flood Queries
**Output:** `discovery/04-geoagent-design.md`

We know the GeoAgent landscape conceptually (read `domain-geoai-ml.md` — section on GeoAgents/agentic workflows). This task makes it concrete for flood queries.

The target interaction: a user asks "Houve cheias perto de Santarém?" and the system geocodes, queries satellite data, checks river gauges, and synthesises an answer with a map.

Focus on:
- What tools does the agent need? (geocoding, STAC search, gauge lookup, index computation, map rendering)
- What's the simplest version that demonstrates the pattern?
- What's the hardest part? (likely combining heterogeneous data sources in real-time)
- Orchestration: n8n workflow vs direct LLM tool-use vs hybrid. We have n8n running at n8n.lunasilvestre.systems.
- MCP servers: any existing ones for geospatial data? Chris Holmes recently advocated for MCP+geo (see his people-tech profile).

### Task 5: What Already Exists (Competitive Landscape)
**Output:** `discovery/05-competitive-landscape.md`

What flood monitoring platforms exist for Portugal and Europe? Where are the gaps?

Look at: Portuguese government flood tools (SNIRH web interface, APA viewers), EFAS/GloFAS public viewers, Copernicus EMS rapid mapping, academic projects from Portuguese universities, commercial platforms, open source flood tools.

What does cheias.pt need to do that nothing else currently does?

### Task 6: Synthesis
**Output:** `discovery/06-synthesis.md`

**Depends on Tasks 1–5 AND the existing vault intelligence.** Read everything, then produce:

1. **Data source tier list** — what's usable now, what needs work, what's blocked
2. **Key architectural decisions** to make (list the questions, don't prescribe answers)
3. **MVP scope recommendation** — what could ship first to demonstrate the most value
4. **Risk register** — data access, technical complexity, strategic positioning
5. **What Phase 1 should focus on** — and what the next prompt should contain

---

## Output Standards

Each file should:
- Start with YAML frontmatter: `title`, `phase: discovery`, `created`, `status`
- Note which vault files were read as prior context
- Include tested/working URLs where possible
- Flag dead ends and blockers with `> ⚠️` callouts
- End with `## Key Takeaways` (3–5 bullets)
- Be honest about uncertainty — "couldn't verify" beats guessing

---

## Environment

- **OS:** Debian 13, Python 3.x
- **Existing prototype:** `~/Documents/dev/geo-viz-deliverable/`
- **STAC/COG skill:** `/mnt/skills/user/stac-cog-viewer/`
- **n8n:** n8n.lunasilvestre.systems
- **Vault:** `~/.vaults/root/2nd-Brain/Projects/cheias-pt/`
- **Domains:** cheias.pt (registered), lunasilvestre.systems (active)

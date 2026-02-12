# Component Architecture Patterns

**[STUB]** This reference file would contain patterns for architecting map + sidebar layouts and state management.

**Topics to cover:**
- Three-layer component structure (presentation / container / data)
- Render-less managers (layer management without UI concerns)
- Feature modules (Redux Toolkit slices, feature-based organization)
- Layer toggle patterns (batch operations, z-index control, beforeId ordering)
- Responsive mobile sheets (desktop sidebar → mobile bottom sheet transformation)
- State synchronization (map state ↔ UI state, deck.gl props)

**Source material:** LandGriffon's Redux Toolkit organization, GlobalFishingWatch's Nx monorepo architecture, Half-Earth's ArcGIS layer manager, landgriffon's declarative layer manager with z-index ordering.

**Status:** Code examples extracted during repo analysis. Architecture decisions documented in research files but not synthesized into reusable component patterns. LandGriffon analysis particularly rich (layout-based app architecture, collapsible sidebars, mode switching).

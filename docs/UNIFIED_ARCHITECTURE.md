# Unified Architecture Blueprint

Discovered **235** Echo modules and reorganised them into layered constellations that expose foundation systems, synthesis engines, and expressive story surfaces.

## Layered Overview
- **Frontier** · 149 modules · frontier
- **Foundation** · 44 modules · bridge, continuum, pulse, sovereign, systems
- **Synthesis** · 30 modules · continuum, pulse
- **Expression** · 12 modules · creative

## Category Atlas
- **frontier** (149 modules) → _paths.py, akit/cli.py, akit/config.py, akit/models.py, akit/persistence.py, amplify.py, api/routes_echonet.py, api/state.py
- **pulse** (22 modules) → ecosystem_pulse.py, grand_crucible/telemetry.py, hyperdimensional_resonance_cli.py, hyperdimensional_resonance_engine.py, mythogenic_pulse_engine.py, orbital_resonance_analyzer.py, pulse/analytics.py, pulse/broadcaster.py
- **systems** (19 modules) → akit/core.py, echo_capability_engine.py, echo_core_system_v4.py, echo_eye_core.py, hypermesh_engine.py, hypernova/orchestrator.py, meta_causal/engine.py, orbital_loop.py
- **bridge** (13 modules) → api/routes_registry.py, bridge/models.py, bridge/router.py, bridge/service.py, bridge_emitter.py, bridge_harmonix.py, echonet/registry.py, groundbreaking_manifest.py
- **continuum** (12 modules) → api/routes_timeline.py, atlas/temporal_ledger.py, continuum_atlas/atlas_resolver.py, continuum_compass.py, continuum_cycle.py, continuum_engine.py, continuum_health.py, continuum_insights.py
- **creative** (12 modules) → aurora_chant_generator.py, aurora_chronicle.py, aurora_chronicles.py, aurora_storyweaver.py, aurora_unbound.py, creative_bloom.py, creative_compass.py, creative_echo.py
- **sovereign** (8 modules) → guardian.py, meta_evolution_charter.py, sovereign/beneficiary.py, sovereign/compliance.py, sovereign/donations.py, sovereign/entity.py, sovereign/governance.py, sovereign/transparency.py

## Keystone Modules
- `continuum_engine.py` · categories: continuum, systems · score 4
- `mythogenic_pulse_engine.py` · categories: pulse, systems · score 4
- `hyperdimensional_resonance_engine.py` · categories: pulse, systems · score 3
- `orchestrator/core.py` · categories: systems · score 3
- `policy_engine.py` · categories: systems, sovereign · score 3
- `vNext/agents/governance_pulse.py` · categories: pulse, sovereign · score 3
- `akit/core.py` · categories: systems · score 2
- `bridge/models.py` · categories: bridge · score 2
- `bridge/router.py` · categories: bridge · score 2
- `bridge/service.py` · categories: bridge · score 2
- `bridge_emitter.py` · categories: bridge · score 2
- `bridge_harmonix.py` · categories: bridge · score 2

## Convergent Pathways
- pulse<->systems × 2
- creative<->pulse × 2
- continuum<->systems × 1
- sovereign<->systems × 1
- pulse<->sovereign × 1

Use `python -m echo.unified_architecture_engine --json` to stream the raw blueprint into other research pipelines or `--output docs/UNIFIED_ARCHITECTURE.md` to refresh this file.

| Name | Type | Path | Version | Digest | Dependencies |
| --- | --- | --- | --- | --- | --- |
| ManifestInsights | akit | scripts/manifest_table.py | 2024.05 | 7b44fdbea0b09d989fbc4be734ebdd47491d2c66120e182c391f247758e9ee36 | BridgeEmitter, ContinuumEngine |
| BridgeEmitter | engine | echo/bridge_emitter.py | 2024.05 | 17843844daabd8cd2613a35d2eafbca51c209d144ef76364b990fb5bc48de583 | — |
| ContinuumEngine | engine | echo/continuum_engine.py | 2024.05 | 5d621cd31c03c821044e3facdbde4024167922c48f6f5dc366eb094136a278a7 | BridgeEmitter |
| ContinuumLedger | state | pulse_history.json | 2024.05 | 9d6d7aecba16e1736615d9b539678b06a2776c9a9d975c21304e5c4ab292729d | PulseTimeline |
| PulseTimeline | state | pulse.json | 2024.05 | 63492ba7baf2aaea68ea6bccbef43bbf2a1072565cfe276b6a49e266763d6cd1 | ContinuumEngine |

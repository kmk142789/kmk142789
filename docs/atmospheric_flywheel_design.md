# Atmospheric Flywheel Energy Storage Concept

## Objective
Design a flywheel energy storage system (FESS) that can operate at atmospheric pressure with inexpensive, non-magnetic bearings while remaining safe, manufacturable, and cost-competitive with lithium-ion batteries for behind-the-meter and microgrid use.

## Target performance envelope
- **Power/energy**: 15–50 kW charge/discharge, 50–150 kWh usable energy per module.
- **Round-trip efficiency**: 85–90% at rated power (drag-limited at low speed, converter-limited at high speed).
- **Lifetime**: 20,000+ deep cycles with <5% capacity fade; 20-year calendar life.
- **CAPEX target**: <$250/kWh at scale.

## Architecture overview
- **Rotor**: Carbon-fiber filament-wound rim (hoop + radial web) with a glass-fiber sacrificial outer wrap for debris capture. Stainless-steel hub integrates motor/generator shaft coupling.
- **Housing**: Thick-wall steel tube with internal energy-absorbing foam and replaceable aramid (Kevlar) catch liner. Slight negative pressure (not vacuum) using a low-cost blower to limit dust and manage airflow.
- **Bearings**: Duplex angular-contact ceramic-hybrid ball bearings sized for DN < 700,000; optional top foil journal bearing for higher-cycle SKUs. No magnetic levitation or superconductors.
- **Motor/generator**: Switched-reluctance machine (SRM) with integral flywheel hub to avoid permanent magnets; liquid-cooled stator for thermal stability.
- **Aerodynamic drag control**: Narrow annular flow path with stationary shrouds and labyrinth seals; integral fins on the rotor web pump air through an annular heat exchanger to recover convective losses into useful heat.
- **Safety**: Steel + aramid containment sized for 1.5× maximum stored energy; burst vents directed to top; passive mechanical overspeed trip using centrifugal pawls engaging a friction collar.

## Rotor sizing sketch
For a rim-dominant rotor, stored energy is roughly one half times mass times radius squared times angular speed squared (thin hoop approximation):
- **Example**: 90 kg carbon/glass composite rim, mean radius 0.45 m, design tip speed 350 m/s (about 12,000 rpm).
- Stored energy ≈ 0.5 × 90 × 0.45² × (350/0.45)² ≈ 110 kWh (usable ~90 kWh with 80% depth of discharge on speed window).
- Hoop stress scales with density times tip speed squared. With composite density 1,600 kg/m³ and allowable 1.8 GPa, the stress margin is about 1.3× at 350 m/s.

## Bearings without magnets
1. **Primary option (cost-optimized)**: Back-to-back angular-contact ball bearings with ceramic balls and steel races.
   - Preloaded to avoid skidding at low speed.
   - Grease-for-life with periodic relubrication via ports; expected L10 life > 30,000 hours at 12,000 rpm with proper sizing.
2. **Higher-cycle option**: Compliant foil journal + thrust bearing at the top, rolling bearing at the bottom for axial retention.
   - Uses ambient air as the working fluid, eliminating oil systems.
   - Proven in microturbines for 50,000+ hour life.

## Atmospheric drag and thermal strategy
- **Shrouded annulus** around the rim to minimize form drag; labyrinth seals reduce windage without requiring a hard vacuum.
- **Flow-driven heat recovery**: Rotor web carries low-profile fins that act as an impeller, moving 50–150 cfm through a stationary annular heat exchanger. Waste heat can preheat building water or space air, reclaiming 3–6% otherwise lost.
- **Material choices**: Use low-surface-energy epoxy topcoat and polished liners to cut skin friction; coat inner housing with ceramic paint to handle brief hot-gas pulses during a fault.

## Motor/generator and power electronics
- **Switched-reluctance drive** eliminates magnets and is tolerant to temperature rise; concentrated windings simplify cooling.
- **Bi-directional converter** with wide-bandgap MOSFETs/IGBTs; DC bus at 800–1,000 V for good power density.
- **Black start** via small supercapacitor bank; DC/DC interface for microgrid coupling and UPS ride-through.

## Containment and safety-in-depth
1. **Passive overspeed limit**: Centrifugal pawls engage a graphite/steel friction collar at 110% rated speed, bleeding energy as heat while triggering electrical shutdown.
2. **Liner and foam stack**: Aramid liner catches fragments; crushable aluminum foam absorbs impulse; steel tube contains residual shrapnel.
3. **Diverter ports**: Top-mounted blow-out disks vent to a sacrificial plenum; prevents lateral fragment jetting.
4. **Runaway detection**: Dual-redundant tachometers plus vibration probes; hardwired comparator trips at 105% speed or two times baseline vibration.

## Operations and maintenance
- Annual inspection of bearings via ultrasound and vibration signature; relubricate if grease option is used.
- Replaceable modular rotor cartridge (rim + hub + bearings) for field swaps under 4 hours.
- Automated balancing routine: at mid-speed, the SRM injects dither to measure imbalance and applies trim via threaded balance nuts accessible through service ports.

## Cost-down levers
- Use commodity SRM laminations and bus hardware shared with industrial drives.
- Glass fiber for sacrificial outer wrap and containment liner where allowable to reduce carbon use.
- Stacked laser-cut steel housing rather than thick forgings for small units.
- Foil-bearing option removes lubrication circuit entirely for mission-critical models.

## Risk register (top items)
| Risk | Mitigation |
| --- | --- |
| Bearing heat at high DN | Use ceramic balls, moderate preload, forced-air purge; monitor temperature and derate. |
| Windage losses eroding efficiency | Optimize shroud clearance; add CFD-tested riblets; reclaim heat via exchanger. |
| Rotor burst | 1.5× energy-rated containment, proof spin at 120% in factory, non-destructive inspection every 5 years. |
| SRM acoustic noise | Skewed poles, higher switching frequency with spread-spectrum PWM, acoustic damping in housing. |
| Installation shocks | Shock mounts and transport locks on rotor; accelerometer interlock on startup. |

## Deployment scenarios
- **Commercial buildings**: Pair with rooftop PV; waste heat to hydronic loop.
- **Microgrids**: Works in dusty or humid sites where vacuum systems are unreliable; foil-bearing SKU for minimal maintenance.
- **Industrial UPS**: Ride-through for mills and fabs where high cycle count and low degradation beat batteries.

## Next validation steps
1. Bench-test a 5 kWh subscale rotor (0.2 m radius, 20,000 rpm) to validate windage and bearing heating.
2. Build CFD model of shroud and heat-recovery flow path; target drag coefficient under 0.015 at rated speed.
3. Fatigue-test filament-wound rim coupons to one million cycles at 1.2 times operating stress.
4. Integrate SRM plus converter prototype; demonstrate black-start and 50 kW peak discharge for 30 seconds.

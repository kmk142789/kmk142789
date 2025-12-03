# Mechanical Joint That Self-Centers and Self-Repairs

## Objective
Create a robotic rotary joint that automatically compensates for wear, restores tolerances, and eliminates backlash over long service life without human intervention.

## Core Design Principles
- **Kinematic biasing, not brute preload:** Use opposing cam pairs and flexures to center the rotor without over-constraining the raceways.
- **Closed-loop clearance control:** Sense micrometer-scale radial/axial clearance and adjust preload adaptively.
- **Sacrificial + regenerative surfaces:** Include low-friction sacrificial pads that can be advanced or reflowed to restore geometry.
- **Onboard metrology:** Embed displacement and torque sensing to distinguish wear from thermal drift or load spikes.
- **Field-swappable cartridges:** Keep actuation and sensing modular for rapid replacement if a subassembly fails.

## Architecture Overview
```
         [Slip ring/FOG cable]  
                 │
        ┌────────┴────────┐
        │  Hollow shaft   │
        │  (rotor)        │
        └────────┬────────┘
                 │
   ┌─────────────┼─────────────┐
   │  Dual opposed cam rings   │  ← self-centering via flexure-driven wedges
   └─────────────┼─────────────┘
        ╱        │        ╲
   Radial flexures│Radial flexures
        ╲        │        ╱
   ┌─────────────┴─────────────┐
   │  Stator housing (split)   │
   └───────────────────────────┘
```

### Load Paths
- **Radial/axial loads:** Transferred through ceramic hybrid bearings with split races and wedge preloads.
- **Torsion:** Carried by keyed rotor/hub; preload loops avoid adding torsion to the flexures.
- **Shock:** Decoupled by viscoelastic layer under sacrificial pads; clamps re-center after transient.

## Self-Centering Mechanism
1. **Opposed cam wedges:** Two cam rings at 90° phase advance push split outer races radially in four quadrants.
2. **Flexure bias:** S-shaped titanium flexures convert axial micro-motion from piezo stacks into radial preload without friction.
3. **Symmetry logic:** Controller advances wedges in paired, equal steps to keep the rotor axis coincident with the stator datum.
4. **Thermal decoupling:** Athermal flexure geometry (matched CTE titanium + Invar shims) minimizes drift.

## Self-Repair / Wear Compensation
- **Incremental advance pads:** PTFE/bronze or PEEK pads on threaded micro-cartridges advance a few µm/step via piezo-actuated harmonic drive; they renew contact surfaces and erase clearance.
- **In-situ reflow option:** Resistive micro-heaters behind polymer pads soften and reflow the pad face against the race to re-establish conformity, then cool while held with preload.
- **Debris management:** Micro-grooved races and a vacuum/filtered micro-blower pull wear debris into a replaceable cartridge; magnetic insert captures ferrous fines.
- **Surface refresh cycles:** Controller runs short preload/oscillation cycles to burnish regenerated pads and measure restored stiffness.

## Sensing and Control
- **Displacement sensing:** Four differential capacitive probes (±5 µm range, 5 nm resolution) read radial/axial clearance; redundant Hall or inductive probes if contamination occurs.
- **Torque + current:** Motor phase current + inline strain-gauge ring monitor friction growth.
- **Temperature:** RTDs near pads and bearings separate thermal expansion from wear.
- **Control loop:**
  - Kalman filter fuses displacement, torque, and temperature to estimate true clearance.
  - Backlash threshold: when estimated clearance > target (e.g., 1 µm), issue micro-advance of paired pads.
  - Verify: after actuation, remeasure; if not restored, schedule reflow cycle.

## Materials
- **Rotor/shaft:** 17-4 PH SS or Ti-6Al-4V with hard-chrome or DLC coating.
- **Bearings:** Hybrid ceramic (Si3N4 balls) with split outer races and dry film (MoS₂ + PTFE) solid lube.
- **Flexures:** Titanium for high fatigue life; EDM-cut with generous fillets.
- **Pads:** Bronze/PTFE or PEEK with carbon fiber fill; optional nano-diamond sprinkle for polish.
- **Seals:** Low-drag labyrinth + PTFE lip; maintain slight negative pressure via micro-blower.

## Actuation Subsystems
- **Piezo stacks (radial):** 10–20 µm stroke, amplified by flexures to 40–60 µm preload travel.
- **Micro harmonic drives:** 50:1 reduction for pad advance; back-drivable only under commanded voltage to avoid creep.
- **Heaters:** Thin-film polyimide heaters behind pads; temp controlled < 220 °C for polymer longevity.

## Electronics & Firmware
- **MCU/FPGA mix:** MCU runs estimation loop at 1 kHz; FPGA times capacitive sensing and piezo drive.
- **Health counters:** Track pad advance counts, reflow cycles, actuator margin, bearing vibration (RMS).
- **Failsafes:** If preload margin exhausted or vibration exceeds threshold, lock joint and alert higher-level controller.
- **Interfaces:** CAN-FD or EtherCAT; publish clearance estimate, stiffness, and remaining life.

## Maintenance & Modularity
- **Cartridge design:** Pad + flexure + cam wedge module removable without disturbing encoder or motor.
- **No human adjustment:** Replacement cartridges self-home via mechanical datum pins and run an auto-calibration sequence.
- **Predictive alerts:** Remaining pad travel and flexure fatigue factor reported continuously.

## Test & Validation Plan
1. **Bench metrology:** Measure stiffness vs. preload curve before/after 10k wear cycles (dust-contaminated test).
2. **Backlash audit:** Laser interferometer to verify <1 µm bidirectional reversal error after 1e6 cycles.
3. **Self-repair demo:** Intentionally gap the race by 10 µm, command auto-compensation, verify restored stiffness/center.
4. **Environmental:** Thermal cycling -40 to 85 °C; vibration per MIL-STD-810; vacuum compatibility check for outgassing.
5. **Firmware fault injection:** Sensor dropout and stuck actuator simulations to ensure lockout and alert paths.

## Implementation Roadmap
- **Phase 1 — Breadboard:** Fixed shaft with four piezo-flexure wedges, external sensors, and manual pad advance.
- **Phase 2 — Integrated cartridge:** Add micro harmonic drives and heaters; validate auto-calibration and reflow.
- **Phase 3 — Sealed joint:** Add seals, blower, and debris cartridge; run endurance + contamination tests.
- **Phase 4 — Productionization:** Design for manufacturability (DFM), lifecycle FMEA, and supply chain locking for pads and flexures.

## Why It Self-Centers and Self-Repairs
- **Self-centering:** Symmetric opposing wedges driven in closed loop keep radial error near zero despite asymmetric wear.
- **Self-repair:** Consumable pads plus micro-advance and reflow restore the functional geometry, removing backlash.
- **Long-term stability:** Flexure-driven preload avoids fretting that conventional spring preloads suffer, and sensing closes the loop on true clearance rather than assumed preload.

# Echo Fusion Drone — Secondary Ambient Energy Harvesting Evaluation

## Purpose
This document evaluates **secondary ambient energy harvesting** methods for the Echo Fusion Drone. It focuses on three classes explicitly requested: **thermal gradients**, **vibration harvesting**, and **regenerative capture**. Each method includes quantified yield estimates, operational niches, and viability constraints. Non-viable expectations are rejected explicitly.

## Baseline Assumptions
- **Vehicle mass**: 1.5–3.0 kg class, battery-powered.
- **Primary propulsion power**: tens to hundreds of watts during flight.
- **Secondary harvesting target**: milliwatts to low watts for sensors, logging, and trickle recovery.
- **Thermal environment**: electronics/motor housings typically 40–80°C under load; ambient 0–35°C.
- **Mechanical environment**: vibration dominated by actuator harmonics, variable by mode.

---

## 1) Thermal Gradient Harvesting (TEG)
**Mechanism**: Thermoelectric generators (TEGs) produce power from a temperature difference (ΔT) between a hot component (motor/ESC/battery) and a cooled surface (airframe/heat sink).

### Expected Yield (Conservative Ranges)
| Gradient (ΔT) | TEG Active Area | Expected Output | Notes |
|---|---:|---:|---|
| 5–10°C | 10 cm² | 2–10 mW | Typical small module on warm electronics |
| 10–20°C | 10 cm² | 5–30 mW | Requires good heat spreader + airflow |
| 15–30°C | 50 cm² | 0.1–0.5 W | Large area; realistic only with distributed panels |
| 20–30°C | 100 cm² | 0.3–1.5 W | Best-case for extended hot surfaces |

### Operational Niches
- **Sustained load + cool ambient**: cold weather flight or high-altitude operations where ΔT stays high.
- **Ground standby / thermal soak**: electronics remain warm, airframe cools, enabling trickle recharge for data logging.
- **Thermal governance**: can act as a *parasitic* heat sink, aiding thermal management while providing small power.

### Viability Assessment
- **Viable for**: sensor networks, safety MCU backup, log persistence, thermal state monitoring.
- **Not viable for**: propulsion or endurance extension beyond a **few percent** at most.

### Explicit Rejections
- **Rejected**: “TEG can power flight” — TEG yields are orders of magnitude below propulsion demands.
- **Rejected**: “Uniform internal heat harvesting” — without a **real ΔT**, TEG output collapses to near zero.

---

## 2) Vibration Energy Harvesting (Piezo / Electromagnetic)
**Mechanism**: Harvests oscillatory motion from structure or actuator vibration into electrical energy via piezoelectric or electromagnetic transducers.

### Expected Yield (Conservative Ranges)
| Vibration Environment | Harvester Count | Expected Output | Notes |
|---|---:|---:|---|
| Low amplitude, cruise | 1–2 | 0.05–0.5 mW | Typical if frame is well-balanced |
| Moderate vibration, hover | 2–4 | 0.5–5 mW | Depends strongly on resonance tuning |
| High vibration, test regime | 4–8 | 5–20 mW | Only during abnormal or aggressive operation |

### Operational Niches
- **Structural health monitoring**: supports always-on strain or resonance sensors without burdening main battery.
- **Ground testing / diagnostics**: vibration-intensive scenarios can sustain tiny data loggers.
- **Fault detection**: harvesting spikes can signal abnormal vibration states and trigger alerts.

### Viability Assessment
- **Viable for**: micro-power sensing, wake-on-vibration triggers, lightweight diagnostics.
- **Not viable for**: propulsion or significant endurance gains.

### Explicit Rejections
- **Rejected**: “Vibration harvesting can sustain flight” — yields are **milliwatt-scale** vs. flight power in the **hundreds of watts**.
- **Rejected**: “Stable cruise harvesting” — well-balanced flight intentionally minimizes vibration, reducing harvestable energy.

---

## 3) Regenerative Capture (Actuator / Descent / Braking)
**Mechanism**: Converts kinetic or potential energy back into electrical energy via regenerative motor drivers, back-EMF capture, or controlled descent energy recovery.

### Expected Yield (Conservative Ranges)
| Scenario | Capture Path | Expected Output | Notes |
|---|---|---:|---|
| Morphing joint deceleration | Motor regen | 0.5–5 W (short bursts) | Depends on actuator mass and duty cycle |
| Controlled descent (1–3 kg, 50–150 m) | Prop/actuator regen | 0.05–0.3 Wh | ~2–20% of potential energy if captured efficiently |
| Aggressive braking / maneuver rollback | Motor regen | 1–15 W (brief) | Short pulses, not continuous |

**Example calculation**: A 2 kg drone descending 100 m has ~2 kJ of potential energy (≈0.56 Wh). Even at **20% recovery**, usable energy is only **~0.11 Wh**, a minor fraction of a typical multi-Wh battery.

### Operational Niches
- **Descent phases**: recovery during controlled descent or landing profiles.
- **Morphing or CVT rollback**: reclaim energy during actuator deceleration.
- **Safety modes**: mild recovery in degraded/return-to-home sequences.

### Viability Assessment
- **Viable for**: topping up avionics, extending loiter time **marginally**, powering brief sensor bursts.
- **Not viable for**: primary energy supply or continuous flight.

### Explicit Rejections
- **Rejected**: “Continuous regen in steady flight” — no net braking energy is available in steady-state cruise/hover.
- **Rejected**: “Regen replaces battery” — energy available in descent events is **intermittent and limited**.

---

## Cross-Method Summary
| Method | Typical Power | Best Use Case | Viability Summary |
|---|---:|---|---|
| Thermal gradients (TEG) | mW to ~1 W | Cold ambient + warm electronics | Trickle power for sensors, logging |
| Vibration harvesting | µW to tens of mW | Health monitoring / diagnostics | Only micro-power applications |
| Regenerative capture | 0.5–15 W (bursts) / 0.05–0.3 Wh per descent | Descent / actuator rollback | Intermittent, marginal endurance gains |

---

## Non-Viable Expectations (Explicit)
1. **Secondary harvesting is not a propulsion substitute**: All evaluated methods yield **orders of magnitude less** than propulsion power needs.
2. **No perpetual or self-sustaining flight**: Harvesting depends on **existing energy sinks** (heat loss, vibration, or descent energy) and cannot exceed them.
3. **Steady-state flight provides minimal harvestable energy**: Low vibration and balanced thermal gradients limit recoverable power.

---

## Recommended Integration Strategy
- **Tier 1 (Always-Useful)**: TEGs on hot electronics + heat spreaders for **thermal governance + trickle power**.
- **Tier 2 (Diagnostic)**: Piezo vibration harvesters for **fault detection and sensor wake-up**.
- **Tier 3 (Mission-Specific)**: Regenerative capture on morphing actuators and controlled descent for **small energy recovery**.

**Design Rule**: Treat all secondary harvesting as **micro-power supplements** and **sensing enablers**, not as endurance multipliers.

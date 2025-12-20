# Flight Mode Constitution — Echo Fusion Drone (Thermal, Acoustic, Power Governance)

This constitution defines **invariants**, **entry criteria**, **forbidden conditions**, and **safe degradation paths** for each flight mode. The Governance Layer enforces these rules and logs every state transition or violation as evidence-grade artifacts.

## Constitutional Principles (Non-Optional)
1. **Thermal, acoustic, and power limits are hard constraints**, not optimizations.
2. **No mode entry** is permitted if any Do-Not-Enter condition is true.
3. **Any hard-limit violation forces Degraded Mode** and cannot be blocked.
4. **All transitions, violations, and derating events are logged** with timestamps and thresholds.

---

## Modes & Invariants

### 1) Hover
**Purpose:** Stable station-keeping with minimal thermal and acoustic stress.

**Invariants**
- `T_battery <= 60°C`
- `T_ESC <= 75°C`
- `dT/dt <= 1.0°C/s`
- `current_high_rail <= 0.8 × rated_continuous`
- `SPL_peak <= SPL_hover_max`
- `power_ramp_rate <= ramp_hover_max`

**Do-Not-Enter**
- Any sensor invalid.
- Battery temp ≥ 65°C.
- Voltage < minimum safe threshold.
- Any acoustic limit violation in last 30 seconds.

---

### 2) Cruise
**Purpose:** Sustained forward flight at balanced thermal load.

**Invariants**
- `thermal_margin >= 10°C` (all nodes)
- `dT/dt <= 0.8°C/s`
- `current_high_rail <= 0.8 × rated_continuous`
- `SPL_peak <= SPL_cruise_max`
- `power_ramp_rate <= ramp_cruise_max`

**Do-Not-Enter**
- `thermal_margin < 10°C`
- Any previous hard-limit event within last 60 seconds.
- Acoustic guard active or SPL limit exceeded in last 60 seconds.

---

### 3) Lift
**Purpose:** Short-duration high-power thrust for ascent or obstacle clearance.

**Invariants**
- `thermal_margin >= 15°C`
- `lift_timer <= 15 seconds`
- `current_high_rail <= 0.9 × rated_continuous`
- `SPL_peak <= SPL_lift_max`
- `power_ramp_rate <= ramp_lift_max`

**Do-Not-Enter**
- `thermal_margin < 15°C`
- `current_high_rail > 0.9 × rated_continuous`
- Battery temp >= 60°C.
- Acoustic guard active or SPL limit exceeded in last 60 seconds.

---

### 4) Degraded
**Purpose:** Emergency safe mode; minimum power for controlled descent or landing.

**Invariants**
- `derate_level >= 70%`
- Only essential avionics powered.
- High rail may be cut if critical fault persists.

**Do-Not-Enter**
- Degraded is mandatory on hard-limit violations; cannot be blocked.

---

## Forbidden States (System-Wide)
- **Propulsion demand exceeds power cap** (augmentation >15% instantaneous load).
- **Battery SOC < reserve floor** while in non-degraded mode.
- **Any unlogged state transition** (must be logged or transition is invalid).
- **Thermal or acoustic guard overridden by mission logic.**

---

## Transition Rules (Summary)
- **Hover → Cruise**: `speed >= V_min` AND `thermal_margin >= 10°C` AND acoustic guard inactive.
- **Hover → Lift**: `lift_request` AND `thermal_margin >= 15°C` AND `lift_timer < 15s` AND acoustic guard inactive.
- **Any → Degraded**: any hard-limit violation OR sensor fault OR watchdog trip.
- **Degraded → Hover**: manual acknowledgment + recovery criteria met.

---

## Safe Degradation Paths (Mandatory)
1. **Soft derate** to restore thermal or acoustic margin.
2. **Hard derate** if limits continue to be exceeded.
3. **High rail cut** if instability or unsafe state persists.
4. **Controlled landing** with essential avionics only.

---

## Governance Logging Requirements
Every mode transition must log:
- Timestamp
- From/To mode
- Trigger condition
- Thermal margin snapshot
- Acoustic status snapshot
- Active violations

Every violation must log:
- Constraint name
- Measured value
- Threshold
- Resulting derating or shutdown action

---

## Enforcement Guarantees
- The governance layer must refuse entry into any mode that violates **Do-Not-Enter** conditions.
- If a hard limit is crossed, it must force **Degraded** mode immediately and log the event.

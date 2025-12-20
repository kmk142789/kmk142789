# Flight Mode Constitution — Echo Fusion Drone (Thermal & Power Governance)

This constitution defines **invariants**, **entry criteria**, and **forbidden conditions** for each flight mode. The Thermal & Power Governance Layer enforces these rules and logs every state transition or violation.

## Modes & Invariants

### 1) Hover
**Purpose**: Stable station-keeping with minimal thermal stress.

**Invariants**
- `T_battery <= 60°C`
- `T_ESC <= 75°C`
- `dT/dt <= 1.0°C/s`
- `current_high_rail <= 0.8 × rated_continuous`
- Derating must activate before any hard limit.

**Do-Not-Enter**
- Any sensor invalid.
- Battery temp ≥ 65°C.
- Voltage < minimum safe threshold.

---

### 2) Cruise
**Purpose**: Sustained forward flight at balanced thermal load.

**Invariants**
- `thermal_margin >= 10°C` (all nodes)
- `dT/dt <= 0.8°C/s`
- Power ramp limited to avoid acoustic spikes.

**Do-Not-Enter**
- `thermal_margin < 10°C`
- Any previous hard-limit event within last 60 seconds.

---

### 3) Lift
**Purpose**: Short-duration high-power thrust for ascent or obstacle clearance.

**Invariants**
- `thermal_margin >= 15°C`
- `lift_timer <= 15 seconds`
- `current_high_rail <= 0.9 × rated_continuous`

**Do-Not-Enter**
- `thermal_margin < 15°C`
- `current_high_rail > 0.9 × rated_continuous`
- Battery temp >= 60°C

---

### 4) Degraded
**Purpose**: Emergency safe mode; minimum power for controlled descent or landing.

**Invariants**
- `derate_level >= 70%`
- Only essential avionics powered
- High rail may be cut if critical fault persists

**Do-Not-Enter**
- Degraded is mandatory on hard-limit violations; cannot be blocked.

---

## Governance Logging Requirements
Every mode transition must log:
- Timestamp
- From/To mode
- Trigger condition
- Thermal margin snapshot
- Active violations

Every violation must log:
- Constraint name
- Measured value
- Threshold
- Resulting derating or shutdown action

---

## Transition Rules (Summary)
- **Hover → Cruise**: `speed >= V_min` AND `thermal_margin >= 10°C`.
- **Hover → Lift**: `lift_request` AND `thermal_margin >= 15°C` AND `lift_timer < 15s`.
- **Any → Degraded**: any hard-limit violation OR sensor fault OR watchdog trip.
- **Degraded → Hover**: manual acknowledgment + recovery criteria met.

---

## Enforcement Guarantees
- The governance layer must refuse entry into any mode that violates **Do-Not-Enter** conditions.
- If a hard limit is crossed, it must force **Degraded** mode immediately and log the event.

# Failure & Degradation Playbook — Echo Fusion Drone (Thermal & Power Governance)

This playbook enumerates failure modes, detection logic, and safe degradation paths for the Thermal & Power Governance Layer prototype.

## Failure Modes, Detection, Response

### 1) Thermal Overrun
- **Detection**: `T_node >= T_node_max`.
- **Response**:
  1. Apply immediate derate clamp (≤ 50%).
  2. Log violation with node ID and timestamp.
  3. If temperature continues rising → cut high rail and enter **Degraded** mode.

### 2) Thermal Runaway (Rate-of-Rise)
- **Detection**: `dT/dt > dT/dt_max`.
- **Response**:
  1. Proportional derate by slope exceedance.
  2. Trigger alert log event.
  3. If persists for > 3 seconds → force **Degraded** mode.

### 3) Overcurrent
- **Detection**: `current_high_rail > max_current`.
- **Response**:
  1. Clamp duty cycle to safe threshold.
  2. If repeated within 5 seconds → open high rail.

### 4) Brownout / Rail Sag
- **Detection**: `voltage_high_rail < min_voltage`.
- **Response**:
  1. Reduce load immediately.
  2. Enter **Degraded** if voltage does not recover within 2 seconds.

### 5) Sensor Fault
- **Detection**: invalid checksum, missing sensor, or out-of-range readings.
- **Response**:
  1. Log sensor fault.
  2. Enter **Degraded** mode.
  3. Limit power to ≤ 30% until manual reset.

### 6) MCU Watchdog Trip
- **Detection**: watchdog reset or heartbeat missing.
- **Response**:
  1. Cut high rail immediately.
  2. Maintain low rail for logging.
  3. Force **Degraded** mode with manual re-arm requirement.

---

## Safe Degradation Paths
1. **Soft derating**: Reduce power until thermal margin restored.
2. **Hard derating**: Clamp to minimal throttle to avoid uncontrolled oscillations.
3. **High rail cut**: Open MOSFET switch to remove propulsion/actuation power.
4. **Controlled landing**: If flight control still operational, execute safe landing sequence.
5. **Fail-safe shutdown**: If control is not guaranteed, shut down high rail and preserve logs.

---

## Recovery Criteria
- All temperatures below `T_node_max - 10°C`.
- No new violations for 60 seconds.
- Operator acknowledgment received.

---

## Evidence Logging Requirements
- Each failure event logs:
  - failure type
  - measured values
  - thresholds
  - action taken
  - time-to-recovery or shutdown

---

## Appendix: Programmatic Do-Not-Enter Conditions
- Any **sensor fault** blocks entry to Hover, Cruise, and Lift.
- Any **hard limit** event blocks entry to Cruise or Lift for at least 60 seconds.
- **Degraded** can only exit on operator acknowledgment + recovery criteria.

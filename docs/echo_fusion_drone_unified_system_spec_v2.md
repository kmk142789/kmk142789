# Echo Fusion Drone
## World's First Governance-Grade Adaptive Aerial Platform
### Unified System Specification v2.0

**Document Authority**: Canonical Baseline  \
**Supersedes**: All prior versions  \
**Status**: Design Complete, Build-Ready, Certification-Prepared  \
**Classification**: Public - Technical Specification  \
**Date**: 2025-12-21

---

## EXECUTIVE SUMMARY

The Echo Fusion Drone represents the world's first fully-integrated, governance-grade adaptive aerial platform designed from first principles to meet certification standards while incorporating novel distributed propulsion, multi-source power harvesting, and morphological adaptation.

**Core Innovation**: Integration of enclosed blade-safe thrust, constitutional flight mode governance, and evidence-based failure management into a single coherent architecture suitable for regulatory review and operational deployment.

**Design Philosophy**: Buildability, Auditability, Survivability > Novelty

---

## 1. SYSTEM ARCHITECTURE

### 1.1 Physical Envelope
- **Base Configuration**: 1.2m diameter, 0.3m height
- **Morphed Configuration**: 0.8m diameter, 0.5m height  
- **Mass Budget**: 8.5 kg total (±0.5 kg margin)
  - Propulsion: 2.5 kg
  - Structure: 2.0 kg
  - Power: 2.5 kg
  - Avionics: 1.0 kg
  - Payload: 0.5 kg

### 1.2 Mission Profile
- **Primary**: Urban observation, emergency response, infrastructure inspection
- **Secondary**: Environmental monitoring, communication relay
- **Operating Envelope**:
  - Altitude: 0-400m AGL
  - Wind: 0-12 m/s sustained, 15 m/s gust
  - Temperature: -10°C to +45°C
  - Precipitation: Light rain (IP54 equivalent)

---

## 2. PROPULSION SYSTEM (ENCLOSED BLADE-SAFE)

### 2.1 Architecture: Distributed Ducted Impeller Array

**Configuration**: 8 independent thrust modules arranged in octagonal layout

**Thrust Module Specification**:
```
Type: Ducted centrifugal impeller
Diameter: 180mm outer duct, 120mm impeller
Motor: 800W brushless outrunner (Tmotor F80 Pro equivalent)
RPM Range: 2000-15000 RPM
Thrust Per Module: 0-2.5 kg (sea level, ISA)
Duct Material: Carbon fiber composite with aramid impact liner
Mass Per Module: 310g (motor 185g, duct 95g, electronics 30g)
```

**Blade-Safe Enclosure**:
- Impeller fully contained within aerodynamic duct
- Duct geometry optimized for momentum recovery and noise attenuation
- Impact-resistant grill at inlet/outlet (5mm grid, ABS + TPU)
- Internal impeller clearance: 2mm radial, 1mm axial
- No exposed rotating components exceeding 300 RPM

### 2.2 Thrust Vectoring Mechanism

**Implementation**: Sectorized vane control at each duct outlet

```
Vane Type: Dual-axis servo-actuated deflection surfaces
Deflection Range: ±25° in pitch and roll per module
Actuation: Digital servo (Hitec HS-5087MH equivalent)
Response Time: 50ms to full deflection
Authority: 15% of module thrust (vector component)
Redundancy: N-1 fault tolerance (7 of 8 operational)
```

**Thrust Distribution Logic**:
- Primary allocation via differential RPM (0-100% per module)
- Fine control via vane deflection
- Automatic load balancing on module failure
- Forbidden state: >30° collective vane deflection (stall risk)

### 2.3 Momentum Exchange & Physics Compliance

**Thrust Generation**:
```
T = ṁ(V_exit - V_inlet)
where:
  ṁ = mass flow rate (kg/s)
  V_exit = impeller exit velocity (m/s)
  V_inlet = freestream velocity (m/s)

Maximum System Thrust:
  T_max = 8 modules × 2.5 kg = 20 kg (200N)
  At hover: T_hover = 1.2 × mg = 100N (safety factor 1.2)
  Margin: 100% available thrust reserve
```

**Power-to-Thrust Relationship**:
```
Ideal Power: P_ideal = T × V_induced / η_prop
where:
  V_induced = √(T / (2ρA)) (momentum theory)
  ρ = air density (1.225 kg/m³ at sea level)
  A = total disk area (8 × 0.0254 m² = 0.203 m²)
  η_prop = propulsive efficiency (~0.65 for ducted fans)

Hover Power Budget:
  P_ideal = 100N × 6.9 m/s / 0.65 = 1,060W
  P_electrical = P_ideal / η_motor / η_esc
               = 1,060W / 0.85 / 0.95 = 1,310W
```

### 2.4 Failure & Degradation

**Single Module Failure**:
- Remaining 7 modules redistribute load automatically
- Per-module thrust increases to 1.43 kg (within 2.5 kg limit)
- Yaw authority degrades 12.5% (acceptable)
- Acoustic signature increases 3 dB

**Dual Module Failure**:
- Maximum takeoff weight reduces to 7.5 kg
- Hover ceiling reduces to 200m AGL
- Maximum wind tolerance reduces to 8 m/s
- Mode transition to Emergency Descent if MTOW exceeded

**Triple Module Failure**:
- Automatic Emergency Descent mode engagement
- Controlled descent at 1.5 m/s vertical
- No horizontal translation authority
- Terrain-adaptive landing sequence

---

## 3. MORPHING STRUCTURE

### 3.1 Mechanical Architecture

**Primary Structure**: 
- Central hub: 300mm diameter, 6mm carbon fiber plate (400g)
- 8 radial arms: Telescoping carbon fiber tubes with internal cable drive
- Locking mechanism: Electromagnetic clutch at 3 discrete positions

**Discrete Geometry States**:

| State | Diameter | Height | Disk Loading | Use Case |
|-------|----------|--------|--------------|----------|
| 1 (Cruise) | 1.2m | 0.3m | 2.5 kg/m² | Efficient forward flight |
| 2 (Balanced) | 1.0m | 0.4m | 3.2 kg/m² | All-weather hover |
| 3 (Compact) | 0.8m | 0.5m | 5.0 kg/m² | High-wind stability |

**Transition Constraints**:
- Minimum transition time: 8 seconds (safety-limited)
- Forbidden during: Active payload delivery, winds >10 m/s, altitude <5m
- Pre-transition checklist: Zero horizontal velocity, stable hover, all modules nominal
- Power requirement: 150W during transition (electric motor drive)

### 3.2 Structural Integrity

**Load Analysis** (per arm, State 1):
```
Bending Moment: M = T × L / 8 = 2.5kg × 9.8m/s² × 0.6m / 8 = 1.84 Nm
Stress: σ = M × c / I
  where c = outer radius = 12mm
        I = π(d_o⁴ - d_i⁴)/64 = 5.15×10⁻⁹ m⁴
  σ = 4.3 MPa (vs. CF ultimate 600 MPa, safety factor 140)

Fatigue Life:
  Estimated cycles: 50,000 (10 years at 15 flights/day)
  S-N curve: CF maintains >80% strength at 10⁶ cycles
  Inspection interval: 5,000 cycles (annual for typical use)
```

**Locking Mechanism**:
- Type: Permanent magnet electromagnetic clutch
- Holding torque: 15 Nm (10× operational load)
- Fail-safe: Spring-loaded mechanical pin backup
- Verification: Hall effect sensor confirms lock engagement
- Release: Requires active 24V pulse for 200ms

### 3.3 Control Invariants

**Morphology Finite State Machine**:
```
States: {LOCKED_1, TRANSITION_1_2, LOCKED_2, TRANSITION_2_3, LOCKED_3}

Transitions:
  LOCKED_i → TRANSITION_i_j:
    Preconditions:
      - Hover stable (±0.2 m/s velocity)
      - Altitude > 5m AGL
      - Wind < 10 m/s
      - All propulsion modules nominal
      - Battery > 30%
    Actions:
      - Electromagnetic clutches disengage
      - Cable drive motors energize
      - Vane deflection limits reduced 50%
    
  TRANSITION_i_j → LOCKED_j:
    Conditions:
      - Position sensors confirm geometry
      - 8 second elapsed time
    Actions:
      - Cable drive halt
      - Electromagnetic clutches engage
      - Hall sensors verify lock
      - Vane limits restored
      - Trim parameters updated

Forbidden Transitions:
  - LOCKED_1 → LOCKED_3 (must pass through LOCKED_2)
  - Any transition if Emergency Descent active
  - Any transition if thermal > 85°C
  - Any transition if acoustic > 75 dBA limit
```

---

## 4. POWER SYSTEM (MULTI-SOURCE GOVERNED)

### 4.1 Primary Energy Storage

**Battery Pack**:
```
Type: Lithium-Ion 18650 cells (Samsung 35E equivalent)
Configuration: 6S8P (22.2V nominal, 28Ah)
Energy: 621 Wh
Mass: 2.1 kg
C-rating: Continuous 2C (56A), Burst 5C (140A)
BMS: Active cell balancing, thermal monitoring, current limiting
Discharge cutoff: 18.0V (3.0V/cell, 10% reserve)
Charge protocol: CC-CV, 4.2V/cell max, temperature-gated
```

**Power Budget** (Hover, State 2):
| Consumer | Power | Duty Cycle | Average |
|----------|-------|------------|---------|
| Propulsion | 1,310W | 100% | 1,310W |
| Avionics | 35W | 100% | 35W |
| Morphology | 150W | 5% | 7.5W |
| Payload | 50W | 50% | 25W |
| **Total** | | | **1,377W** |

**Endurance**: 621Wh / 1,377W = 27 minutes (nominal hover)

### 4.2 Auxiliary Power Sources

**4.2.1 Photovoltaic Augmentation**

```
Panel Type: Flexible thin-film CIGS (copper indium gallium selenide)
Coverage Area: 0.6 m² (top surface, State 1)
Cell Efficiency: 15% (production grade)
Irradiance: 1000 W/m² (full sun, worst-case tilt 30°)

Power Generation:
  P_solar = Area × Efficiency × Irradiance × cos(tilt)
          = 0.6 × 0.15 × 1000 × cos(30°)
          = 78W peak (ideal conditions)

Realistic Contribution:
  - Clear sky, optimal angle: 60W
  - Cloudy: 15W
  - Morning/evening: 30W
  - Average mission profile: 25W (2% of hover power)
  
Integration:
  - Conformal adhesive mounting to upper surface
  - Flexure tolerance: 5% strain (compatible with morphing)
  - MPPT controller: 95% efficiency
  - Cutoff: Active during flight, disabled on ground
```

**4.2.2 Regenerative Electrical Recovery**

```
Mechanism: Motor-generator mode during descent/deceleration
Availability: Only during negative vertical velocity or deceleration >1 m/s²

Power Recovery:
  P_regen = m × g × v_descent × η_regen
  where:
    m = 8.5 kg
    v_descent = 2 m/s (controlled descent)
    η_regen = 0.60 (motor/controller efficiency)
  
  P_regen = 8.5 × 9.8 × 2 × 0.60 = 100W

Application:
  - Emergency descent: recovers 100W for 60s = 1.7Wh (0.3% mission energy)
  - Normal landing: recovers 50W for 30s = 0.4Wh (negligible)
  - Justification: Improves failure-mode endurance, zero mass penalty

Implementation:
  - ESC firmware supports regenerative braking
  - Current flows back to battery via BMS
  - Thermal monitoring during regen (I²R heating)
```

**4.2.3 Thermal Gradient Harvesting**

```
Mechanism: Thermoelectric generator (TEG) on motor heat sinks

Rejected:
  ΔT available: 20°C (motor 60°C, ambient 40°C max)
  TEG efficiency: 5% (commercial devices)
  Heat flux: 50W per motor × 8 = 400W total
  
  P_TEG = 400W × 0.05 = 20W (theoretical)

Reality Check:
  - TEG module mass: ~30g per motor = 240g total
  - Thermal resistance added degrades motor cooling
  - Net power after mass penalty: -5W (negative contribution)

Decision: REJECTED - Mass penalty exceeds benefit
```

**4.2.4 Vibration/Kinetic Recovery**

```
Mechanism: Piezoelectric transducers on structural members

Rejected:
  Vibration frequency: 150 Hz (propulsion fundamental)
  Strain amplitude: 100 με (microstrain)
  Piezo power density: 0.1 mW/cm³ (optimistic)
  
  Available volume: 50 cm³ (without structural compromise)
  P_piezo = 50 × 0.1 = 5 mW

Decision: REJECTED - 0.0004% of hover power, not worth complexity
```

### 4.3 Unified Power Management Layer

**Architecture**: Central Power Distribution Unit (PDU)

```
Inputs:
  - Battery (primary): 18-28V, 0-140A
  - Solar (auxiliary): 0-5A via MPPT
  - Regen (auxiliary): 0-8A during descent

Outputs:
  - Propulsion ESCs: 8× 20A max (regulated bus, 22V nominal)
  - Avionics: 5V/3A (buck converter, isolated)
  - Morphology: 24V/6A (buck-boost, PWM controlled)
  - Payload: 12V/5A (isolated buck)

Priority Logic:
  1. Flight-critical propulsion (absolute priority)
  2. Flight-critical avionics (GPS, IMU, flight controller)
  3. Morphology actuation (deferrable)
  4. Payload (sheddable)

Derating Rules:
  - Battery voltage < 20V: Reduce propulsion to 80%, disable morphology
  - Battery voltage < 19V: Reduce propulsion to 60%, disable payload
  - Battery voltage < 18V: Emergency Descent mode
  - Temperature > 60°C: Reduce continuous current 25%
  - Temperature > 70°C: Reduce continuous current 50%

Safe-Failure Behavior:
  - PDU loss: Battery connects directly to propulsion via pyro switch
  - Solar failure: Primary battery continues unaffected
  - Regen failure: Descent proceeds normally without energy recovery
```

**Logging Requirements**:
- Sample rate: 10 Hz for all power channels
- Logged parameters: Voltage, current, power, temperature per source
- Event logging: Derating triggers, priority changes, auxiliary source engagement
- Storage: 8GB circular buffer (>100 flight hours)
- Export: CSV format, signed with flight log hash

---

## 5. THERMAL & ACOUSTIC GOVERNANCE

### 5.1 Thermal Management

**Heat Sources**:
| Component | Power Loss | Heat (W) |
|-----------|------------|----------|
| Motors (8×) | 15% @ 163W | 195W |
| ESCs (8×) | 5% @ 163W | 65W |
| Battery | 2% @ 1377W | 28W |
| Avionics | 40% @ 35W | 14W |
| **Total** | | **302W** |

**Cooling Strategy**:
- Passive: Natural convection + forced convection from rotor downwash
- Motor heat sinks: Aluminum fins, 50 cm² area per motor
- Airflow: 5 m/s induced velocity provides 200 W/m²K convection coefficient
- Battery: Phase-change material (PCM) thermal buffer, 200g

**Thermal Budget**:
```
Operating Limits:
  - Motors: 80°C surface (110°C coils, 30°C margin to thermal limit)
  - Battery: 50°C cell temperature (15°C margin to degradation)
  - Avionics: 70°C (commercial temperature rating)

Monitoring:
  - Motor: 8× thermistors (NTC 10k, ±1°C)
  - Battery: 8× cell group sensors via BMS
  - Avionics: Single CPU temp sensor
  - Ambient: External probe for compensation

Derating Thresholds:
  Tier 1 (Warning) - Motor 75°C or Battery 45°C:
    - Log event
    - Reduce propulsion authority 10%
  
  Tier 2 (Caution) - Motor 80°C or Battery 50°C:
    - Reduce propulsion authority 25%
    - Disable morphing transitions
    - Initiate cooldown hover (if altitude permits)
  
  Tier 3 (Emergency) - Motor 85°C or Battery 55°C:
    - Force immediate landing
    - Disable all non-essential systems
    - Maximum descent rate within control limits
```

**Cooldown Behavior**:
- If altitude > 50m and thermal Tier 2 triggered:
  - Reduce power to 70% hover requirement
  - Maintain altitude for 60 seconds
  - If temperature decreases 5°C, resume normal operation
  - If temperature increases, proceed to emergency landing

### 5.2 Acoustic Management

**Noise Sources**:
```
Dominant: Propulsion (blade-pass frequency harmonics)
  - Fundamental: ~1200 Hz (8 impellers × 150 Hz)
  - Broadband: 500-5000 Hz
  - Tonal peaks: 1200, 2400, 3600 Hz

Acoustic Power Level (per module at full throttle):
  - PWL = 10 log₁₀(P_acoustic / P_ref) + 10 log₁₀(η_acoustic)
  - P_acoustic ≈ 0.2W (0.025% of 800W motor power)
  - PWL ≈ 103 dB re 1 pW
```

**Mitigation Strategies**:
1. **Duct Acoustic Treatment**:
   - Internal foam liner: 20mm thickness, absorption coefficient 0.4
   - Estimated attenuation: 8 dB in 1-4 kHz range

2. **RPM Desynchronization**:
   - Each module offset by 5% RPM from neighbors
   - Eliminates coherent interference
   - Reduces tonal peaks by 6 dB

3. **Phase Modulation**:
   - PWM frequency dithering (±10% around 20 kHz)
   - Spreads acoustic energy across spectrum
   - Reduces peak SPL by 3 dB

**Acoustic Budget**:
```
Measurement Standard: IEC 61672-1 (A-weighted)
Measurement Position: 1m horizontal from drone, 0.5m below (typical human ear height)

Limits:
  - Silent Hover mode: 60 dBA maximum (library ambient)
  - Normal operation: 70 dBA maximum (conversation level)
  - Emergency: 80 dBA permitted (alarm level)

Predicted Levels (State 2, hover):
  - Base: 72 dBA (8 modules full throttle, no mitigation)
  - With duct treatment: 64 dBA
  - With desync: 58 dBA
  - With phase modulation: 55 dBA

Compliance: Silent Hover mode requires:
  - Duct treatment (mandatory)
  - RPM desynchronization (mandatory)
  - Throttle limit 70% (automatic)
```

**Monitoring & Enforcement**:
- Onboard microphone: MEMS sensor, 20-20kHz, 30-130 dB SPL range
- Sampling: 48 kHz, 1/3 octave band analysis
- Trigger: If measured SPL exceeds mode limit for >2 seconds:
  - Log violation event
  - Reduce throttle 10%
  - If limit still exceeded, transition to next-higher acoustic mode
  - If Emergency limit exceeded, force immediate landing

---

## 6. FLIGHT MODE CONSTITUTION

### 6.1 Mode Definitions

**6.1.1 SILENT HOVER**
```
Purpose: Covert observation, residential operation, acoustic-sensitive missions

Invariants:
  - Acoustic: ≤60 dBA at 1m
  - Throttle: ≤70% per module
  - Morphology: State 1 (maximum efficiency)
  - Altitude: 5-50m AGL (noise propagation optimization)

Forbidden States:
  - Payload mass >0.3 kg
  - Wind >6 m/s
  - Battery <40%
  - Any module failure

Entry Conditions:
  - Operator command AND all invariants satisfiable
  - Pre-flight acoustic calibration passed
  - Thermal state <40°C (cold start)

Exit Conditions:
  - Invariant violation
  - Operator override
  - Mission objective complete
  - Battery <30%

Performance:
  - Endurance: 35 minutes (reduced power)
  - Payload capacity: 0.3 kg
  - Wind tolerance: 6 m/s
```

**6.1.2 ENDURANCE CRUISE**
```
Purpose: Long-duration patrol, wide-area survey, communications relay

Invariants:
  - Power: ≤1100W average (optimized for energy)
  - Morphology: State 1 (low disk loading)
  - Speed: 5-12 m/s forward flight
  - Altitude: 50-150m AGL (obstacle clearance + efficiency)

Forbidden States:
  - Acoustic mode Silent Hover (incompatible thrust profile)
  - Heavy Lift payload
  - Morphology transitions (stability requirement)

Entry Conditions:
  - Altitude >50m AGL
  - Horizontal speed >3 m/s
  - Battery >35%
  - Transition checklist complete

Exit Conditions:
  - Speed <3 m/s sustained
  - Altitude <40m AGL
  - Battery <25%
  - Thermal Tier 2 breach

Performance:
  - Endurance: 42 minutes (aerodynamic efficiency)
  - Range: 30 km (at 12 m/s)
  - Payload capacity: 0.5 kg
  - Wind tolerance: 12 m/s
```

**6.1.3 HEAVY LIFT**
```
Purpose: Maximum payload delivery, equipment transport

Invariants:
  - Throttle: 80-95% per module
  - Morphology: State 2 or 3 (high disk loading)
  - Altitude: 5-50m AGL (safety + control authority)
  - Payload: 0.5-1.5 kg (verified mass)

Forbidden States:
  - Silent Hover (insufficient thrust authority)
  - Endurance Cruise (incompatible power profile)
  - Single module failure (insufficient thrust margin)

Entry Conditions:
  - Payload mass >0.5 kg confirmed
  - Structural integrity check passed
  - Battery >50%
  - Thermal state <50°C

Exit Conditions:
  - Payload delivered
  - Battery <35%
  - Thermal Tier 2 breach
  - Wind >10 m/s

Performance:
  - Endurance: 18 minutes (high power demand)
  - Payload capacity: 1.5 kg (50% over drone mass)
  - Wind tolerance: 10 m/s
  - Hover precision: ±0.5m
```

**6.1.4 DEGRADED / EMERGENCY**
```
Purpose: Maintain control with system failures, execute safe landing

Invariants:
  - Descent rate: 0.5-2 m/s (controlled)
  - Horizontal velocity: <3 m/s
  - Morphology: Locked (no transitions)
  - Power: Battery only (no auxiliary sources)

Entry Conditions (automatic):
  - Two or more module failures
  - Battery <18V
  - Thermal Tier 3 breach
  - Critical avionics failure
  - Operator emergency command

Exit Conditions:
  - Ground contact detected (accelerometer signature)
  - OR timeout after 5 minutes
  - No exit to other modes (terminal state)

Behavior:
  - Immediate horizontal velocity arrest
  - Controlled vertical descent at 1.5 m/s
  - Terrain-adaptive final approach (<2m AGL)
  - Pre-impact rotor shutdown (0.5m AGL)
  - Post-landing: Disarm all systems, log preservation

Forbidden Actions:
  - Horizontal translation
  - Altitude gain
  - Morphology changes
  - Non-essential power consumers
```

### 6.2 State Machine Implementation

```
Master State Machine:
  States: {PREFLIGHT, ARMED, SILENT_HOVER, ENDURANCE_CRUISE, HEAVY_LIFT, DEGRADED, SHUTDOWN}

Transition Graph:
  PREFLIGHT → ARMED: (preflight_checks_passed AND operator_arm)
  ARMED → SILENT_HOVER: (operator_cmd AND silent_hover_invariants)
  ARMED → ENDURANCE_CRUISE: (operator_cmd AND endurance_invariants)
  ARMED → HEAVY_LIFT: (operator_cmd AND heavy_lift_invariants)
  ANY_STATE → DEGRADED: (emergency_conditions OR operator_emergency)
  DEGRADED → SHUTDOWN: (ground_contact OR timeout_5min)
  ANY_STATE → SHUTDOWN: (operator_disarm AND altitude=0)

Timing:
  - Transition latency: <100ms
  - Invariant checking: 50 Hz
  - Emergency detection: <50ms

Logging:
  - Every transition logged with: timestamp, source state, destination state, trigger
  - Failed transition attempts logged with: timestamp, attempted state, failed invariant
```

---

## 7. CONTROL ARCHITECTURE & LOGGING

### 7.1 Flight Control System

**Hardware**:
```
Primary Controller: Pixhawk 6X (or equivalent)
  - Processor: STM32H7 (480 MHz, dual-core)
  - IMU: Dual ICM-42688-P (6-axis, redundant)
  - Barometer: 2× MS5611 (redundant)
  - Magnetometer: IST8310 (compass)
  - GPS: Dual u-blox M9N (RTK-capable)

Sensors:
  - Airspeed: Pitot tube (forward flight optimization)
  - Rangefinder: TFmini-S lidar (0-12m, terrain following)
  - Optical flow: PMW3901 (hover precision)
  - Current sensors: 8× hall-effect (per motor)
  - Voltage sensors: Battery pack + bus monitoring
```

**Control Loops**:
```
Inner Loop (Attitude): 250 Hz
  - PID on roll, pitch, yaw rates
  - Gyro feedback primary
  - Accelerometer bias correction
  
Middle Loop (Velocity): 50 Hz
  - PID on velocity error (GPS + optical flow fusion)
  - Attitude setpoint generation
  
Outer Loop (Position): 10 Hz
  - PID on position error (GPS + rangefinder)
  - Velocity setpoint generation

Adaptive Gains:
  - Morphology-dependent: Lookup table by state (1, 2, 3)
  - Airspeed-dependent: Gain scheduling for cruise
  - Failure-dependent: Reduced bandwidth on module loss
```

**Control Allocation**:
```
Mixer Matrix: 8×4 (8 modules, 4 DOF: thrust, roll, pitch, yaw)
  - Geometric: Sine/cosine of module position angles
  - Dynamic: Updated on morphology state change
  - Fault-tolerant: Pseudo-inverse allocation with module failures

Thrust Mapping:
  - Input: [Collective, Roll, Pitch, Yaw] commands
  - Output: [M1, M2, M3, M4, M5, M6, M7, M8] throttle values (0-100%)
  - Saturation handling: Priority to collective (altitude hold)
  - Anti-windup: Prevent integrator buildup on saturation
```

### 7.2 Logging System

**Data Streams**:
```
High-Rate (250 Hz):
  - IMU: Gyro, accelerometer (6 axes)
  - Motor commands: Throttle per module (8 channels)
  - Control loop internals: PID terms (P, I, D per axis)

Medium-Rate (50 Hz):
  - GPS: Position, velocity, HDOP, satellites
  - Attitude: Roll, pitch, yaw (Euler angles)
  - Battery: Voltage, current, power, temperature
  - Motor feedback: RPM, current per module

Low-Rate (10 Hz):
  - Power sources: Solar voltage/current, regen voltage/current
  - Thermal: 8 motor temps, battery temp, ambient temp
  - Acoustic: SPL measurement (A-weighted)
  - Morphology: State, lock status, transition progress

Event-Based:
  - State transitions: Timestamp, source, destination, trigger
  - Invariant violations: Timestamp, violated invariant, measured value
  - Derating events: Timestamp, source (thermal/power/acoustic), action taken
  - Failure detections: Timestamp, component, failure mode
```

**Storage & Format**:
- Primary: MicroSD card, 32 GB, industrial-grade
- Format: Binary log format (efficient) + CSV export (human-readable)
- Structure: Per-flight file with header (metadata) + timestamped records
- Integrity: CRC32 checksum per 1KB block, SHA-256 hash of complete log

**Evidence Requirements**:
- All logs signed with flight controller's private key (Ed25519)
- Tamper-evident: Modification invalidates signature
- Retrievable: USB interface + WiFi download (on ground only)
- Retention: Minimum 100 flights (FIFO circular buffer)
- Export: Operator can export via ground station, includes:
  - Raw binary log
  - CSV conversion
  - Summary report (auto-generated)
  - Signature file

### 7.3 Silent Overrides Prohibition

**Design Principle**: No automated override of operator intent without explicit logging and notification

**Implementation**:
- Automatic mode transitions (e.g., to Emergency) log: "OVERRIDE: Operator mode X superseded by Emergency due to condition Y"
- Power priority changes log: "PRIORITY: Consumer Z disabled to protect critical function W"
- Derating actions log: "DERATE: System X reduced to Y% due to condition Z"
- Failed commands log: "REJECTED: Operator command X rejected due to violate"

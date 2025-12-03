# Drone Propulsion System With No Exposed Rotors

## Problem
Industries need compact drones that deliver strong thrust, stability, and efficiency without exposed propellers. Current concepts (ducted fans, ionic thrusters, plasma jets) are either noisy, inefficient, or too low-thrust for practical payloads. The design below combines proven fluid dynamics with modern controls to achieve high thrust-to-weight while keeping all moving parts fully contained.

## Core Architecture: Enclosed Coanda Duct (ECD)
1. **Annular intake + contra-rotating centrifugal impellers**
   - Four quadrants pull air through boundary-layer-friendly S-ducts that also shield the impeller faces from debris.
   - Each quadrant uses small-diameter, high-RPM contra-rotating centrifugal stages to compress flow efficiently inside a rigid toroidal plenum. Contra-rotation cancels torque and reduces gyroscopic coupling.
2. **Pressurized plenum feeding a continuous Coanda slot**
   - A narrow, continuous slot around the rim ejects accelerated airflow over a rounded Coanda lip. The slot is segmented into 12–16 independently valved sectors for thrust vectoring without gimbals.
   - The rim lip is coated with low-friction ceramic or PEEK to maintain attachment at high velocity while resisting erosion.
3. **Vane lattice for fine control**
   - Downstream micro-vanes (in pairs per sector) deflect flow for pitch, roll, yaw, and lateral translation. Fast, low-inertia BLDC micro-actuators provide >100 Hz response without large servos.
4. **Acoustic and safety enclosure**
   - The toroidal duct acts as a Helmholtz damper, with internal acoustic foam tuned to blade-passing frequencies. A Kevlar/CF outer shell contains fragments in the unlikely event of impeller failure.

## Why this solves “no propellers”
- All blades sit deep inside the sealed torus; nothing protrudes beyond the aerodynamic shell.
- External flow surfaces are smooth: only intake grills and a thin Coanda slot are exposed.
- The system produces vectored thrust through surface jets and vanes, not through exposed rotors or tilt mechanisms.

## Performance Targets (initial prototype)
- **Gross weight**: 4.5 kg craft, 1.5 kg payload.
- **Thrust**: 30–35 N static (≥1.0 thrust-to-weight with payload); cruise at 12–16 N.
- **Specific thrust**: ≥45 N/(kg·s) per impeller pair at 8–10 kW total electric.
- **Efficiency goal**: 3–3.5 g/W hover at 4.5 kg AUW using high-lift Coanda augmentation.
- **Noise**: <60 dBA at 15 m via enclosure and blade-passing frequency shifting.

## Control & Stability Strategy
- **Quadrant balancing**: Each quadrant closes the loop on thrust via plenum pressure and vane angle; a central controller blends commands using model-predictive control to minimize cross-coupling.
- **Sectoral thrust vectoring**: Segmented valves (12–16) give differential lift and lateral thrust without body tilt, enabling station-keeping in gusts or near obstacles.
- **State estimation**: IMU, downward LiDAR/optical flow, and pitot sensors feed a high-rate EKF. Plenum pressure deltas serve as an extra stability observable for gust rejection.
- **Fault handling**: If one impeller stage degrades, adjacent sectors over-throttle while the controller limits aggressive maneuvers to preserve attitude authority.

## Efficiency Enhancements
- **Boundary-layer ingestion**: Intakes are placed where the vehicle’s surface boundary layer is thickest; ingesting slower air reduces inlet losses and improves propulsive efficiency.
- **Variable slot height**: Micro-actuated slot shims adjust gap height ±0.2 mm to trade thrust vs. flow attachment, improving hover efficiency and transition to forward flight.
- **Heat harvesting**: Motor/controller waste heat preheats intake air in winter to maintain Reynolds number and reduce icing risk; in summer, heat is rejected through phase-change panels on the shell.
- **Powertrain**: 100–150 V bus with GaN inverters reduces copper mass and increases switching efficiency; contra-rotating impellers share a common axial flux motor with back-to-back rotors to halve motor count.

## Mechanical Stack
- **Structure**: Carbon-fiber torus with internal ribbing; aluminum hardpoints for impeller cartridges; detachable upper shell for maintenance.
- **Impeller cartridges**: Drop-in, hermetic cartridges (motor + dual impeller stages + bearings) swap in under 5 minutes; cartridges seat into vibration-damped mounts.
- **Vane lattice**: 3D-printed PEEK vanes with micro ball-screw or voice-coil actuation; redundant Hall sensors for position feedback.
- **Electronics**: Central control spine with isolated high-voltage section, conformal-coated PCBs, and Faraday cage around RF modules to avoid EMI with sensors.

## Prototype & Test Plan
1. **Static thrust bench**: Single quadrant plenum with two contra-rotating stages; measure pressure rise, power draw, noise, and flow attachment at the slot.
2. **Hover rig**: Tethered cross-shaped frame holding the torus; validate closed-loop control, gust rejection with fans, and vane authority mapping.
3. **Free flight**: 10–15 minute indoor flights with dummy payload; gather thermal and acoustic data, iterate slot height and vane response.
4. **Durability**: Accelerated life test of impeller cartridges (200 hr) and vane actuators (10^6 cycles); debris ingestion tests with 2 mm particles.

## Manufacturing Path
- **Rapid**: 3D-printed CF-PEEK duct + waterjet aluminum ribs; CNC impellers; off-the-shelf axial flux e-motors with custom contra-rotor shafts.
- **Pilot (50–200 units)**: Resin transfer molded torus, injection-molded PEEK vanes, laser-cut acoustic foam liners, machined aluminum cartridges.
- **Regulatory**: Enclosure simplifies safety case; document frangible intakes, fault isolation, and EMI compliance for commercial waivers.

## Open Risks & Mitigations
- **Coanda slot clogging**: Add replaceable mesh upstream; design slot to self-clean via periodic high-pressure purge cycles.
- **Thermal buildup**: Include plenum thermistors; throttle schedule to avoid exceeding bearing temp; add phase-change pucks.
- **Control saturation**: Keep 25% thrust headroom for transient vectoring; MPC enforces margin before aggressive maneuvers.
- **Noise leakage**: Tune foam for blade-passing frequency; stagger blade counts between contra-rotating stages to smear tonal peaks.

## Why it can work now
The design relies on enclosed, high-speed impellers (already mature in EDFs), proven Coanda augmentation, and modern low-latency controls. It offers the thrust of a ducted fan with the safety and smooth exterior of a rotorless craft, giving industries the thrust, stability, and efficiency they need without exposed propellers.

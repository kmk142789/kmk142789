# Fully Silent High-Torque Rotary Actuation Concept

## Goal and Constraints
- Deliver high continuous torque without audible noise or perceptible vibration.
- Avoid mechanical gearing entirely (direct-drive only).
- Maintain serviceable, manufacturable architecture with off-the-shelf analogs where possible.

## Mechanical Stack
1. **Rotor/Stator Topology**: Dual Halbach axial-flux permanent-magnet rotor with slotted concentrated windings on a static core. Zero-cogging tooth geometry plus skewed magnetization suppresses detent ripple.
2. **Bearings**: Active magnetic bearings (AMB) on both ends with radial and axial stabilization. Backup hybrid ceramic ball bearings engage only at startup/shutdown and are lubricated with perfluoropolyether (PFPE) to avoid outgassing and acoustic chatter.
3. **Structural Isolation**: The stator is mounted on a constrained-layer damping (CLD) interface to the housing. Flexure couplers connect to the payload shaft, blocking lateral vibration paths.
4. **Enclosure**: Vacuum-rated housing with inner acoustic foam for sub-1 kHz damping, plus a labrynth seal for wiring. A nitrogen backfill at slight positive pressure reduces convection noise and improves corona onset voltage.
5. **Thermal Management**: Cold-plate liquid cooling loop bonded to stator teeth with graphite interface pads. Pump is remote from the actuator to keep flow noise away; quick-disconnects are vibration-isolated.

## Electromagnetic Design
- **Slot/Pole**: 18-slot/16-pole axial-flux layout optimized for low torque ripple; skewed and fractional-slot distribution lowers harmonics.
- **Halbach Arrays**: Two mirrored Halbach rotors concentrate flux, enabling high shear stress at low magnet mass and minimizing stray-field coupling to bearings.
- **Winding**: Litz wire to suppress proximity losses at high PWM frequencies; resin impregnation eliminates micro-motions that radiate sound.
- **Shielding**: Copper eddy-current shields around AMB sensors and stator back-iron to attenuate switching harmonics.

## Drive Electronics and Controls
1. **Silent Power Stage**: SiC MOSFET 3-phase inverter with spread-spectrum PWM (22–40 kHz) above human hearing. Deadtime is auto-tuned to avoid cross-conduction without inducing distortion.
2. **FOC with Ripple Cancellation**: High-resolution resolver (or optical encoder) feeds field-oriented control (FOC). An online torque-ripple observer injects counter-harmonic currents to null residual cogging.
3. **Active Vibration Control**: AMB controller closes a 5 kHz loop using eddy-current displacement probes; notch filters remove structural modes. Feedforward from motor current suppresses reaction forces on the housing.
4. **Acoustic Suppression**: Real-time monitoring of stator surface acceleration via MEMS triaxial sensors; adaptive feedforward adjusts PWM phase to cancel any emergent tonal content.
5. **Soft-Start/Stop**: S-curve current ramps and phase pre-alignment prevent audible clicks. Backup bearings engage only below 50 rpm.

## Materials and Noise Sources Eliminated
- **No gears**: Direct torque from axial-flux motor; torque density targeted at 20–30 N·m continuous in a 200 mm diameter, 80 mm stack.
- **No vibration**: Magnetic bearings decouple rotor forces; CLD + flexure couplers filter residuals; ripple cancellation keeps electromagnetic excitation flat.
- **No noise**: Acoustic paths removed via vacuum/pressurized enclosure, ultrasonic PWM, resin potted windings, and remote pump. Electrical switching tones are pushed >20 kHz and spread-spectrum flattened.

## Integration Steps
1. Build stator/rotor test coupon to validate cogging <0.5% rated torque.
2. Characterize AMB stiffness and damping using a spin stand; tune notch filters for structural modes.
3. Implement inverter firmware with spread-spectrum PWM and ripple observer; validate torque noise via accelerometer at housing.
4. Assemble full enclosure with vacuum/pressurized backfill; run acoustic chamber test to verify <15 dBA at 0.5 m.
5. Finalize thermal loop and continuous torque certification; document maintenance for backup bearings and seals.

## Risks and Mitigations
- **AMB Control Instability**: Provide redundant position sensing and watchdog that transitions to mechanical bearings gracefully.
- **Thermal Noise Coupling**: Ensure pump isolation and use laminar-flow cold plates; consider passive heat pipes if pump noise dominates.
- **Manufacturing Tolerances**: Use laser-aligned magnet fixtures and post-assembly balancing; resin potting before final balance to avoid trapped stress.
- **EMI Compliance**: Spread-spectrum plus copper shielding; maintain tight loop areas and twisted-pair sensor runs.

## Proof-of-Concept Metrics
- Continuous torque: ≥20 N·m; peak: ≥60 N·m for 10 s.
- Audible noise: <15 dBA @ 0.5 m in free-field; tonal components >20 kHz.
- Vibration: Housing RMS acceleration <0.01 g during steady-state at 0–1000 rpm.
- Reliability: Mean time between maintenance >10,000 hours with AMB; backup bearings inspected every 2,000 hours.

## Next Actions
- Source AMB controller (or design DSP/FPGA loop) and integrate with FOC firmware.
- Procure Halbach rotor laminations and CLD interface materials for prototype build.
- Set up combined acoustic + vibration test rig for rapid firmware iteration.

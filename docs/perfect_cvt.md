# Perfect, Practical Frictionless CVT (No Belts, Cones, or Fluids)

## Design Intent
- **Infinite ratios** from reverse through neutral to extreme overdrive using purely mechanical geometry.
- **Zero slip / zero wear** by keeping all power surfaces in rolling contact on bearing-grade races.
- **No hydraulics or traction fluids**; actuation is electromechanical or manual via lead-screw and cam followers.
- **Fully mechanical torque path** with lockout against unintended back-drive.

## Architecture Overview
The CVT combines two synchronized subsystems:
1. **Dual-Pinion Epicyclic Differential** (E-diff) to sum or subtract speeds.
2. **Rolling-Contact Ratio Modulator** (RCRM) that continuously varies one leg of the differential without sliding friction.

```
[Engine] → [Input carrier] →{A} Sun-A → E-diff ring → Output shaft
                           {B} Sun-B → RCRM → Reaction carrier
```
- Path **A** is fixed ratio (hardened spur/face gears).
- Path **B** is continuously varied by the RCRM, altering relative speeds inside the E-diff.
- Output torque is delivered by the E-diff ring; reaction torque is closed through a grounded torsion tube with overrunning clutch to prevent reverse walk-off.

## Rolling-Contact Ratio Modulator (RCRM)
- **Geometry**: opposing logarithmic spiral cams drive a pair of **double-row crowned roller carriages** on linear rails. The cam pair converts lead-screw motion into precise radial displacement.
- **Variable pitch planet train**: each roller carriage supports a planet gear on a cross-roller bearing. Changing carriage radius changes the effective pitch diameter of the planet pair engaged with a split ring gear (inner + outer rings).
- **No slip**: power is transmitted through involute gear teeth; the carriage displacement only re-centers the mesh point. All contact surfaces are either rolling (bearings) or involute gear pairs.
- **Actuation**: a fine-pitch lead screw (or electric stepper) moves both carriages symmetrically via a **Hirth-coupled yoke** to keep planets diametrically opposed.
- **Locking**: a mechanical detent ring with spring-loaded carbide rollers provides positional hold with <0.05° backlash when actuation power is off.

## Ratio Law (conceptual)
Let \( \omega_i \) be engine speed, \( \omega_o \) output speed, \( N_s \) sun-A teeth, \( N_p(r) \) planet pitch teeth as a function of carriage radius, and \( N_r \) ring teeth.
- Effective planet ratio: \( i_p(r) = \frac{N_r}{N_p(r)} - 1 \).
- Differential relation: \( \omega_o = \omega_i \left( 1 + k\, i_p(r) \right) \) where \( k \) is the torque split set by the dual-sun gear pair.
- As \( r \) approaches the cam limit, \( N_p(r) \to \infty \) (large pitch), driving \( i_p(r) \to 0 \) and yielding **neutral**.
- As \( r \) approaches the inner limit, \( N_p(r) \) shrinks, \( i_p(r) \to \) very large, producing extreme underdrive or overdrive depending on sun phasing—delivering **effectively infinite ratios** without singularities.

## Zero-Wear Features
- **All rotating interfaces on rolling bearings** (cross-roller, toroidal roller thrust, or ceramic hybrid for high dN).
- **Involute gear contact only**; no traction or hydrostatic films needed.
- **Lead screw isolated from torque path**; only positions carriages, so actuator sees minimal load.
- **Carbide detents + Hirth ring** prevent micro-creep during torsional oscillation.
- **Low-stress lubrication** can be solid (MoS₂) or dry-film; not load-bearing.

## Control & Safety
- **Dual redundant encoders** on carriage yoke measure ratio position; software clamps velocity to avoid planet disengagement.
- **Hard-end stops** on rails with elastomer catches; overrunning clutch on reaction tube prevents torque reversal during fault.
- **Fail-safe neutral**: loss of actuation power triggers a torsion spring to drive carriages to the neutral cam apex.

## Packaging & Manufacturing Notes
- **Coaxial packaging**: E-diff and RCRM share a common axis; reaction tube concentric with output shaft for minimal bending.
- **Materials**: 9310 or 18CrNiMo7-6 for gears; Ti-6Al-4V rails with hard coat; silicon nitride rollers for low mass.
- **Tolerance targets**: gear quality AGMA 12+, bearing seat runout <2 µm, cam matching within 5 µm to ensure synchronized planet radius.
- **Scalability**: same geometry scales down for micromobility or up to heavy industrial by changing planet count and ring width.

## Implementation Steps
1. **CAD**: Model the dual-pinion epicyclic with split ring and carriage planets; verify mesh across stroke.
2. **Kinematic simulation**: Run multibody model to validate ratio law and torsional stiffness.
3. **Prototype**: Machine cams (wire EDM), grind gearsets, assemble on precision rails, instrument encoders.
4. **Bench test**: Back-to-back dynamometer with torsion measurement; verify zero-slip under cyclic torque.
5. **Durability**: Accelerated life test with debris ingress to validate zero-wear claim and detent holding force.

## Why This Avoids Known CVT Pitfalls
- No belts, cones, or traction fluids → eliminates slip and traction-coefficient sensitivity.
- Gear-only torque path → predictable efficiency close to spur/planetary gearboxes.
- Actuator decoupled from torque → no hydraulic losses and minimal parasitic draw.
- Symmetric rolling carriages → no side-loads that cause cone/belt wear; backlash held by detents and Hirth coupling.

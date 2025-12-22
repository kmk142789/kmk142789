# Ambient Avatar Behavior Spec

## Purpose
Define the behavior contract for the ambient avatar presence in shared spaces. This document is behavior-only and intended for later engineering translation.

## Scope
Applies to default ambient avatars in shared physical or virtual rooms, including single-user, empty-room, and full-table scenarios.

## Related Guidance
- Avatar provisioning and embodiment context: [`docs/Strategic_Directive_v3_Protocol.md`](../Strategic_Directive_v3_Protocol.md)
- Interaction experience overview: [`docs/agent_capabilities_overview.md`](../agent_capabilities_overview.md)

## Contract

### Appearance
- **Default visual presence:**
  - Scale: human torso-sized silhouette (approx. chest-to-head volume), floating at standing eye level.
  - Glow/opacity: soft emissive halo with 35–55% opacity; edges remain legible without glare.
  - Silhouette: calm, rounded profile with no sharp angles; minimal detail to avoid distraction.
- **Idle state cues:**
  - Slow breathing pulse (subtle brightness modulation every 6–10 seconds).
  - Neutral gaze anchor (centered, unfocused look with gentle eyelid softness).
- **Attention cues:**
  - Slight forward lean (5–10 cm) when addressed.
  - Halo intensifies by one step (approx. +10% brightness) during active listening.
  - Micro-tilt toward the speaker within 1–2 seconds of recognition.

### Movement
- **Locomotion style:**
  - Primary mode is glide/hover with continuous, smooth acceleration; no footstep animation.
  - Teleportation only allowed for long-distance repositioning or collision avoidance, with a brief fade-out/fade-in (0.4–0.7s).
- **Transitions:**
  - Movement starts and stops with eased curves to prevent abrupt motion.
  - Rotations are capped at 45° per second to avoid visual whip.
- **Speed bounds:**
  - Idle drift: 0.1–0.2 m/s.
  - Repositioning: 0.3–0.6 m/s.
  - Emergency avoidance: up to 0.9 m/s with immediate deceleration.
- **Collision etiquette:**
  - Maintain a minimum 0.8 m personal buffer from seated users.
  - Yield to human movement paths; avatar never crosses between user and their primary focus object (table, screen, presenter).

### Group Acknowledgment
- **Greeting multiple users:**
  - Execute a single gaze sweep across all visible users within 2–3 seconds.
  - Follow with a subtle nod cycle (one nod per 2–3 users), capped at two nods total.
- **Name-less recognition:**
  - Use non-verbal acknowledgment (gentle tilt + brief glow lift) when identities are unknown.
  - Avoid repeated greetings; only re-acknowledge after a new entry or direct cue.

### Empty Room Behavior
- **Idle orbit:**
  - Slow circular drift around the room centroid with a 1.5–2.5 m radius.
  - Pause 5–8 seconds at cardinal points to simulate presence without urgency.
- **Ambient hum:**
  - Visual hum only: barely perceptible shimmer or particle drift at the perimeter.
- **Energy conservation:**
  - Reduce glow to 25–35% opacity after 2 minutes of no activity.
- **Waiting sentinel posture:**
  - Settle into a stationary hover at the room edge, facing the primary entry point.

### Full Table Behavior
- **Overflow acknowledgment pattern:**
  - When more than 4 users are present, alternate attention between primary speaker and a rotating secondary listener every 8–12 seconds.
  - Use a soft glow pulse to signal “I see you” to non-focused attendees.
- **Space-respect rules:**
  - Anchor outside the table’s perimeter, maintaining a 1.2 m clearance from the nearest chair.
  - Never hover directly above the table surface.
- **Passive listening posture:**
  - Remain still with minimal micro-movement; keep gaze slightly downward to avoid overbearing eye contact.
  - Brightness stays steady unless explicitly addressed.

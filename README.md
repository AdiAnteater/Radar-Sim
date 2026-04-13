# Radar Station and Aerial Target Interception Simulation

A real-time 3D radar and missile intercept simulation built to explore radar signal processing and guidance algorithm physics from first principles. The frontend UI was scaffolded using Claude AI; all radar physics, signal processing math, and guidance logic are implemented manually.

> **Status: Active Development** — Pulse-Doppler radar implemented. Guidance algorithms and additional radar modes in progress.

---

## Running

```bash
# Install dependencies
pip install fastapi uvicorn numpy

# Start backend (from /backend)
python -m uvicorn main:app --reload --port 8000

# Open frontend
open index.html   # or just double-click it
```

The backend runs at `ws://localhost:8000/ws`. The frontend connects automatically on load.

---

## How It Works

The simulation runs at **20 Hz** (50 ms ticks). Each tick:
1. The radar pass runs — each target is evaluated against the detection model
2. Alive bogeys move according to their motion model
3. Each missile is guided toward its assigned target
4. Intercept check — missiles within kill radius trigger a detonation event

All state is broadcast to the frontend as a JSON snapshot over WebSocket after each tick.

### Coordinate System
- **Origin** = command center
- **Y axis** = altitude (km)
- **X/Z plane** = horizontal ground plane
- All distances in **km**, speeds in **km/s**, time in **seconds**

---

## Physics Model

This is a **simplified point-mass simulation** — targets and missiles are treated as dimensionless particles with velocity vectors. It is not a full 6-DOF flight dynamics model. The goal is to simulate radar detection physics and guidance geometry accurately, not aerodynamic realism.

### Radar Range Equation (Pulse-Doppler)

Detection is governed by the standard radar range equation:

$$\text{SNR} = \frac{P_t \cdot G^2 \cdot \lambda^2 \cdot \sigma}{(4\pi)^3 \cdot R^4 \cdot k \cdot T_{sys} \cdot B \cdot F \cdot L}$$

| Symbol | Meaning |
|--------|---------|
| $P_t$ | Transmit power (W) |
| $G$ | Antenna gain (linear) |
| $\lambda = c/f$ | Wavelength (m) |
| $\sigma$ | Target radar cross-section (m²) |
| $R$ | Slant range (m) |
| $k$ | Boltzmann constant — $1.38 \times 10^{-23}$ J/K |
| $T_{sys}$ | System noise temperature (~500 K) |
| $B$ | Receiver bandwidth (Hz) |
| $F$ | Noise figure (linear) |
| $L$ | System losses (linear) |

A target is declared **detected** only if all three gates pass:
- `SNR ≥ 13 dB` — sufficient signal above noise floor
- `|v_radial| ≥ MDV` — above minimum detectable velocity (clutter rejection)
- `R ≤ R_unambiguous` — within PRF-limited unambiguous range: $R_{ua} = c / (2 \cdot \text{PRF})$

### RCS Aspect Modulation

RCS varies with the angle between the target's velocity vector and the radar line-of-sight. A broadside target presents a larger cross-section than a head-on one:

```
cos_aspect = |v̂ · û_LOS|
σ_eff = σ · (0.5 + 0.5 · √(1 - cos²_aspect))
```

This is a sinusoidal approximation. Swerling statistical models (planned) will replace this for more realistic target fluctuation.

### Doppler Shift

Radial velocity produces a frequency shift used to separate targets from stationary ground clutter:

$$f_d = \frac{2 \cdot v_{radial} \cdot f_c}{c}$$

Targets below the minimum detectable velocity threshold are filtered out — this is the core clutter rejection mechanism of pulse-Doppler.

### Proportional Navigation (PN) — *stub, in progress*

The intended guidance law. A missile commanded acceleration is proportional to the line-of-sight rotation rate:

$$\vec{a}_{cmd} = N \cdot V_c \cdot \vec{\omega}_{LOS} \times \hat{r}_{LOS}$$

where $N$ is the navigation constant (typically 3–5) and $V_c$ is the closing speed. Currently uses a straight-line pursuit placeholder.

---

## Target Profiles

All values can be edited in `TARGET_PROFILES` in `main.py`.

| Target | Speed (km/h) | RCS (m²) | IR Signature | Maneuverability | Altitude Range (km) |
|--------|-------------|----------|--------------|-----------------|---------------------|
| Drone | 120 | 0.01 | 0.2 | 0.8 | 0.1 – 3.0 |
| Aircraft | 800 | 5.0 | 0.9 | 0.4 | 5.0 – 12.0 |
| Cruise Missile | 900 | 0.1 | 0.7 | 0.6 | 0.05 – 0.5 |
| Ballistic Missile | 7000 | 0.5 | 1.0 | 0.05 | 30.0 – 150.0 |
| Helicopter | 280 | 3.0 | 0.6 | 0.9 | 0.05 – 4.0 |

To add a new target type, add an entry to `TARGET_PROFILES` — the rest of the simulation picks it up automatically.

---

## Radar Modes

| Radar Mode | Status |
|------------|--------|
| Pulse-Doppler | 🔧 |
| FMCW | 🔧 |
| Phased Array (AESA) | ⚪ |
| Bistatic | ⚪ |

**Status index:**
- ✅ Implemented — full physics model
- 🔧 In development — active work in progress
- ⚪ Stub — uses perfect detection placeholder

**Editable radar parameters** (via UI sliders or `radar_params` config object): transmit power (kW), center frequency (GHz), antenna gain (dB), noise figure (dB), receiver bandwidth (MHz), PRF (Hz).

---

## Guidance Modes

| Guidance Mode | Status |
|---------------|--------|
| Proportional Navigation (PN) | 🔧 |
| Semi-Active Radar Homing (SARH) | ⚪ |
| Infrared Seeking (IR) | ⚪ |
| Command / MCLOS | ⚪ |
| Active Radar Homing (ARH) | ⚪ |

**Status index:** same as above.

To add a new guidance mode: implement `guidance_mymode(missile, target, dt) -> dict` in `main.py`, add a branch in `run_tick()`, and add an option to the dropdown in `index.html` (search `homing_options`).

---

## Screenshots

*GIFs and screenshots go here*

---

## Future Plans

- **Embedded deployment** — migrate the simulation engine to a dedicated embedded computer running a custom RTOS (written from scratch), replacing the FastAPI/Python backend with a bare-metal C implementation for hard real-time guarantees
- Implement full Proportional Navigation guidance geometry
- Swerling I/II/III/IV RCS fluctuation models
- FMCW triangle-wave sweep with range-Doppler ambiguity resolution
- Coherent pulse integration (FFT across N pulses) for realistic detection range
- Evasive target maneuver models (max-g break turns, flare/chaff dispensing)
- Nap-of-Earth flight with terrain masking

---

## References

- Zarchan, *Tactical and Strategic Missile Guidance* — proportional navigation math
- Skolnik, *Introduction to Radar Systems* — radar range equation
- Mahafza, *Radar Systems Analysis and Design Using MATLAB* — pulse-Doppler, FMCW
- NATO STANAG 4193 — target RCS reference values

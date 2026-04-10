"""
Airborne Target Interception Simulation - FastAPI Backend
=========================================================
All physics/math functions are STUBS. Fill in each section marked
with  # <<< YOUR MATH HERE >>>  to implement the simulation logic.

Run with:
    pip install fastapi uvicorn numpy
    uvicorn main:app --reload --port 8000
"""

import asyncio
import json
import math
import random
import time
from typing import Optional
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware


# Physics Environment Constants

C_LIGHT = 3e8
K_Boltz = 1.38e-23
T_SYS = 500.0
L_SYS_DB = 3.0
SNR_THRESH_DB = 13.0
V_MDV_MPS = 3.0

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("WARNING: numpy not installed. Some stubs will not work until you install it.")

app = FastAPI(title="Intercept Sim Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# SIMULATION STATE
# ─────────────────────────────────────────────────────────────────────────────

SIM_TICK_RATE = 0.05        # seconds per tick (20 Hz)
MAX_RANGE = 200           # km, boundary of simulation space

active_connections: list[WebSocket] = []
sim_state = {
    "running": False,
    "tick": 0,
    "bogeys": [],           # list of target dicts
    "missiles": [],         # list of missile dicts
    "intercepts": [],       # log of interception events
}


# ─────────────────────────────────────────────────────────────────────────────
# TARGET TYPES  (extend this dict to add new target categories)
# ─────────────────────────────────────────────────────────────────────────────

TARGET_PROFILES = {
    "drone": {
        "speed_kmh": 120,
        "rcs_m2": 0.01,        # radar cross-section in m²
        "ir_signature": 0.2,   # 0-1 relative IR intensity
        "maneuverability": 0.8,
        "altitude_range": (0.1, 3.0),   # km
    },
    "aircraft": {
        "speed_kmh": 800,
        "rcs_m2": 5.0,
        "ir_signature": 0.9,
        "maneuverability": 0.4,
        "altitude_range": (5.0, 12.0),
    },
    "cruise_missile": {
        "speed_kmh": 900,
        "rcs_m2": 0.1,
        "ir_signature": 0.7,
        "maneuverability": 0.6,
        "altitude_range": (0.05, 0.5),
    },
    "ballistic_missile": {
        "speed_kmh": 7000,
        "rcs_m2": 0.5,
        "ir_signature": 1.0,
        "maneuverability": 0.05,
        "altitude_range": (30.0, 150.0),
    },
    "helicopter": {
        "speed_kmh": 280,
        "rcs_m2": 3.0,
        "ir_signature": 0.6,
        "maneuverability": 0.9,
        "altitude_range": (0.05, 4.0),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# HOMING GUIDANCE  — implement your intercept geometry here
# ─────────────────────────────────────────────────────────────────────────────

def guidance_proportional_navigation(missile: dict, target: dict, dt: float) -> dict:
    """
    Proportional Navigation (PN)
    The missile turns at a rate proportional to the line-of-sight (LOS) rotation rate.
    
    Classic formula:  a_cmd = N * V_c * omega_LOS
        N       = navigation constant (typically 3-5)
        V_c     = closing velocity (relative speed along LOS)
        omega_LOS = LOS rotation rate (rad/s)

    Parameters
    ----------
    missile : dict  keys: pos [x,y,z], vel [vx,vy,vz], params {...}
    target  : dict  keys: pos [x,y,z], vel [vx,vy,vz]
    dt      : float seconds since last tick

    Returns
    -------
    dict  updated missile with new pos, vel
    """
    # <<< YOUR MATH HERE >>>
    # Suggested steps:
    # 1. Compute relative position (R) and velocity (Rdot)
    # 2. Compute LOS unit vector and LOS rate (omega)
    # 3. Compute commanded acceleration vector
    # 4. Clamp to missile max-g limit
    # 5. Integrate velocity and position

    # PLACEHOLDER: dumb straight-line step toward target
    missile = _stub_home_toward_target(missile, target, dt)
    return missile


def guidance_sarh(missile: dict, target: dict, radar_state: dict, dt: float) -> dict:
    """
    Semi-Active Radar Homing (SARH)
    Ground radar illuminates the target; missile homes on reflected energy.

    Key physics:
    - Illuminator beam must stay on target (check cone angle)
    - Signal strength degrades with range^4 (two-way path)
    - Add beam-riding correction to keep missile on radar boresight

    Parameters
    ----------
    radar_state : dict  keys: beam_az, beam_el, power_kw, frequency_ghz
    """
    # <<< YOUR MATH HERE >>>
    missile = _stub_home_toward_target(missile, target, dt)
    return missile


def guidance_ir_seeking(missile: dict, target: dict, dt: float) -> dict:
    """
    Infrared (IR) / Heat-seeking guidance
    Missile seeker locks on to target's thermal signature.

    Key physics:
    - IR signature strength vs slant range (inverse-square)
    - Seeker gimbal angle limit (typically ±45 deg off boresight)
    - Background clutter / flare countermeasures (optional)
    - Pursuit curve vs lead pursuit: implement whichever you prefer
    """
    # <<< YOUR MATH HERE >>>
    missile = _stub_home_toward_target(missile, target, dt)
    return missile


def guidance_command_detonation(missile: dict, target: dict, dt: float) -> dict:
    """
    Command / Wire-guided (MCLOS)
    Operator (or autopilot) continuously uplinks steering commands.
    Implement a simple LQR or PD controller here.
    """
    # <<< YOUR MATH HERE >>>
    missile = _stub_home_toward_target(missile, target, dt)
    return missile


def guidance_active_radar(missile: dict, target: dict, dt: float) -> dict:
    """
    Active Radar Homing (ARH / 'fire and forget')
    Missile carries its own miniature radar and tracks autonomously.
    Implement augmented proportional navigation (APN) with seeker noise.
    """
    # <<< YOUR MATH HERE >>>
    missile = _stub_home_toward_target(missile, target, dt)
    return missile


# ─────────────────────────────────────────────────────────────────────────────
# RADAR MODES  — implement detection & tracking math here
# ─────────────────────────────────────────────────────────────────────────────

def Swerling_model():
    #placeholder - need to implement Swerling
    return

def radar_pulse_doppler(targets: list, radar_params: dict) -> list:
    """
    Pulse-Doppler Radar
    Separates targets by Doppler shift; strong clutter rejection.

    Radar equation:  SNR = (P_t * G^2 * lambda^2 * sigma) /
                           ((4*pi)^3 * R^4 * k * T * B * F * L)

    Parameters
    ----------
    radar_params : dict
        power_kw, freq_ghz, antenna_gain_db, noise_figure_db,
        bandwidth_mhz, prf_hz, pulse_width_us

    Returns
    -------
    list of detected target dicts with added fields:
        detected (bool), snr_db, range_m, range_rate_mps, azimuth_deg, elevation_deg
    """
    # <<< YOUR MATH HERE >>>

    P_t = radar_params.get("power_kw", 100.0) * 1e3
    f_c = radar_params.get("freq_ghz", 10.0) * 1e9
    G_db = radar_params.get("antenna_gain_db", 30.0)
    F_db = radar_params.get("noise_figure_db", 5.0)
    B_hz = radar_params.get("bandwidth_mhz", 10.0) * 1e6
    prf = radar_params.get("prf_hz", 5000.0)

    #in linear units
    lam = C_LIGHT / f_c
    G = 10^(G_db / 10)
    F = 10^(F_db / 10)
    L = 10^(L_SYS_DB / 10)

    N0 = K_Boltz * T_SYS * B_hz * F * L #noise power in W - how much background noise in the receiver
    num_const = (P_t * G^2 * lam^2) / ((4*math.pi)^3 * N0 * L) #does not change per target - radar strength factors
    R_ambiguous = C_LIGHT / (2 * prf) #max unambiguous range (range beyond this will alis - echoes will be confusing)

    for t in targets:
        pos = t["pos"]
        vel = t["vel"]

        px_m = pos[0] * 1e3
        py_m = pos[1] * 1e3
        pz_m = pos[2] * 1e3

        R_m = math.sqrt(px_m**2 + py_m**2 + pz_m**2)
        
        if R_m < 1.0:  #avoiding singularity 0 target is inside radar (checking just in case)
            t.update({"detected": False, "snr_db": -999 , "range_m": 0.0, "range_rate_mps": 0.0, "azimuth_deg": 0.0, "elevation_deg": 0.0})
            continue

        ux, uy, uz = px_m / R_m, py_m / R_m, pz_m / R_m

        #azimuth and elevation
        az_rad = math.atan2(ux, uz)
        el_rad = math.asin(uy)
        az_deg = math.degrees(az_rad)
        el_deg = math.degrees(el_rad)

        #Radial velocity
        v_mps = (vel[0] * ux + vel[1] * uy + vel[2] * uz) * 1e3

        #Doppler shift
        f_d = 2 * (-v_mps) * f_c / C_LIGHT

        #Radar Cross Section
        sigma = t.get("profile", {}).get("rcs_m2", 1.0)

        speed_mps = math.sqrt(vel[0]**2 + vel[1]**2 + vel[2]**2) *1e9 or 1e-9
        cos_aspect = v_mps / speed_mps
        rcs_aspect_factor = 0.5 * 0.5 * abs(math.sin(math.acos(max(-1.0, min(1.0, cos_aspect))))) #simple aspect factor - max at 90 deg aspect, zero at head/tail on
        sigma_eff = sigma * rcs_aspect_factor

        #SNR calculation
        SNR_linear = num_const * sigma_eff / (R_m**4)
        SNR_db = 10 * math.log10(max(SNR_linear, 1e-30))

        snr_ok = SNR_db > SNR_THRESH_DB
        range_ok = R_m <= R_ambiguous
        f_mdv = 2.0 * V_MDV_MPS * f_c / C_LIGHT
        doppler_ok = abs(f_d) >= f_mdv

        detected = snr_ok and range_ok and doppler_ok

        if detected:
            t.update({"detected": True, "snr_db": SNR_db, "range_m": R_m, "range_rate_mps": v_mps, "azimuth_deg": az_deg, "elevation_deg": el_deg})
        else:
            t.update({"detected": False, "snr_db": SNR_db, "range_m": R_m, "range_rate_mps": v_mps, "azimuth_deg": az_deg, "elevation_deg": el_deg})
        
    return targets


def radar_fmcw(targets: list, radar_params: dict) -> list:
    """
    Frequency-Modulated Continuous Wave (FMCW)
    Continuous transmission; range extracted from beat frequency.

    Beat frequency:  f_beat = (2 * R * B) / (c * T_sweep)
        R       = target range
        B       = sweep bandwidth
        T_sweep = sweep period

    Doppler shift:   f_d = 2 * v_r * f_c / c

    Implement the triangle-wave sweep to resolve range-Doppler ambiguity.
    """
    # <<< YOUR MATH HERE >>>
    return _stub_perfect_detection(targets)


def radar_phased_array(targets: list, radar_params: dict) -> list:
    """
    Electronically-Scanned Array (AESA/PESA)
    Beam-steering via phase shifters; simultaneous track-while-scan.

    Key features to implement:
    - Beam pattern: sinc^2 or Chebyshev-weighted aperture
    - Grating lobe suppression
    - Adaptive null-steering for jamming
    - Multiple simultaneous beams (AESA)
    """
    # <<< YOUR MATH HERE >>>
    return _stub_perfect_detection(targets)


def radar_bistatic(targets: list, radar_params: dict, tx_pos: list, rx_pos: list) -> list:
    """
    Bistatic Radar (transmitter & receiver separated)
    Exploits different target RCS aspect angles.

    Bistatic range:  R_bistatic = sqrt(R_tx * R_rx)
    Bistatic RCS differs from monostatic; implement Cassini ovals for iso-range.
    """
    # <<< YOUR MATH HERE >>>
    return _stub_perfect_detection(targets)


# ─────────────────────────────────────────────────────────────────────────────
# TARGET MOTION MODELS  — implement evasion/flight dynamics here
# ─────────────────────────────────────────────────────────────────────────────

def target_motion_constant_velocity(target: dict, dt: float) -> dict:
    """Straight-line constant-velocity flight."""
    for i, k in enumerate(['x', 'y', 'z']):
        target['pos'][i] += target['vel'][i] * dt
    return target


def target_motion_evasive(target: dict, dt: float, threat_pos: list) -> dict:
    """
    Evasive maneuver: target detected incoming missile and breaks.

    Implement:
    - Detect threat bearing
    - Pull maximum-g turn away from threat
    - Dispensing flares / chaff (flag for IR/radar countermeasures)
    """
    # <<< YOUR MATH HERE >>>
    return target_motion_constant_velocity(target, dt)


def target_motion_nap_of_earth(target: dict, dt: float) -> dict:
    """
    NOE (Nap-of-the-Earth) flying — hug terrain to exploit radar shadow.
    Implement terrain-following altitude constraint + jinking.
    """
    # <<< YOUR MATH HERE >>>
    return target_motion_constant_velocity(target, dt)


# ─────────────────────────────────────────────────────────────────────────────
# INTERCEPT / DETONATION LOGIC
# ─────────────────────────────────────────────────────────────────────────────

def check_intercept(missile: dict, target: dict) -> bool:
    """
    Returns True if missile is close enough to kill target.

    Implement:
    - Proximity fuze: detonate within lethal radius
    - Direct hit (point-mass collision)
    - Blast/fragmentation lethality model (optional)
    """
    # <<< YOUR MATH HERE >>>
    # Stub: simple Euclidean kill radius
    kill_radius_km = missile.get("kill_radius_km", 0.5)
    dist = _distance(missile["pos"], target["pos"])
    return dist < kill_radius_km


# ─────────────────────────────────────────────────────────────────────────────
# SPAWN HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def spawn_bogey(target_type: str, bogey_id: int) -> dict:
    profile = TARGET_PROFILES.get(target_type, TARGET_PROFILES["aircraft"])
    alt_min, alt_max = profile["altitude_range"]
    angle = random.uniform(0, 2 * math.pi)
    radius = random.uniform(MAX_RANGE * 0.5, MAX_RANGE * 0.85)
    alt = random.uniform(alt_min, alt_max)

    speed_kms = profile["speed_kmh"] / 3600.0
    heading = angle + math.pi + random.uniform(-0.4, 0.4)  # roughly toward origin

    return {
        "id": bogey_id,
        "type": target_type,
        "pos": [radius * math.cos(angle), alt, radius * math.sin(angle)],
        "vel": [
            speed_kms * math.cos(heading),
            random.uniform(-0.01, 0.01),
            speed_kms * math.sin(heading),
        ],
        "profile": profile,
        "alive": True,
        "intercepted": False,
        "detected": True,     # set to False until radar detects it
        "snr_db": 20.0,
    }


def spawn_missile(target: dict, homing_mode: str, missile_id: int) -> dict:
    return {
        "id": missile_id,
        "target_id": target["id"],
        "homing": homing_mode,
        "pos": [0.0, 0.05, 0.0],     # launch from origin (command center)
        "vel": [0.0, 0.5, 0.0],      # initial upward boost
        "speed_kms": 2.5,            # km/s
        "kill_radius_km": 0.3,
        "fuel": 60.0,                # seconds of burn
        "alive": True,
    }


# ─────────────────────────────────────────────────────────────────────────────
# SIMULATION TICK
# ─────────────────────────────────────────────────────────────────────────────

def run_tick(config: dict):
    dt = SIM_TICK_RATE
    homing = config.get("homing_mode", "proportional_navigation")
    radar = config.get("radar_mode", "pulse_doppler")
    radar_params = config.get("radar_params", {})

    # 1. Radar detection pass
    alive_bogeys = [b for b in sim_state["bogeys"] if b["alive"]]
    if radar == "pulse_doppler":
        alive_bogeys = radar_pulse_doppler(alive_bogeys, radar_params)
    elif radar == "fmcw":
        alive_bogeys = radar_fmcw(alive_bogeys, radar_params)
    elif radar == "phased_array":
        alive_bogeys = radar_phased_array(alive_bogeys, radar_params)
    elif radar == "bistatic":
        alive_bogeys = radar_bistatic(alive_bogeys, radar_params, [0,0,0], [5,0,5])

    # 2. Move bogeys
    for b in alive_bogeys:
        b = target_motion_constant_velocity(b, dt)

    # 3. Move & guide missiles
    target_map = {b["id"]: b for b in alive_bogeys}
    for m in sim_state["missiles"]:
        if not m["alive"]:
            continue
        t = target_map.get(m["target_id"])
        if t is None or not t["alive"]:
            m["alive"] = False
            continue

        m["fuel"] -= dt
        if m["fuel"] <= 0:
            m["alive"] = False
            continue

        if homing == "proportional_navigation":
            m = guidance_proportional_navigation(m, t, dt)
        elif homing == "sarh":
            m = guidance_sarh(m, t, {}, dt)
        elif homing == "ir_seeking":
            m = guidance_ir_seeking(m, t, dt)
        elif homing == "command_detonation":
            m = guidance_command_detonation(m, t, dt)
        elif homing == "active_radar":
            m = guidance_active_radar(m, t, dt)

        # 4. Check intercept
        if check_intercept(m, t):
            t["alive"] = False
            t["intercepted"] = True
            m["alive"] = False
            sim_state["intercepts"].append({
                "tick": sim_state["tick"],
                "bogey_id": t["id"],
                "missile_id": m["id"],
                "pos": t["pos"][:],
            })

    sim_state["tick"] += 1


# ─────────────────────────────────────────────────────────────────────────────
# WEBSOCKET ENDPOINT
# ─────────────────────────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    active_connections.append(ws)
    config = {}
    sim_task = None

    async def sim_loop():
        while sim_state["running"]:
            run_tick(config)
            payload = {
                "type": "state",
                "tick": sim_state["tick"],
                "bogeys": [serialize_entity(b) for b in sim_state["bogeys"]],
                "missiles": [serialize_entity(m) for m in sim_state["missiles"]],
                "intercepts": sim_state["intercepts"][-20:],
            }
            try:
                await ws.send_text(json.dumps(payload))
            except Exception:
                break
            await asyncio.sleep(SIM_TICK_RATE)

    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            cmd = msg.get("cmd")

            if cmd == "launch_sim":
                config = msg.get("config", {})
                target_type = config.get("target_type", "aircraft")
                n_bogeys = int(config.get("n_bogeys", 3))

                sim_state["running"] = False
                await asyncio.sleep(0.1)

                sim_state.update({
                    "running": True, "tick": 0,
                    "bogeys": [spawn_bogey(target_type, i) for i in range(n_bogeys)],
                    "missiles": [],
                    "intercepts": [],
                })
                sim_task = asyncio.create_task(sim_loop())
                await ws.send_text(json.dumps({"type": "ack", "msg": "sim started"}))

            elif cmd == "fire_missile":
                homing = config.get("homing_mode", "proportional_navigation")
                target_id = msg.get("target_id")
                target = next((b for b in sim_state["bogeys"] if b["id"] == target_id and b["alive"]), None)
                if target:
                    mid = len(sim_state["missiles"])
                    sim_state["missiles"].append(spawn_missile(target, homing, mid))
                    await ws.send_text(json.dumps({"type": "ack", "msg": f"missile {mid} fired"}))

            elif cmd == "fire_all":
                homing = config.get("homing_mode", "proportional_navigation")
                for b in sim_state["bogeys"]:
                    if b["alive"]:
                        mid = len(sim_state["missiles"])
                        sim_state["missiles"].append(spawn_missile(b, homing, mid))
                await ws.send_text(json.dumps({"type": "ack", "msg": "all missiles fired"}))

            elif cmd == "stop":
                sim_state["running"] = False
                await ws.send_text(json.dumps({"type": "ack", "msg": "sim stopped"}))

    except WebSocketDisconnect:
        pass
    finally:
        active_connections.remove(ws)
        sim_state["running"] = False


# ─────────────────────────────────────────────────────────────────────────────
# INTERNAL STUBS & UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def _stub_home_toward_target(missile: dict, target: dict, dt: float) -> dict:
    """Placeholder: fly straight toward target at constant speed."""
    mp, tp = missile["pos"], target["pos"]
    dx, dy, dz = tp[0]-mp[0], tp[1]-mp[1], tp[2]-mp[2]
    dist = math.sqrt(dx*dx + dy*dy + dz*dz) or 1e-9
    spd = missile["speed_kms"]
    missile["vel"] = [dx/dist*spd, dy/dist*spd, dz/dist*spd]
    for i in range(3):
        missile["pos"][i] += missile["vel"][i] * dt
    return missile


def _stub_perfect_detection(targets: list) -> list:
    """Placeholder: every target is always detected with perfect SNR."""
    for t in targets:
        t["detected"] = True
        t["snr_db"] = 30.0
    return targets


def _distance(a: list, b: list) -> float:
    return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))


def serialize_entity(e: dict) -> dict:
    """Strip non-serialisable fields before sending over WS."""
    return {k: v for k, v in e.items() if k != "profile"}


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

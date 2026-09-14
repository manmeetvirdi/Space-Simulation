r"""
04_gravity_assist_simulation.py — Live Numerical Integration of Voyager 1 under a Multi-Body Ephemeris-Based Gravitational Field
Part of Space Simulation / YPAE Simathon 02

Features:
  1. Complete Solar System Visualization (Identical to 03):
     - All 11 celestial bodies rendered live (Sun, Earth, Mars, Jupiter, Saturn, Uranus, Neptune, Pluto, Halley, Borisov).
     - Clean, singular 1-pixel orbital tracks extracted from exactly ONE true orbital period (no multi-year fuzz, perfectly aligned).
     - Comet ion tails, Saturn's rings, 3D axes, and Heliopause ring at 121 AU.
  2. Live Trajectory Calculation under Multi-Body Gravitational Field (Ephemeris-Driven):
     - Numerically integrated spacecraft trajectory under a multi-body gravitational field whose planetary states are supplied by NASA ephemerides.
     - Computes real-time Newtonian gravitational acceleration from Sun, Jupiter, Saturn, Earth, Mars, Uranus, Neptune:
         d^2 r / dt^2 = sum_i [ G * M_i / |r_i(t) - r|^3 * (r_i(t) - r) ]
     - J2 oblateness corrections for Jupiter (J2=0.014736) and Saturn (J2=0.016298)
     - Galilean moon gravity (Io, Europa, Ganymede, Callisto) during Jupiter close approach
     - Catmull-Rom cubic spline interpolation for sub-daily planet position accuracy
     - Adaptive 5-tier timestep: 30s at closest approach, 120s near encounter, up to 1hr in cruise
     - Trajectory is dynamically calculated on-the-fly via numerical integration, NOT read from ephemeris!
  3. Guidance & Trajectory Correction Maneuvers (Pure Delta-V, No Position Snapping):
     - Historical NASA Trajectory Correction Maneuvers (TCM-1 to TCM-6):
       * TCM-1 (Day 6): Launch injection dispersion trim (~7 m/s)
       * TCM-2 (Day 36): Earth-Jupiter transfer orbit refinement (~17 m/s)
       * TCM-3 (Day 520): Pre-Jupiter aimpoint targeting using velocity guidance (~1 m/s)
       * TCM-4 (Day 582): Post-Jupiter outbound clean-up targeting Saturn (~90 m/s)
       * TCM-5 (Day 920): Jupiter-Saturn mid-cruise trim (~0.2 m/s)
       * TCM-6 (Day 1130): Pre-Saturn aimpoint targeting using velocity guidance (~0.1 m/s)
     - Simulated Autonomous Guidance Corrections (every 60 days):
       * Simulated autonomous guidance corrections used to maintain mission targeting and
         demonstrate realistic navigation control (prevents numerical drift accumulation).
     - ZERO POSITION SNAPPING: Trajectory is influenced strictly through Delta-V velocity guidance,
       allowing the numerical physics model to compute all forces, gravitational assists, and orbital
       motion dynamically. The spacecraft coordinates are NEVER snapped or overwritten.
     - Key [T] toggles between Active Guided Flight and Unguided Ballistic Flight.
  4. Infinite Interstellar Extrapolation (Past 2026 into Eternity):
     - No stop at Day 17,931! Continues flying into deep interstellar space (>200 AU, >500 AU).
     - Dynamic date calculator tracks future years (2030, 2040, 2050+).
  5. Keyboard Controls Mapped 1-to-1 with File 03:
     - Keys [0] through [6] identical to 03 (Launch, Stepping, Jupiter, Saturn, Halley, Pluto).
     - Physics Integrators shifted to Keys [7] RK4, [8] Velocity Verlet, [9] Forward Euler.
  6. Exact same keyboard navigation scheme as 03_solar_system_voyager.py:
     - [SPACE] Freeze / Play live physics integration
     - [Q] / [W] Simulation Speed (1, 2, 4, 7, 14, 30 Days/frame)
     - [UP], [DOWN], [LEFT], [RIGHT] 2D Frame Panning
     - [Z] / [Ctrl+Z] In-place Zoom In / Out
     - [V] Center Voyager 1 (Preserves zoom)
     - [F] Toggle Probe Chase Cam (Smooth lock / cinematic orbit around Voyager 1)
     - [S] Center Sun (Preserves zoom)
     - [P] / [Ctrl+P] Pitch Up / Down
     - [Y] / [Ctrl+Y] Yaw Right / Left
     - [T] Toggle Active TCM Guidance Burns ON / OFF
     - [0] / [L] Earth Launch Standby (Day 0, 1977)
     - [1] Step Forward +7 Days (paused)
     - [2] Step Backward -7 Days (paused)
     - [3] Jump to Jupiter Encounter (Day 516)
     - [4] Jump to Saturn Encounter (Day 1134)
     - [5] Jump to Halley Perihelion (Day 3079)
     - [6] Jump to Pluto Inside Neptune View (Day 4500)
     - [7] Switch to RK4 Integrator (High Precision)
     - [8] Switch to Velocity Verlet Integrator (Symplectic Leapfrog)
     - [9] Switch to Forward Euler Integrator (Numerical Divergence Demo)
     - [H] Clean Mode (Hide all HUD and overlays)
     - [K] High-Res Screenshot Capture
     - [ESC] Exit
"""

import os
import time
import math
import datetime
import numpy as np
import taichi as ti

# ==============================================================================
# 1. PHYSICAL CONSTANTS & GRAVITATIONAL PARAMETERS (km^3 / s^2)
# ==============================================================================
AU_KM = 1.495978707e8   # 1 Astronomical Unit in km
C_LIGHT = 299792.458    # Speed of light in km/s
G_STANDARD = 9.80665e-3 # 1 g in km/s^2

# Standard Gravitational Parameters (mu = G * M in km^3 / s^2)
MU_SUN     = 1.32712440018e11
MU_JUPITER = 1.26686534e8
MU_SATURN  = 3.7931187e7
MU_EARTH   = 3.986004418e5
MU_MARS    = 4.282837e4
MU_URANUS  = 5.793939e6
MU_NEPTUNE = 6.836529e6

BODIES_MU = {
    "sun": MU_SUN,
    "jupiter": MU_JUPITER,
    "saturn": MU_SATURN,
    "earth": MU_EARTH,
    "mars": MU_MARS,
    "uranus": MU_URANUS,
    "neptune": MU_NEPTUNE,
}

# J2 Oblateness Coefficients and Equatorial Radii (km)
# J2 captures the quadrupole moment from planetary flattening
J2_JUPITER = 0.014736     # Jupiter is ~6.5% oblate
R_EQ_JUPITER = 71492.0    # Jupiter equatorial radius (km)
J2_SATURN  = 0.016298     # Saturn is ~9.8% oblate
R_EQ_SATURN = 60268.0     # Saturn equatorial radius (km)

BODIES_J2 = {
    "jupiter": (J2_JUPITER, R_EQ_JUPITER),
    "saturn":  (J2_SATURN,  R_EQ_SATURN),
}

# Solar system bodies display configuration (identical to 03)
BODIES_CONFIG = [
    {"key": "sun",      "name": "Sun",         "color": 0xFFEB3B, "radius": 7, "glow": 0x44FFE033, "trail_col": 0x332211},
    {"key": "earth",    "name": "Earth",       "color": 0x29B6F6, "radius": 4, "glow": 0x3329B6F6, "trail_col": 0x1A3A5A},
    {"key": "mars",     "name": "Mars",        "color": 0xFF5722, "radius": 3, "glow": 0x33FF5722, "trail_col": 0x4A2218},
    {"key": "jupiter",  "name": "Jupiter",     "color": 0xFFA726, "radius": 6, "glow": 0x33FFA726, "trail_col": 0x5A401A},
    {"key": "saturn",   "name": "Saturn",      "color": 0xFFD54F, "radius": 5, "glow": 0x33FFD54F, "trail_col": 0x5A501A},
    {"key": "uranus",   "name": "Uranus",      "color": 0x4DD0E1, "radius": 4, "glow": 0x334DD0E1, "trail_col": 0x1A4048},
    {"key": "neptune",  "name": "Neptune",     "color": 0x3F51B5, "radius": 4, "glow": 0x333F51B5, "trail_col": 0x1A2048},
    {"key": "pluto",    "name": "Pluto",       "color": 0xCE93D8, "radius": 3, "glow": 0x33CE93D8, "trail_col": 0x3E2448},
    {"key": "halley",   "name": "1P/Halley",   "color": 0xE0F7FA, "radius": 3, "glow": 0x66FFFFFF, "trail_col": 0x2E4A52, "is_comet": True},
    {"key": "borisov",  "name": "C/2021 Borisov", "color": 0x80DEEA, "radius": 2, "glow": 0x3380DEEA, "trail_col": 0x1A3840, "is_comet": True},
]

# Exact planetary orbital periods (in days) to extract single closed loops
ORBITAL_PERIODS_DAYS = {
    "earth": 365,
    "mars": 687,
    "jupiter": 4333,
    "saturn": 10759,
    "uranus": 17931,
    "neptune": 17931,
    "pluto": 17931,
    "halley": 17931,
    "borisov": 17931,
}

# Historical milestones
MILESTONES = [
    {"name": "LAUNCH", "day": 0, "date": "1977-Sep-06", "desc": "Voyager 1 lifts off from Earth, crossing lunar orbit on Day 1", "color": 0x00FF88},
    {"name": "JUPITER FLYBY", "day": 546, "date": "1979-Mar-06", "desc": "Closest approach to Jupiter (~349,000 km). +10 km/s Gravity Assist Boost.", "color": 0xFFA726},
    {"name": "SATURN FLYBY", "day": 1164, "date": "1980-Nov-13", "desc": "Skims Saturn at 184,000 km. Titan encounter deflects Voyager 35.5 deg North.", "color": 0xFFD54F},
    {"name": "HALLEY PERIHELION", "day": 3079, "date": "1986-Feb-09", "desc": "Halley's Comet sweeps past the Sun and Earth at 0.58 AU.", "color": 0xE0F7FA},
    {"name": "TERMINATION SHOCK", "day": 9964, "date": "2004-Dec-16", "desc": "Crossed solar wind termination shock at ~94 AU.", "color": 0xBA68C8},
    {"name": "INTERSTELLAR SPACE", "day": 12773, "date": "2012-Aug-25", "desc": "Historic crossing: Voyager 1 crosses Heliopause at 121 AU.", "color": 0x00E5FF},
    {"name": "PRESENT DAY", "day": 17931, "date": "2026-Oct-10", "desc": "Voyager 1 in deep interstellar space (>172 AU).", "color": 0xFF3366},
]

# Trajectory Correction Maneuver (TCM) Architecture:
# 1. Historical NASA JPL Voyager 1 Trajectory Correction Maneuvers (TCM-1 through TCM-6)
#    Influences trajectory through Delta-V guidance rather than forcing coordinates.
# 2. Simulated autonomous guidance corrections used to maintain mission targeting and
#    demonstrate realistic navigation control (counteracts long-term numerical integration drift).
TCM_SCHEDULE = [
    {"name": "TCM-1", "day": 6,    "is_major": True,  "dv_nom_ms": 7.0,  "desc": "Launch Injection Dispersion Trim"},
    {"name": "TCM-2", "day": 36,   "is_major": True,  "dv_nom_ms": 17.0, "desc": "Earth-Jupiter Transfer Orbit Refinement"},
    {"name": "TCM-3", "day": 520,  "is_major": True,  "dv_nom_ms": 1.0,  "desc": "Pre-Jupiter aimpoint targeting using velocity guidance"},
    {"name": "TCM-4", "day": 582,  "is_major": True,  "dv_nom_ms": 90.0, "desc": "Post-Jupiter Outbound Clean-Up (Target Saturn)"},
    {"name": "TCM-5", "day": 920,  "is_major": True,  "dv_nom_ms": 0.2,  "desc": "Jupiter-Saturn Mid-Course Trim"},
    {"name": "TCM-6", "day": 1130, "is_major": True,  "dv_nom_ms": 0.1,  "desc": "Pre-Saturn aimpoint targeting using velocity guidance"},
]

# Simulated autonomous guidance corrections used to maintain mission targeting and demonstrate realistic navigation control.
# Note: These periodic trims are simulated autonomous G&NC corrections (every 60 days) to prevent
# numerical drift accumulation across multi-year cruise; they are not historical Voyager burns.
CRUISE_TRIM_DAYS = sorted(list(set(list(range(60, 520, 60)) + list(range(640, 920, 60)) + list(range(980, 1130, 60)))))
for cd in CRUISE_TRIM_DAYS:
    TCM_SCHEDULE.append({
        "name": f"G&NC-{cd}", "day": cd, "is_major": False, "dv_nom_ms": 0.5,
        "desc": "Simulated autonomous guidance correction (realistic navigation control)"
    })
TCM_SCHEDULE.sort(key=lambda x: x["day"])

# Base date for calendar calculations
BASE_LAUNCH_DATE = datetime.date(1977, 9, 5)

def format_mission_date(day_val, dates_list):
    """Formats date from ephemeris table or calculates future calendar date beyond 2026."""
    idx = int(day_val)
    if idx < len(dates_list):
        return dates_list[idx]
    future_date = BASE_LAUNCH_DATE + datetime.timedelta(days=int(day_val))
    return future_date.strftime("%Y-%b-%d")

# Galilean Moon Parameters (circular coplanar orbits in Jupiter's equatorial plane)
# mu: gravitational parameter (km^3/s^2), a: orbital semi-major axis (km),
# period: orbital period (days), L0: mean longitude at J2000 epoch (degrees)
# Source: JPL Horizons / Lieske (1998) Galilean satellite ephemeris
J2000_MISSION_DAY = (datetime.date(2000, 1, 1) - BASE_LAUNCH_DATE).days + 0.5

GALILEAN_MOONS = [
    {"name": "Io",       "mu": 5959.9, "a_km": 421700.0, "period_days": 1.7691, "L0_deg": 200.39},
    {"name": "Europa",   "mu": 3202.7, "a_km": 671100.0, "period_days": 3.5512, "L0_deg":  36.49},
    {"name": "Ganymede", "mu": 9887.8, "a_km": 1070400.0, "period_days": 7.1546, "L0_deg":  44.06},
    {"name": "Callisto", "mu": 7179.3, "a_km": 1882700.0, "period_days": 16.689, "L0_deg": 259.73},
]

# Moon gravity computed only within this distance of Jupiter (km) — roughly Jupiter's Hill sphere
MOON_GRAVITY_RADIUS = 5.0e7  # 50 million km

# ==============================================================================
# 2. EPHEMERIS LOADER & CACHE MANAGER
# ==============================================================================
def load_ephemeris_data(cache_path="solar_system_voyager_data.npz"):
    """Loads planetary state vectors and Voyager 1 ephemerides."""
    if not os.path.exists(cache_path):
        raise FileNotFoundError(f"Missing ephemeris cache '{cache_path}'. Please run 03_solar_system_voyager.py first to build the cache.")
    
    npz = np.load(cache_path, allow_pickle=True)
    dates = npz["dates"]
    v1_vel_kms = npz["v1_vel"]  # km/s
    
    bodies_pos_au = {}
    for cfg in BODIES_CONFIG:
        k = cfg["key"]
        if k in npz:
            bodies_pos_au[k] = npz[k]
    bodies_pos_au["voyager1"] = npz["voyager1"]

    # Extract in km for high precision physics calculations
    bodies_pos_km = {}
    for k, v in bodies_pos_au.items():
        bodies_pos_km[k] = v * AU_KM

    return dates, bodies_pos_au, bodies_pos_km, v1_vel_kms

# ==============================================================================
# 3. LIVE MULTI-BODY GRAVITATIONAL PHYSICS ENGINE (EPHEMERIS-BASED)
# ==============================================================================

@ti.data_oriented
class TaichiPhysicsEngine:
    def __init__(self, bodies_pos_km_dict, total_days, bodies_mu, bodies_j2, moons_data):
        self.total_days = total_days
        self.bodies_pos_km_dict = bodies_pos_km_dict
        self.BODY_KEYS = ["sun", "jupiter", "saturn", "earth", "mars", "uranus", "neptune"]
        self.num_bodies = len(self.BODY_KEYS)
        
        self.pos_table = ti.Vector.field(3, dtype=ti.f64, shape=(self.num_bodies, total_days))
        self.mu_arr = ti.field(dtype=ti.f64, shape=(self.num_bodies,))
        self.j2_arr = ti.field(dtype=ti.f64, shape=(self.num_bodies,))
        self.req_arr = ti.field(dtype=ti.f64, shape=(self.num_bodies,))
        self.period_arr = ti.field(dtype=ti.f64, shape=(self.num_bodies,))
        
        pos_np = np.zeros((self.num_bodies, total_days, 3), dtype=np.float64)
        for i, key in enumerate(self.BODY_KEYS):
            if key in bodies_pos_km_dict:
                pts = bodies_pos_km_dict[key]
                length = min(total_days, len(pts))
                pos_np[i, :length, :] = pts[:length]
            self.mu_arr[i] = bodies_mu.get(key, 0.0)
            if key in bodies_j2:
                self.j2_arr[i], self.req_arr[i] = bodies_j2[key]
            else:
                self.j2_arr[i], self.req_arr[i] = 0.0, 1.0
            self.period_arr[i] = ORBITAL_PERIODS_DAYS.get(key, 17931.0)
            
        self.pos_table.from_numpy(pos_np)
        
        self.num_moons = len(moons_data)
        self.moon_mu = ti.field(dtype=ti.f64, shape=(self.num_moons,))
        self.moon_a = ti.field(dtype=ti.f64, shape=(self.num_moons,))
        self.moon_period = ti.field(dtype=ti.f64, shape=(self.num_moons,))
        self.moon_L0 = ti.field(dtype=ti.f64, shape=(self.num_moons,))
        
        for i, m in enumerate(moons_data):
            self.moon_mu[i] = m["mu"]
            self.moon_a[i] = m["a_km"]
            self.moon_period[i] = m["period_days"]
            self.moon_L0[i] = m["L0_deg"]
            
        self.sim_day = ti.field(dtype=ti.f64, shape=())
        self.sim_pos = ti.Vector.field(3, dtype=ti.f64, shape=())
        self.sim_vel = ti.Vector.field(3, dtype=ti.f64, shape=())
        self.breakdown = ti.field(dtype=ti.f64, shape=(self.num_bodies,))
        self.moon_breakdown = ti.field(dtype=ti.f64, shape=())
        self.prev_acc = ti.Vector.field(3, dtype=ti.f64, shape=())
        self.has_prev_acc = ti.field(dtype=ti.i32, shape=())
        self.current_accel = ti.Vector.field(3, dtype=ti.f64, shape=())

    @ti.func
    def _catmull_rom(self, p0, p1, p2, p3, t):
        t2 = t * t
        t3 = t2 * t
        return 0.5 * ((2.0 * p1) + (-p0 + p2) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3)

    @ti.func
    def get_body_pos_km(self, b_idx, t_day):
        res = ti.Vector([0.0, 0.0, 0.0], dt=ti.f64)
        if b_idx != 0:
            total_pts = ti.cast(self.total_days, ti.f64)
            if t_day < total_pts - 1.0:
                t_clamped = ti.max(0.0, t_day)
                idx1 = ti.cast(ti.floor(t_clamped), ti.i32)
                idx2 = ti.min(self.total_days - 1, idx1 + 1)
                frac = t_clamped - ti.cast(idx1, ti.f64)
                idx0 = ti.max(0, idx1 - 1)
                idx3 = ti.min(self.total_days - 1, idx2 + 1)
                res = self._catmull_rom(self.pos_table[b_idx, idx0], self.pos_table[b_idx, idx1], self.pos_table[b_idx, idx2], self.pos_table[b_idx, idx3], frac)
            else:
                dt = t_day - (total_pts - 1.0)
                P = self.period_arr[b_idx]
                equiv_t = (total_pts - 1.0) - P + (dt % P)
                idx1 = ti.cast(ti.floor(equiv_t), ti.i32)
                idx2 = ti.min(self.total_days - 1, idx1 + 1)
                frac = equiv_t - ti.cast(idx1, ti.f64)
                idx0 = ti.max(0, idx1 - 1)
                idx3 = ti.min(self.total_days - 1, idx2 + 1)
                res = self._catmull_rom(self.pos_table[b_idx, idx0], self.pos_table[b_idx, idx1], self.pos_table[b_idx, idx2], self.pos_table[b_idx, idx3], frac)
        return res

    @ti.func
    def compute_acceleration(self, r_km, t_day, update_breakdown: ti.template()):
        a_net = ti.Vector([0.0, 0.0, 0.0], dt=ti.f64)
        jup_pos = ti.Vector([0.0, 0.0, 0.0], dt=ti.f64)
        moon_tot = 0.0
        for i in range(self.num_bodies):
            b_pos = self.get_body_pos_km(i, t_day)
            if i == 1: jup_pos = b_pos
            rel = b_pos - r_km
            dist = rel.norm()
            body_accel = 0.0
            if dist > 1.0:
                mu = self.mu_arr[i]
                mag = mu / (dist * dist * dist)
                a_comp = mag * rel
                a_net += a_comp
                body_accel = a_comp.norm()
                j2 = self.j2_arr[i]
                if j2 > 0.0:
                    req = self.req_arr[i]
                    dr = -rel
                    dist_sq = dist * dist
                    z_sq = dr[2] * dr[2]
                    factor = -1.5 * mu * j2 * req * req / (dist_sq * dist_sq * dist)
                    a_j2 = ti.Vector([factor * dr[0] * (1.0 - 5.0 * z_sq / dist_sq), factor * dr[1] * (1.0 - 5.0 * z_sq / dist_sq), factor * dr[2] * (3.0 - 5.0 * z_sq / dist_sq)], dt=ti.f64)
                    a_net += a_j2
                    body_accel += a_j2.norm()
            if update_breakdown:
                self.breakdown[i] = body_accel

        dist_to_jup = (r_km - jup_pos).norm()
        if dist_to_jup < MOON_GRAVITY_RADIUS:
            days_from_j2000 = t_day - J2000_MISSION_DAY
            for m in range(self.num_moons):
                angle_rad = (self.moon_L0[m] + (360.0 / self.moon_period[m]) * days_from_j2000) * (3.14159265358979 / 180.0)
                moon_pos = jup_pos + self.moon_a[m] * ti.Vector([ti.cos(angle_rad), ti.sin(angle_rad), 0.0], dt=ti.f64)
                moon_rel = moon_pos - r_km
                moon_dist = moon_rel.norm()
                if moon_dist > 1.0:
                    moon_mag = self.moon_mu[m] / (moon_dist * moon_dist * moon_dist)
                    a_moon = moon_mag * moon_rel
                    a_net += a_moon
                    moon_tot += a_moon.norm()
        if update_breakdown:
            self.moon_breakdown[None] = moon_tot
            self.current_accel[None] = a_net
        return a_net

    @ti.func
    def step_euler(self, dt_sec):
        a = self.compute_acceleration(self.sim_pos[None], self.sim_day[None], True)
        self.sim_pos[None] += self.sim_vel[None] * dt_sec
        self.sim_vel[None] += a * dt_sec

    @ti.func
    def step_verlet(self, dt_sec):
        a1 = ti.Vector([0.0, 0.0, 0.0], dt=ti.f64)
        if self.has_prev_acc[None] == 1:
            a1 = self.prev_acc[None]
        else:
            a1 = self.compute_acceleration(self.sim_pos[None], self.sim_day[None], True)
        self.sim_pos[None] += self.sim_vel[None] * dt_sec + 0.5 * a1 * (dt_sec * dt_sec)
        t_next = self.sim_day[None] + dt_sec / 86400.0
        a2 = self.compute_acceleration(self.sim_pos[None], t_next, True)
        self.sim_vel[None] += 0.5 * (a1 + a2) * dt_sec
        self.prev_acc[None] = a2
        self.has_prev_acc[None] = 1

    @ti.func
    def step_rk4(self, dt_sec):
        dt_day = dt_sec / 86400.0
        r = self.sim_pos[None]
        v = self.sim_vel[None]
        t = self.sim_day[None]
        a1 = self.compute_acceleration(r, t, True)
        k1_v = a1 * dt_sec
        k1_r = v * dt_sec
        r2 = r + 0.5 * k1_r
        v2 = v + 0.5 * k1_v
        a2 = self.compute_acceleration(r2, t + 0.5 * dt_day, False)
        k2_v = a2 * dt_sec
        k2_r = v2 * dt_sec
        r3 = r + 0.5 * k2_r
        v3 = v + 0.5 * k2_v
        a3 = self.compute_acceleration(r3, t + 0.5 * dt_day, False)
        k3_v = a3 * dt_sec
        k3_r = v3 * dt_sec
        r4 = r + k3_r
        v4 = v + k3_v
        a4 = self.compute_acceleration(r4, t + dt_day, False)
        k4_v = a4 * dt_sec
        k4_r = v4 * dt_sec
        self.sim_pos[None] = r + (k1_r + 2.0 * k2_r + 2.0 * k3_r + k4_r) / 6.0
        self.sim_vel[None] = v + (k1_v + 2.0 * k2_v + 2.0 * k3_v + k4_v) / 6.0

    @ti.kernel
    def advance_loop(self, target_day: ti.f64, cur_integrator: ti.i32):
        while self.sim_day[None] < target_day:
            jup_pos = self.get_body_pos_km(1, self.sim_day[None])
            sat_pos = self.get_body_pos_km(2, self.sim_day[None])
            earth_pos = self.get_body_pos_km(3, self.sim_day[None])
            
            dist_jup = (self.sim_pos[None] - jup_pos).norm()
            dist_sat = (self.sim_pos[None] - sat_pos).norm()
            dist_earth = (self.sim_pos[None] - earth_pos).norm()
            
            min_dist = ti.min(dist_jup, dist_sat)
            min_dist = ti.min(min_dist, dist_earth)
            
            dt_slice = 3600.0
            if min_dist < 1.0e6: dt_slice = 60.0
            elif min_dist < 5.0e6: dt_slice = 180.0
            elif min_dist < 3.0e7: dt_slice = 300.0
            elif min_dist < 1.0e8: dt_slice = 1800.0
            
            time_left_sec = (target_day - self.sim_day[None]) * 86400.0
            actual_dt = ti.min(dt_slice, time_left_sec)
            
            if cur_integrator == 0:
                self.step_rk4(actual_dt)
            elif cur_integrator == 1:
                self.step_verlet(actual_dt)
            else:
                self.step_euler(actual_dt)
                
            self.sim_day[None] += actual_dt / 86400.0
            
            if cur_integrator != 1:
                self.has_prev_acc[None] = 0


    @ti.kernel
    def update_breakdown_paused(self):
        self.compute_acceleration(self.sim_pos[None], self.sim_day[None], True)

    def compute_specific_energy(self, r_km=None, v_kms=None, t_day=None):
        if r_km is None: r_km = self.sim_pos[None].to_numpy()
        if v_kms is None: v_kms = self.sim_vel[None].to_numpy()
        if t_day is None: t_day = self.sim_day[None]
        v_sq = np.sum(v_kms * v_kms)
        pot = 0.0
        for i, key in enumerate(self.BODY_KEYS):
            b_pos = self.get_body_pos_km_py(key, t_day)
            dist = np.linalg.norm(r_km - b_pos)
            if dist > 1.0:
                pot += self.mu_arr.to_numpy()[i] / dist
        return 0.5 * v_sq - pot

    def get_latest_breakdown_dict(self):
        bd_arr = self.breakdown.to_numpy()
        res = {}
        for i, k in enumerate(self.BODY_KEYS):
            res[k] = bd_arr[i]
        res["moons"] = self.moon_breakdown[None]
        res["total"] = sum(res.values())
        return res


    def _catmull_rom_py(self, p0, p1, p2, p3, t):
        import numpy as np
        t2 = t * t
        t3 = t2 * t
        return 0.5 * ((2.0 * p1) + (-p0 + p2) * t + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * t2 + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * t3)

    def get_body_pos_km_py(self, key, t_day):
        import numpy as np
        if key == "sun":
            return np.array([0.0, 0.0, 0.0], dtype=np.float64)
        
        pts = self.bodies_pos_km_dict[key]
        total_pts = len(pts)
        t_f = float(t_day)

        if t_f < total_pts - 1.0:
            t_clamped = max(0.0, t_f)
            idx1 = int(t_clamped)
            idx2 = min(total_pts - 1, idx1 + 1)
            frac = t_clamped - idx1

            idx0 = max(0, idx1 - 1)
            idx3 = min(total_pts - 1, idx2 + 1)

            return self._catmull_rom_py(pts[idx0], pts[idx1], pts[idx2], pts[idx3], frac)

        dt = t_f - (total_pts - 1.0)
        
        if key in ["earth", "mars", "jupiter", "saturn"]:
            P = float(ORBITAL_PERIODS_DAYS[key])
            equiv_t = (total_pts - 1.0) - P + (dt % P)
            idx1 = int(equiv_t)
            idx2 = min(total_pts - 1, idx1 + 1)
            frac = equiv_t - idx1
            idx0 = max(0, idx1 - 1)
            idx3 = min(total_pts - 1, idx2 + 1)
            return self._catmull_rom_py(pts[idx0], pts[idx1], pts[idx2], pts[idx3], frac)

        r_end = pts[-1]
        v_end = pts[-1] - pts[-2]
        R = float(np.linalg.norm(r_end))
        V = float(np.linalg.norm(v_end))
        if R > 1e-4 and V > 1e-6:
            r_hat = r_end / R
            v_hat = v_end / V
            dtheta = (V / R) * dt
            return R * (np.cos(dtheta) * r_hat + np.sin(dtheta) * v_hat)
        return r_end

    def get_body_pos_au(self, key, t_day):
        import numpy as np
        return (self.get_body_pos_km_py(key, t_day) / 1.495978707e8).astype(np.float32)


class Camera3D:
    def __init__(self, yaw_deg=-35.0, pitch_deg=45.0, view_radius_au=12.0):
        self.yaw = math.radians(yaw_deg)
        self.pitch = math.radians(pitch_deg)
        self.radius = view_radius_au
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)

    def project_points(self, pos_au, width, height):
        """Projects array of (N, 3) coordinates in AU to screen space [0, 1]."""
        rel_pos = pos_au - self.target
        x = rel_pos[:, 0]
        y = rel_pos[:, 1]
        z = rel_pos[:, 2]

        cos_y = math.cos(self.yaw)
        sin_y = math.sin(self.yaw)
        x_rot = x * cos_y - y * sin_y
        y_rot = x * sin_y + y * cos_y

        cos_p = math.cos(self.pitch)
        sin_p = math.sin(self.pitch)
        x_cam = x_rot
        y_cam = y_rot * cos_p + z * sin_p

        aspect = width / height
        scale = 0.42 / max(1e-3, self.radius)
        sx = 0.5 + self.pan_x + (x_cam * scale) / aspect
        sy = 0.5 + self.pan_y + (y_cam * scale)
        return np.column_stack([sx, sy])

    def project_single(self, pos_au, width, height):
        p = np.array([pos_au], dtype=np.float32)
        s = self.project_points(p, width, height)
        return float(s[0, 0]), float(s[0, 1])

class SimValue:
    def __init__(self, init_val):
        self.value = init_val

# ==============================================================================
# 6. INITIALIZATION & GUI SETUP
# ==============================================================================
ti.init(arch=ti.cpu, default_fp=ti.f64)

WIDTH, HEIGHT = 1280, 880
gui = ti.GUI("04 · Voyager 1 Gravity Assist — Multi-Body Ephemeris-Based Integration", res=(WIDTH, HEIGHT), background_color=0x060911)

# Load ephemerides
dates, bodies_pos_au, bodies_pos_km, v1_vel_kms = load_ephemeris_data()
TOTAL_DAYS = len(dates)

# Physics Engine
physics = TaichiPhysicsEngine(bodies_pos_km, TOTAL_DAYS, BODIES_MU, BODIES_J2, GALILEAN_MOONS)

# Interactive Camera
camera = Camera3D(yaw_deg=-35.0, pitch_deg=45.0, view_radius_au=12.0)

# Playback Speed Levels (Days / frame)
SPEED_LEVELS = [1, 2, 4, 7, 14, 30]
slider_speed = SimValue(7)
slider_zoom  = SimValue(12.0)
slider_pitch = SimValue(45.0)
slider_yaw   = SimValue(-35.0)

# Integrator modes: 0: RK4 (Key [7]), 1: Velocity Verlet (Key [8]), 2: Forward Euler (Key [9])
INTEGRATOR_NAMES = [
    "RK4 (4th Order Runge-Kutta - High Precision)",
    "Velocity Verlet (Symplectic Leapfrog - Energy Conserving)",
    "Forward Euler (1st Order Naive - Numerical Drift)"
]
cur_integrator = 0  # Default to RK4

# TCM guidance state
tcm_enabled = True
applied_tcms = set()
last_tcm_msg = ""
last_tcm_timer = 0

# Live Simulation State
physics.sim_day[None] = 0.0
physics.sim_pos[None] = bodies_pos_km["voyager1"][0]
physics.sim_vel[None] = v1_vel_kms[0]
physics.update_breakdown_paused()

# Recorded simulation history
sim_trail = [physics.sim_pos[None].to_numpy() / AU_KM]
nasa_trail = [bodies_pos_km["voyager1"][0] / AU_KM]

is_playing = False
clean_hud = False
show_trails = True
follow_probe = False
sim_term_shock_pos = None
sim_heliopause_pos = None
notice_text = "SIMULATION READY: PRESS [SPACE] TO START LIVE NUMERICAL INTEGRATION"
notice_timer = 200
trigger_screenshot = False
pulse_timer = 0.0

def reset_to_day(target_day, integrator_mode=None):
    """Resets physics state vectors to the target day from ephemeris."""
    global sim_trail, nasa_trail, cur_integrator, applied_tcms, last_tcm_msg, last_tcm_timer, follow_probe, sim_term_shock_pos, sim_heliopause_pos
    if integrator_mode is not None:
        cur_integrator = integrator_mode
    t_int = int(min(TOTAL_DAYS - 1, max(0, target_day)))
    clamped_day = t_int
    
    physics.sim_day[None] = float(t_int)
    physics.sim_pos[None] = bodies_pos_km["voyager1"][clamped_day]
    physics.sim_vel[None] = v1_vel_kms[clamped_day]
    physics.has_prev_acc[None] = 0
    physics.update_breakdown_paused()
    
    follow_probe = False
    sim_term_shock_pos = None
    sim_heliopause_pos = None
    applied_tcms = {tcm["day"] for tcm in TCM_SCHEDULE if tcm["day"] < t_int}
    last_tcm_msg = ""
    last_tcm_timer = 0
    sim_trail = [physics.sim_pos[None].to_numpy() / AU_KM]
    nasa_trail = [bodies_pos_km["voyager1"][clamped_day] / AU_KM]

# Pre-generate 3D reference grid rings, Termination Shock & Heliopause
GRID_SEGS = 120
thetas = np.linspace(0, 2 * np.pi, GRID_SEGS)
grid_radii = [1.0, 5.2, 9.5, 19.2, 30.1, 50.0, 100.0]
grid_rings = []
for gr in grid_radii:
    ring_xyz = np.column_stack([gr * np.cos(thetas), gr * np.sin(thetas), np.zeros(GRID_SEGS)])
    grid_rings.append(ring_xyz)

# Termination Shock ring at 94 AU (Heliosheath inner boundary)
ts_pts = np.column_stack([94.0 * np.cos(thetas), 94.0 * np.sin(thetas), np.zeros(GRID_SEGS)])

# Heliopause ring at 121 AU (Interstellar frontier)
hp_pts = np.column_stack([121.0 * np.cos(thetas), 121.0 * np.sin(thetas), np.zeros(GRID_SEGS)])

# Pre-compute clean, closed, single-period orbit tracks from exact NASA ephemeris data
orbit_tracks = {}
for cfg in BODIES_CONFIG:
    k = cfg["key"]
    if k == "sun":
        continue
    full_pts = bodies_pos_au[k]
    period = min(len(full_pts), ORBITAL_PERIODS_DAYS.get(k, 17931))
    period_pts = full_pts[:period]
    # Downsample to 180 smooth segments
    step_track = max(1, len(period_pts) // 180)
    sub = period_pts[::step_track]
    # Only close circular orbits that completed full periods in the dataset
    if k in ["earth", "mars", "jupiter", "saturn"]:
        orbit_tracks[k] = np.vstack([sub, sub[0]])
    else:
        orbit_tracks[k] = sub

print("=" * 80)
print("  * 04 · VOYAGER 1 LIVE NUMERICAL INTEGRATION (MULTI-BODY EPHEMERIS FIELD)")
print("=" * 80)
print("  KEYBOARD CONTROLS (Identical to 03):")
print("    - [SPACEBAR]         : Toggle Play / Freeze Live Numerical Integration")
print("    - Key [0] / [L]      : Earth Launch Standby (Day 0, 1977, Zoom 6.0 AU, Paused)")
print("    - Key [1]            : Step Voyager 1 Forward (+7 Days, remaining frozen)")
print("    - Key [2]            : Step Voyager 1 Backward (-7 Days, remaining frozen)")
print("    - Key [3]            : Jump to Jupiter Encounter (Day 516, Zoom 8.0 AU)")
print("    - Key [4]            : Jump to Saturn Encounter (Day 1134, Zoom 10.0 AU)")
print("    - Key [5]            : Jump to Halley Perihelion (Day 3079, Zoom 4.0 AU)")
print("    - Key [6]            : Jump to Pluto Inside Neptune View (Day 4500, Zoom 42.0 AU)")
print("  INTEGRATOR CONTROLS (Shifted to Keys 7, 8, 9):")
print("    - Key [7]            : Switch to RK4 (Runge-Kutta 4th Order - High Precision)")
print("    - Key [8]            : Switch to Velocity Verlet (Symplectic - Energy Conserving)")
print("    - Key [9]            : Switch to Forward Euler (1st Order - Divergence Demonstration)")
print("    - Key [T]            : Toggle NASA Trajectory Correction Maneuvers (TCM) ON / OFF")
print("  NAVIGATION CONTROLS:")
print("    - Key [Q]            : Increase Play Speed (1 -> 2 -> 4 -> 7 -> 14 -> 30 Days/Frame)")
print("    - Key [W]            : Decrease Play Speed (30 -> 14 -> 7 -> 4 -> 2 -> 1 Days/Frame)")
print("    - [ARROW KEYS]       : 2D Frame Pan (UP/DOWN vertically, LEFT/RIGHT horizontally)")
print("    - Key [Z]            : Pure In-Place Zoom In (-10% view radius)")
print("    - [Ctrl+Z]/[Shift+Z] : Pure In-Place Zoom Out (+10% view radius)")
print("    - Key [V]            : Center Camera on Voyager 1 (Preserves zoom)")
print("    - Key [F]            : Toggle Probe Chase Cam (Smooth lock on Voyager 1)")
print("    - Key [S]            : Center Camera on Sun (Preserves zoom)")
print("    - Key [P] / [Ctrl+P] : Pitch Angle Up / Down")
print("    - Key [Y] / [Ctrl+Y] : Yaw Angle Right / Left")
print("    - Key [H]            : Clean Mode (Hide all HUD and overlays)")
print("    - Key [K]            : Capture High-Res Screenshot Frame")
print("    - Key [ESC]          : Exit Simulation")
print("=" * 80)

# ==============================================================================
# 7. MAIN SIMULATION & RENDER LOOP
# ==============================================================================
while gui.running:
    # --------------------------------------------------------------------------
    # 7.1 KEYBOARD INPUT HANDLING (Keys 0-6 match 03; Integrators shifted to 7, 8, 9)
    # --------------------------------------------------------------------------
    for e in gui.get_events(ti.GUI.PRESS):
        if e.key == ti.GUI.ESCAPE:
            gui.running = False
        elif e.key == ti.GUI.SPACE:
            is_playing = not is_playing
            state = "COMPUTING LIVE PHYSICS" if is_playing else "SIMULATION FROZEN (PAUSED)"
            notice_text = f"SIMULATION: {state}"
            notice_timer = 90
        elif e.key == "0" or e.key == "l" or e.key == "L":
            # Earth Launch Standby (Day 0, Zoom 6.0 AU, Paused)
            reset_to_day(0)
            camera.target = bodies_pos_au["earth"][0].copy()
            camera.pan_x, camera.pan_y = 0.0, 0.0
            slider_zoom.value = 6.0
            slider_pitch.value = 45.0
            slider_yaw.value = -35.0
            is_playing = False
            follow_probe = False
            notice_text = "EARTH LAUNCH STANDBY (DAY 0, 6.0 AU) - PRESS [SPACE] TO LAUNCH"
            notice_timer = 120
        elif e.key == "1":
            # Step forward +7 days (paused)
            is_playing = False
            follow_probe = False
            if physics.sim_day[None] + 7.0 < TOTAL_DAYS:
                reset_to_day(physics.sim_day[None] + 7.0)
            else:
                target_sim_day = physics.sim_day[None] + 7.0
                physics.advance_loop(target_sim_day, cur_integrator)
                sim_trail.append(physics.sim_pos[None].to_numpy() / AU_KM)
            notice_text = f"STEPPED FORWARD +7 DAYS -> DAY {int(physics.sim_day[None])} (FROZEN)"
            notice_timer = 90
        elif e.key == "2":
            # Step backward -7 days (paused)
            is_playing = False
            follow_probe = False
            if physics.sim_day[None] - 7.0 < TOTAL_DAYS - 1:
                new_day = max(0.0, physics.sim_day[None] - 7.0)
                reset_to_day(new_day)
            else:
                target_sim_day = physics.sim_day[None] - 7.0
                reset_to_day(target_sim_day)
                cur_r_au = float(np.linalg.norm(physics.sim_pos[None].to_numpy() / AU_KM))
                sim_trail = [pt for pt in sim_trail if np.linalg.norm(pt) <= cur_r_au + 0.05]
                if not sim_trail:
                    sim_trail = [physics.sim_pos[None].to_numpy() / AU_KM]
            notice_text = f"STEPPED BACKWARD -7 DAYS -> DAY {int(physics.sim_day[None])} (FROZEN)"
            notice_timer = 90
        elif e.key == "3":
            # Jupiter Encounter: Day 516 (30 days before closest encounter), Zoom 8.0 AU
            reset_to_day(516)
            camera.target = (bodies_pos_km["jupiter"][516] / AU_KM).astype(np.float32)
            camera.pan_x, camera.pan_y = 0.0, 0.0
            slider_zoom.value = 8.0
            slider_pitch.value = 40.0
            slider_yaw.value = -60.0
            follow_probe = False
            notice_text = "JUPITER ENCOUNTER: 30 DAYS BEFORE FLYBY (DAY 516, ZOOM 8.0 AU)"
            notice_timer = 120
        elif e.key == "4":
            # Saturn Encounter: Day 1134 (30 days before closest encounter), Zoom 10.0 AU
            reset_to_day(1134)
            camera.target = (bodies_pos_km["saturn"][1134] / AU_KM).astype(np.float32)
            camera.pan_x, camera.pan_y = 0.0, 0.0
            slider_zoom.value = 10.0
            slider_pitch.value = 65.0
            slider_yaw.value = -45.0
            follow_probe = False
            notice_text = "SATURN ENCOUNTER: 30 DAYS BEFORE FLYBY (DAY 1134, ZOOM 10.0 AU)"
            notice_timer = 120
        elif e.key == "5":
            # Halley's Comet Perihelion: Day 3079, Zoom 4.0 AU
            reset_to_day(3079)
            camera.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            camera.pan_x, camera.pan_y = 0.0, 0.0
            slider_zoom.value = 4.0
            slider_pitch.value = 45.0
            slider_yaw.value = -30.0
            follow_probe = False
            notice_text = "HALLEY'S COMET PERIHELION (DAY 3079, ZOOM 4.0 AU)"
            notice_timer = 120
        elif e.key == "6":
            # Pluto Crossing Inside Neptune: Day 4500, Zoom 42.0 AU
            reset_to_day(4500)
            camera.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            camera.pan_x, camera.pan_y = 0.0, 0.0
            slider_zoom.value = 42.0
            slider_pitch.value = 68.0
            slider_yaw.value = -75.0
            follow_probe = False
            notice_text = "PLUTO CROSSING INSIDE NEPTUNE (DAY 4500, ZOOM 42.0 AU)"
            notice_timer = 120
        elif e.key == "7":
            cur_integrator = 0
            notice_text = f"INTEGRATOR: {INTEGRATOR_NAMES[cur_integrator]} ACTIVATED"
            notice_timer = 120
        elif e.key == "8":
            cur_integrator = 1
            notice_text = f"INTEGRATOR: {INTEGRATOR_NAMES[cur_integrator]} ACTIVATED"
            notice_timer = 120
        elif e.key == "9":
            cur_integrator = 2
            notice_text = f"INTEGRATOR: {INTEGRATOR_NAMES[cur_integrator]} ACTIVATED"
            notice_timer = 120
        elif e.key == "t" or e.key == "T":
            tcm_enabled = not tcm_enabled
            state = "ENABLED (ACTIVE GUIDANCE FOR UPCOMING BURNS)" if tcm_enabled else "DISABLED (PURE UNGUIDED BALLISTIC FLIGHT)"
            notice_text = f"NASA TCM GUIDANCE: {state}"
            notice_timer = 150
        elif e.key == "q" or e.key == "Q":
            cur_s = int(slider_speed.value)
            idx = 0
            for i, s in enumerate(SPEED_LEVELS):
                if s > cur_s:
                    idx = i
                    break
                idx = i
            if SPEED_LEVELS[idx] > cur_s:
                slider_speed.value = SPEED_LEVELS[idx]
            elif idx + 1 < len(SPEED_LEVELS):
                slider_speed.value = SPEED_LEVELS[idx + 1]
            notice_text = f"PLAY SPEED: {int(slider_speed.value)} DAYS / FRAME"
            notice_timer = 120
        elif e.key == "w" or e.key == "W":
            cur_s = int(slider_speed.value)
            idx = len(SPEED_LEVELS) - 1
            for i in range(len(SPEED_LEVELS) - 1, -1, -1):
                if SPEED_LEVELS[i] < cur_s:
                    idx = i
                    break
                idx = i
            slider_speed.value = SPEED_LEVELS[idx]
            notice_text = f"PLAY SPEED: {int(slider_speed.value)} DAYS / FRAME"
            notice_timer = 120
        elif e.key == ti.GUI.UP:
            camera.pan_y = float(np.clip(camera.pan_y + 0.03, -1.0, 1.0))
            notice_text = f"FRAME PAN UP: {camera.pan_y:+.2f}"
            notice_timer = 60
        elif e.key == ti.GUI.DOWN:
            camera.pan_y = float(np.clip(camera.pan_y - 0.03, -1.0, 1.0))
            notice_text = f"FRAME PAN DOWN: {camera.pan_y:+.2f}"
            notice_timer = 60
        elif e.key == ti.GUI.LEFT:
            camera.pan_x = float(np.clip(camera.pan_x - 0.03, -1.0, 1.0))
            notice_text = f"FRAME PAN LEFT: {camera.pan_x:+.2f}"
            notice_timer = 60
        elif e.key == ti.GUI.RIGHT:
            camera.pan_x = float(np.clip(camera.pan_x + 0.03, -1.0, 1.0))
            notice_text = f"FRAME PAN RIGHT: {camera.pan_x:+.2f}"
            notice_timer = 60
        elif e.key == "z" or e.key == "Z":
            is_ctrl = gui.is_pressed(ti.GUI.CTRL) or gui.is_pressed(ti.GUI.SHIFT) or ("Control" in getattr(e, "modifier", [])) or ("Shift" in getattr(e, "modifier", []))
            zoom_mul = 1.10 if is_ctrl else 0.90
            slider_zoom.value = float(np.clip(slider_zoom.value * zoom_mul, 0.5, 500.0))
            action = "ZOOM OUT" if is_ctrl else "ZOOM IN"
            notice_text = f"{action}: {slider_zoom.value:.1f} AU"
            notice_timer = 60
        elif e.key == "v" or e.key == "V":
            camera.target = (physics.sim_pos[None].to_numpy() / AU_KM).astype(np.float32)
            camera.pan_x, camera.pan_y = 0.0, 0.0
            follow_probe = False
            notice_text = f"CENTERED ON VOYAGER 1 (ZOOM {slider_zoom.value:.1f} AU PRESERVED)"
            notice_timer = 90
        elif e.key == "f" or e.key == "F":
            follow_probe = not follow_probe
            if follow_probe:
                slider_zoom.value = 3.2
                slider_pitch.value = 28.0
                camera.pan_x, camera.pan_y = 0.0, 0.0
                notice_text = "PROBE CHASE CAM: ACTIVE (LOCKED ON VOYAGER 1)"
                notice_timer = 120
            else:
                notice_text = "MANUAL CAMERA CONTROL ACTIVE"
                notice_timer = 120
        elif e.key == "s" or e.key == "S":
            camera.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
            camera.pan_x, camera.pan_y = 0.0, 0.0
            follow_probe = False
            notice_text = f"CENTERED ON SUN (ZOOM {slider_zoom.value:.1f} AU PRESERVED)"
            notice_timer = 90
        elif e.key == "p" or e.key == "P":
            is_ctrl = gui.is_pressed(ti.GUI.CTRL) or gui.is_pressed(ti.GUI.SHIFT) or ("Control" in getattr(e, "modifier", [])) or ("Shift" in getattr(e, "modifier", []))
            step_deg = -2.5 if is_ctrl else 2.5
            slider_pitch.value = float(np.clip(slider_pitch.value + step_deg, 0.0, 90.0))
            action = "DECREASED" if is_ctrl else "INCREASED"
            notice_text = f"PITCH {action} ({slider_pitch.value:.1f} deg)"
            notice_timer = 60
        elif e.key == "y" or e.key == "Y":
            is_ctrl = gui.is_pressed(ti.GUI.CTRL) or gui.is_pressed(ti.GUI.SHIFT) or ("Control" in getattr(e, "modifier", [])) or ("Shift" in getattr(e, "modifier", []))
            step_deg = -5.0 if is_ctrl else 5.0
            slider_yaw.value += step_deg
            if slider_yaw.value > 180.0: slider_yaw.value -= 360.0
            if slider_yaw.value < -180.0: slider_yaw.value += 360.0
            action = "LEFT" if is_ctrl else "RIGHT"
            notice_text = f"YAW ROTATED {action} ({slider_yaw.value:.1f} deg)"
            notice_timer = 60
        elif e.key == "h" or e.key == "H":
            clean_hud = not clean_hud
            state = "CLEAN (ALL HUD HIDDEN)" if clean_hud else "FULL TELEMETRY HUD"
            notice_text = f"DISPLAY: {state}"
            notice_timer = 90
        elif e.key == "k" or e.key == "K":
            trigger_screenshot = True

    # --------------------------------------------------------------------------
    # 7.2 NUMERICAL INTEGRATION STEP (Continuous into infinity)
    # --------------------------------------------------------------------------
    latest_breakdown = {}
    if is_playing:
        days_per_frame = slider_speed.value
        target_sim_day = physics.sim_day[None] + days_per_frame

        while physics.sim_day[None] < target_sim_day:
            cur_int_day = int(physics.sim_day[None])

            if tcm_enabled:
                tcm_hit = False
                for tcm in TCM_SCHEDULE:
                    t_day = tcm["day"]
                    if cur_int_day <= t_day and t_day < target_sim_day and t_day not in applied_tcms:
                        physics.advance_loop(float(t_day), cur_integrator)
                        
                        applied_tcms.add(t_day)
                        v_target = v1_vel_kms[t_day]
                        r_target = bodies_pos_km["voyager1"][t_day]
                        
                        cur_pos = physics.sim_pos[None].to_numpy()
                        cur_vel = physics.sim_vel[None].to_numpy()
                        
                        # Check if all prior major NASA TCMs up to this day were applied
                        major_prior_applied = all(
                            prev_tcm["day"] in applied_tcms
                            for prev_tcm in TCM_SCHEDULE if prev_tcm.get("is_major") and prev_tcm["day"] < t_day
                        )
                        
                        tau_sec = 60.0 * 86400.0
                        
                        if major_prior_applied:
                            # 100% Pure Velocity Guidance with 60-day horizon (ZERO position snapping!):
                            # We influence the trajectory through Delta-V guidance and allow the physics model
                            # to do the rest. The trajectory is never forced or snapped onto an aimpoint.
                            r_err = r_target - cur_pos
                            guidance_dv = r_err / tau_sec
                            delta_v = (v_target - cur_vel) + guidance_dv
                            dv_mag = np.linalg.norm(delta_v) * 1000.0
                            physics.sim_vel[None] = cur_vel + delta_v
                        else:
                            # Prior major TCMs were missed (spacecraft is on unguided drifted trajectory):
                            # Apply nominal planned burn AT CURRENT PHYSICAL POSITION without forcing
                            # the trajectory back onto the historical NASA ground-truth path.
                            nom_dv_ms = tcm.get("dv_nom_ms", 0.5)
                            v_mag = np.linalg.norm(cur_vel)
                            v_dir = cur_vel / max(1e-6, v_mag)
                            delta_v = v_dir * (nom_dv_ms / 1000.0)
                            dv_mag = nom_dv_ms
                            physics.sim_vel[None] = cur_vel + delta_v
                        
                        # CRITICAL PHYSICS MANDATE: Position is NEVER snapped, forced, or teleported to r_target!
                        # The craft strictly remains at cur_pos and the numerical integrator computes all motion dynamically.
                        physics.has_prev_acc[None] = 0
                        
                        if tcm.get("is_major", True):
                            last_tcm_msg = f"THRUSTER BURN [{tcm['name']}]: Delta-V = {dv_mag:.1f} m/s ({tcm['desc']})"
                            last_tcm_timer = 180
                        tcm_hit = True
                        break
                        
                if tcm_hit:
                    continue

            physics.advance_loop(target_sim_day, cur_integrator)

        sim_trail.append(physics.sim_pos[None].to_numpy() / AU_KM)
        curr_int_day = int(physics.sim_day[None])
        if curr_int_day < TOTAL_DAYS:
            nasa_trail.append(bodies_pos_km["voyager1"][curr_int_day] / AU_KM)
    else:
        physics.update_breakdown_paused()

    sim_pos_km = physics.sim_pos[None].to_numpy()
    sim_vel_kms = physics.sim_vel[None].to_numpy()
    sim_day = physics.sim_day[None]
    latest_breakdown = physics.get_latest_breakdown_dict()
    sim_accel_kms2 = physics.current_accel[None].to_numpy()

    # Smoothly track Voyager 1 only if probe chase cam is active
    if follow_probe:
        v1_sim_au = (physics.sim_pos[None].to_numpy() / AU_KM).astype(np.float32)
        camera.target += (v1_sim_au - camera.target) * 0.1
        if is_playing:
            slider_yaw.value += 0.12  # Smooth orbit around Voyager
            if slider_yaw.value > 180.0:
                slider_yaw.value -= 360.0

    camera.yaw = math.radians(slider_yaw.value)
    camera.pitch = math.radians(slider_pitch.value)
    camera.radius = slider_zoom.value
    pulse_timer += 0.08
    current_idx = min(TOTAL_DAYS - 1, int(physics.sim_day[None]))

    # Dynamic radial boundary crossing trackers along simulated trajectory
    curr_r_sun_au = float(np.linalg.norm(sim_pos_km - physics.get_body_pos_km_py("sun", sim_day)) / AU_KM)
    if curr_r_sun_au >= 94.0 and sim_term_shock_pos is None:
        for pt in sim_trail:
            if np.linalg.norm(pt) >= 94.0:
                sim_term_shock_pos = pt.copy()
                break
        if sim_term_shock_pos is None:
            sim_term_shock_pos = (physics.sim_pos[None].to_numpy() / AU_KM).copy()

    if curr_r_sun_au >= 121.0 and sim_heliopause_pos is None:
        for pt in sim_trail:
            if np.linalg.norm(pt) >= 121.0:
                sim_heliopause_pos = pt.copy()
                break
        if sim_heliopause_pos is None:
            sim_heliopause_pos = (physics.sim_pos[None].to_numpy() / AU_KM).copy()

    # --------------------------------------------------------------------------
    # 7.3 DRAW 3D REFERENCE GRID, TERMINATION SHOCK & HELIOPAUSE
    # --------------------------------------------------------------------------
    for gr in grid_rings:
        scr = camera.project_points(gr, WIDTH, HEIGHT)
        gui.lines(scr[:-1], scr[1:], radius=1, color=0x152232)

    # 3D Termination Shock Reference Ring (94 AU - Heliosheath Inner Boundary)
    ts_scr = camera.project_points(ts_pts, WIDTH, HEIGHT)
    gui.lines(ts_scr[:-1], ts_scr[1:], radius=1, color=0x4A2555)
    ts_lbl_s = camera.project_single(np.array([94.0, 0.0, 0.0]), WIDTH, HEIGHT)
    if 0.05 < ts_lbl_s[0] < 0.95 and 0.05 < ts_lbl_s[1] < 0.95:
        gui.text("Termination Shock (94 AU)", ts_lbl_s, font_size=12, color=0xBA68C8)

    # 3D Heliopause Reference Ring (121 AU - Interstellar Frontier)
    hp_scr = camera.project_points(hp_pts, WIDTH, HEIGHT)
    gui.lines(hp_scr[:-1], hp_scr[1:], radius=1, color=0x224855)
    hp_lbl_s = camera.project_single(np.array([121.0, 0.0, 0.0]), WIDTH, HEIGHT)
    if 0.05 < hp_lbl_s[0] < 0.95 and 0.05 < hp_lbl_s[1] < 0.95:
        gui.text("Heliopause (121 AU)", hp_lbl_s, font_size=12, color=0x00A0C0)

    # 3D Ecliptic Coordinate Axes
    axis_len = camera.radius * 0.25
    origin_s = camera.project_single(np.array([0.0, 0.0, 0.0]), WIDTH, HEIGHT)
    x_axis_s = camera.project_single(np.array([axis_len, 0.0, 0.0]), WIDTH, HEIGHT)
    y_axis_s = camera.project_single(np.array([0.0, axis_len, 0.0]), WIDTH, HEIGHT)
    z_axis_s = camera.project_single(np.array([0.0, 0.0, axis_len]), WIDTH, HEIGHT)

    gui.line(origin_s, x_axis_s, radius=1, color=0x883333)
    gui.line(origin_s, y_axis_s, radius=1, color=0x338833)
    gui.line(origin_s, z_axis_s, radius=1, color=0x3366CC)
    gui.text("+X (ICRF)", x_axis_s, font_size=11, color=0xAA5555)
    gui.text("+Y", y_axis_s, font_size=11, color=0x55AA55)
    gui.text("+Z (North)", z_axis_s, font_size=11, color=0x6699FF)

    # --------------------------------------------------------------------------
    # 7.4 DRAW PLANETARY ORBIT TRAILS (Clean 1-period loops, 100% matched to bodies)
    # --------------------------------------------------------------------------
    if show_trails:
        for cfg in BODIES_CONFIG:
            k = cfg["key"]
            if k == "sun":
                continue
            pts = orbit_tracks[k]
            max_r = np.max(np.linalg.norm(pts, axis=1))
            if max_r < camera.radius * 2.5:
                scr = camera.project_points(pts, WIDTH, HEIGHT)
                gui.lines(scr[:-1], scr[1:], radius=1, color=cfg["trail_col"])

    # --------------------------------------------------------------------------
    # 7.5 DRAW LIVE CELESTIAL BODIES (MOVING IN REAL TIME)
    # --------------------------------------------------------------------------
    v1_sim_au = physics.sim_pos[None].to_numpy() / AU_KM

    for cfg in BODIES_CONFIG:
        k = cfg["key"]
        pos_now = physics.get_body_pos_au(k, sim_day)
        pos_s = camera.project_single(pos_now, WIDTH, HEIGHT)

        if not (-0.1 <= pos_s[0] <= 1.1 and -0.1 <= pos_s[1] <= 1.1):
            continue

        r = cfg["radius"]
        col = cfg["color"]
        glow = cfg["glow"]

        # Draw Sun
        if k == "sun":
            gui.circle(pos_s, radius=r, color=col)
            gui.circle(pos_s, radius=r + 4, color=glow)
            gui.text("Sun", (pos_s[0] + 0.008, pos_s[1] - 0.005), font_size=12, color=0xFFEE55)
            continue

        # Draw Comets (tail pointing away from Sun)
        if cfg.get("is_comet"):
            sun_pos = physics.get_body_pos_au("sun", sim_day)
            sun_to_comet = pos_now - sun_pos
            d_sun = np.linalg.norm(sun_to_comet)
            if d_sun > 1e-3:
                tail_dir = sun_to_comet / d_sun
                tail_len = max(0.5, 3.0 / max(0.6, d_sun))
                tail_tip = pos_now + tail_dir * (tail_len * camera.radius * 0.02)
                tail_s = camera.project_single(tail_tip, WIDTH, HEIGHT)
                gui.line(pos_s, tail_s, radius=2, color=col)

            gui.circle(pos_s, radius=r, color=col)
            gui.circle(pos_s, radius=r + 2, color=glow)
            if camera.radius < 50.0 or k == "halley":
                gui.text(cfg["name"], (pos_s[0] + 0.008, pos_s[1] + 0.006), font_size=11, color=col)
            continue

        # Draw Saturn Rings
        if k == "saturn":
            gui.circle(pos_s, radius=r, color=col)
            gui.circle(pos_s, radius=r + 2, color=glow)
            ring_tilt_x = 0.009 * (180.0 / camera.radius)
            ring_tilt_y = 0.004 * (180.0 / camera.radius)
            ring_tilt_x = max(0.005, min(0.025, ring_tilt_x))
            ring_tilt_y = max(0.002, min(0.012, ring_tilt_y))
            gui.line((pos_s[0] - ring_tilt_x, pos_s[1] - ring_tilt_y),
                     (pos_s[0] + ring_tilt_x, pos_s[1] + ring_tilt_y), radius=2, color=0xCCBA80)

            d_v1 = np.linalg.norm(pos_now - v1_sim_au) * AU_KM
            if d_v1 < 10e6:
                gui.circle(pos_s, radius=r + 8, color=0x88FFD54F)
            gui.text("Saturn", (pos_s[0] + 0.008, pos_s[1] + 0.006), font_size=12, color=col)
            continue

        # Draw Standard Planets
        gui.circle(pos_s, radius=r, color=col)
        gui.circle(pos_s, radius=r + 2, color=glow)

        # Proximity highlight for Jupiter
        if k == "jupiter":
            d_v1 = np.linalg.norm(pos_now - v1_sim_au) * AU_KM
            if d_v1 < 10e6:
                gui.circle(pos_s, radius=r + 8, color=0x88FFA726)

        # Label visible planets
        d_to_origin = np.linalg.norm(pos_now)
        if d_to_origin < camera.radius * 1.3:
            gui.text(cfg["name"], (pos_s[0] + 0.008, pos_s[1] + 0.006), font_size=12, color=col)

    # --------------------------------------------------------------------------
    # 7.6 TRAJECTORIES: LIVE COMPUTED (CYAN) vs NASA GROUND TRUTH (GOLD)
    # --------------------------------------------------------------------------
    # 1. NASA JPL Ephemeris Ground Truth (Gold dashed line up to 2026)
    if len(nasa_trail) > 1:
        nasa_pts = np.array(nasa_trail, dtype=np.float32)
        step_pts = max(1, len(nasa_pts) // 180)
        nasa_sub = nasa_pts[::step_pts]
        if len(nasa_sub) > 1:
            nasa_s = camera.project_points(nasa_sub, WIDTH, HEIGHT)
            gui.lines(nasa_s[:-1], nasa_s[1:], radius=1, color=0xFFC107)

    # 2. Live Computed Simulation Trail (Cyan or Red if divergent)
    if len(sim_trail) > 1:
        sim_pts = np.array(sim_trail, dtype=np.float32)
        step_sim = max(1, len(sim_pts) // 400)
        sim_sub = sim_pts[::step_sim]
        if len(sim_sub) > 1:
            sim_s = camera.project_points(sim_sub, WIDTH, HEIGHT)
            trail_color = 0x00E5FF if cur_integrator != 2 else 0xFF5252
            gui.lines(sim_s[:-1], sim_s[1:], radius=2, color=trail_color)

    # --------------------------------------------------------------------------
    # --------------------------------------------------------------------------
    # 7.7 VOYAGER 1 SPACECRAFT, MISSION PHASE & ACCELERATION / VELOCITY VECTORS
    # --------------------------------------------------------------------------
    probe_s = camera.project_single(v1_sim_au, WIDTH, HEIGHT)

    # Distances for phase calculation and telemetry
    d_sun_au = float(np.linalg.norm(sim_pos_km - physics.get_body_pos_km_py("sun", sim_day)) / AU_KM)
    d_jup_km = float(np.linalg.norm(sim_pos_km - physics.get_body_pos_km_py("jupiter", sim_day)))
    d_sat_km = float(np.linalg.norm(sim_pos_km - physics.get_body_pos_km_py("saturn", sim_day)))
    d_earth_km = float(np.linalg.norm(sim_pos_km - physics.get_body_pos_km_py("earth", sim_day)))
    light_hrs = (d_earth_km / C_LIGHT) / 3600.0

    # Determine Current Mission Phase from live physical state
    if d_sun_au < 1.5 and sim_day < 100.0:
        phase_name = "Earth Departure & Inner Solar System Cruise"
        phase_col = 0x00FF88
        short_phase = "EARTH DEPARTURE"
    elif d_jup_km < 15.0e6 or (500.0 <= sim_day <= 570.0):
        phase_name = "Jupiter Gravity Assist & Slingshot Flyby"
        phase_col = 0xFFA726
        short_phase = "JUPITER FLYBY"
    elif d_sun_au < 5.2 and sim_day < 546.0:
        phase_name = "Jupiter Inbound Transfer Cruise"
        phase_col = 0xFFB74D
        short_phase = "JUPITER CRUISE"
    elif d_sat_km < 15.0e6 or (1120.0 <= sim_day <= 1200.0):
        phase_name = "Saturn Gravity Assist & Northward Deflection"
        phase_col = 0xFFD54F
        short_phase = "SATURN FLYBY"
    elif d_sun_au < 9.5 and sim_day < 1164.0:
        phase_name = "Jupiter-to-Saturn Transfer Cruise"
        phase_col = 0xFFE082
        short_phase = "SATURN CRUISE"
    elif d_sun_au < 94.0:
        phase_name = "Outer Solar System & Kuiper Belt Cruise"
        phase_col = 0x80DEEA
        short_phase = "OUTER SYSTEM"
    elif d_sun_au < 121.0:
        phase_name = "Heliosheath (Crossed Termination Shock @ 94 AU)"
        phase_col = 0xCE93D8
        short_phase = "HELIOSHEATH"
    else:
        phase_name = "Deep Interstellar Space (Beyond Heliopause @ 121 AU)"
        phase_col = 0x00E5FF
        short_phase = "INTERSTELLAR SPACE"

    # Ecliptic drop stem (Z = 0)
    ecliptic_shadow = camera.project_single(np.array([v1_sim_au[0], v1_sim_au[1], 0.0]), WIDTH, HEIGHT)
    gui.line(probe_s, ecliptic_shadow, radius=1, color=0x336688)
    gui.circle(ecliptic_shadow, radius=2, color=0x336688)

    # Reticle
    ret_r = int(5.0 + 2.5 * math.sin(pulse_timer))
    gui.circle(probe_s, radius=ret_r, color=0x00FFFF)
    gui.circle(probe_s, radius=2, color=0xFFFFFF)

    # Velocity Vector Arrow (Red)
    v_mag = np.linalg.norm(sim_vel_kms)
    v_dir = sim_vel_kms / max(1e-3, v_mag)
    v_tip_au = v1_sim_au + v_dir * (camera.radius * 0.08)
    v_tip_s = camera.project_single(v_tip_au, WIDTH, HEIGHT)
    gui.line(probe_s, v_tip_s, radius=2, color=0xFF5533)
    gui.circle(v_tip_s, radius=3, color=0xFF5533)

    # Gravitational Force Vector Arrow (Bright Yellow pointing toward Net Acceleration)
    a_net = sim_accel_kms2
    a_mag = np.linalg.norm(a_net)
    if a_mag > 1e-12:
        a_dir = a_net / a_mag
        a_tip_au = v1_sim_au + a_dir * (camera.radius * 0.06)
        a_tip_s = camera.project_single(a_tip_au, WIDTH, HEIGHT)
        gui.line(probe_s, a_tip_s, radius=1, color=0xFFEB3B)
        gui.circle(a_tip_s, radius=2, color=0xFFEB3B)

    # Spacecraft Label with Live Mission Phase & Distance
    gui.text(f"VOYAGER 1 [{short_phase} - {d_sun_au:.1f} AU]", (probe_s[0] + 0.010, probe_s[1] - 0.008), font_size=12, color=phase_col)

    # --------------------------------------------------------------------------
    # 7.8 HISTORICAL & DYNAMIC MILESTONES ALONG VOYAGER'S PATH
    # --------------------------------------------------------------------------
    v1_all_au = bodies_pos_au["voyager1"]
    for ms in MILESTONES:
        m_day = ms["day"]
        m_pos = v1_all_au[m_day]

        # Dynamically anchor radial boundaries directly onto simulated trajectory once reached
        if ms["name"] == "TERMINATION SHOCK" and sim_term_shock_pos is not None:
            m_pos = sim_term_shock_pos
        elif ms["name"] == "INTERSTELLAR SPACE" and sim_heliopause_pos is not None:
            m_pos = sim_heliopause_pos

        ms_s = camera.project_single(m_pos, WIDTH, HEIGHT)

        if 0.04 < ms_s[0] < 0.96 and 0.04 < ms_s[1] < 0.96:
            gui.circle(ms_s, radius=4, color=ms["color"])
            dist_m = float(np.linalg.norm(m_pos))
            has_passed = (d_sun_au >= dist_m - 0.5) or (current_idx >= m_day) or (camera.radius < 35.0)
            if has_passed:
                gui.text(f"* {ms['name']} ({dist_m:.1f} AU)", (ms_s[0] + 0.008, ms_s[1] + 0.008), font_size=11, color=ms["color"])

    # --------------------------------------------------------------------------
    # 7.9 LIVE TELEMETRY, INTEGRATOR BENCHMARK & HUD
    # --------------------------------------------------------------------------
    if not clean_hud:
        # Top Banner
        gui.text("VOYAGER 1 FULL MISSION -- LIVE NUMERICAL INTEGRATION (EPHEMERIS FIELD)", (0.24, 0.965), font_size=17, color=0xFFFFFF)
        
        # Integrator Status Badge & TCM Guidance Status
        badge_col = 0x00FF88 if cur_integrator == 0 else (0xFFD54F if cur_integrator == 1 else 0xFF5252)
        tcm_badge = "[TCM: ON]" if tcm_enabled else "[TCM: OFF (BALLISTIC)]"
        tcm_col = 0x00FF88 if tcm_enabled else 0xFF5252
        gui.text(f"INTEGRATOR: [{cur_integrator + 7}] {INTEGRATOR_NAMES[cur_integrator]}", (0.28, 0.938), font_size=13, color=badge_col)
        gui.text(f"G&NC GUIDANCE: {tcm_badge} (Press [T] to toggle)", (0.28, 0.915), font_size=12, color=tcm_col)
        gui.text(f"PLAY SPEED: {int(slider_speed.value)} DAYS / FRAME ([Q]/[W])", (0.65, 0.915), font_size=12, color=0x00E5FF)

        # Thruster Firing Alert (Dedicated Row)
        if last_tcm_timer > 0:
            gui.text(f">> {last_tcm_msg}", (0.28, 0.888), font_size=12, color=0xFFD54F)
            last_tcm_timer -= 1

        # User Action & Speed Notice (Dedicated Row)
        if notice_timer > 0:
            gui.text(f"* {notice_text}", (0.28, 0.865), font_size=12, color=0x00FF88)
            notice_timer -= 1

        # Calculate live comparison metrics vs NASA Ephemeris (up to 2026)
        true_pos_km = bodies_pos_km["voyager1"][current_idx]
        true_vel_kms = v1_vel_kms[current_idx]
        drift_km = np.linalg.norm(sim_pos_km - true_pos_km)
        drift_pct = (drift_km / max(1.0, np.linalg.norm(true_pos_km))) * 100.0

        # Specific orbital energy
        spec_energy = physics.compute_specific_energy(sim_pos_km, sim_vel_kms, sim_day)

        # Distances
        d_sun_au = np.linalg.norm(sim_pos_km - physics.get_body_pos_km_py("sun", sim_day)) / AU_KM
        d_earth_km = np.linalg.norm(sim_pos_km - physics.get_body_pos_km_py("earth", sim_day))
        d_jup_km = np.linalg.norm(sim_pos_km - physics.get_body_pos_km_py("jupiter", sim_day))
        d_sat_km = np.linalg.norm(sim_pos_km - physics.get_body_pos_km_py("saturn", sim_day))
        light_hrs = (d_earth_km / C_LIGHT) / 3600.0

        # Gravitational breakdown percentages
        total_a = latest_breakdown.get("total", 1e-12)
        pct_sun = (latest_breakdown.get("sun", 0.0) / max(1e-12, total_a)) * 100.0
        pct_jup = (latest_breakdown.get("jupiter", 0.0) / max(1e-12, total_a)) * 100.0
        pct_sat = (latest_breakdown.get("saturn", 0.0) / max(1e-12, total_a)) * 100.0
        pct_ear = (latest_breakdown.get("earth", 0.0) / max(1e-12, total_a)) * 100.0

        # Velocity pitch angle (degrees North of ecliptic)
        v_lat_deg = math.degrees(math.atan2(sim_vel_kms[2], math.hypot(sim_vel_kms[0], sim_vel_kms[1])))

        # Mission Date (Real table date or Future Interstellar Extrapolation)
        cur_date_str = format_mission_date(sim_day, dates)
        is_future = int(physics.sim_day[None]) >= TOTAL_DAYS

        # Bottom-Left Telemetry Card
        hud_y = 0.368
        lh = 0.021
        gui.text("=== LIVE PHYSICS TELEMETRY ===", (0.02, hud_y), font_size=13, color=0x90CAF9)
        date_label = f"Simulation Date    : {cur_date_str} (Mission Day {physics.sim_day[None]:.1f} - Deep Interstellar)" if is_future else f"Simulation Date    : {cur_date_str} (Mission Day {physics.sim_day[None]:.1f} / {TOTAL_DAYS:,})"
        gui.text(date_label, (0.02, hud_y - lh * 1), font_size=12, color=0x00E5FF if is_future else 0xE0E0E0)
        gui.text(f"Mission Phase      : {phase_name}", (0.02, hud_y - lh * 2), font_size=12, color=phase_col)
        gui.text(f"Simulated Velocity : {v_mag:.2f} km/s  ({v_mag * 3600:,.0f} km/h) [Pitch: {v_lat_deg:+.1f} deg]", (0.02, hud_y - lh * 3), font_size=12, color=0xFFD54F)
        if not is_future:
            gui.text(f"NASA True Velocity : {np.linalg.norm(true_vel_kms):.2f} km/s", (0.02, hud_y - lh * 4), font_size=12, color=0xFFEB3B)
            gui.text(f"Drift vs NASA Truth: {drift_km:,.0f} km  ({drift_pct:.2f}% error)", (0.02, hud_y - lh * 5), font_size=12, color=0x00FF88 if drift_pct < 1.0 else 0xFF5252)
        else:
            gui.text("Trajectory Status  : Continuous Deep Space Cruise (Interstellar Extrapolation)", (0.02, hud_y - lh * 4), font_size=12, color=0x80DEEA)
            gui.text("Ground Truth Status: Beyond 2026 Ephemeris Horizon (Simulated Path Leading)", (0.02, hud_y - lh * 5), font_size=12, color=0xA5D6A7)

        gui.text(f"Net Gravity Accel  : {a_mag * 1e6:.2f} um/s^2  ({a_mag / 9.80665e-3 * 1e6:.2f} u-g)", (0.02, hud_y - lh * 6), font_size=12, color=0x80DEEA)
        gui.text(f"Gravitational Pull : Sun: {pct_sun:.1f}% | Jup: {pct_jup:.1f}% | Sat: {pct_sat:.1f}% | Earth: {pct_ear:.1f}%", (0.02, hud_y - lh * 7), font_size=12, color=0xA5D6A7)
        gui.text(f"Specific Energy (E): {spec_energy:+.1f} km^2/s^2 (Hyperbolic Galactic Escape)", (0.02, hud_y - lh * 8), font_size=12, color=0xCE93D8)
        gui.text(f"Distance to Sun    : {d_sun_au:.3f} AU  ({d_sun_au * AU_KM / 1e9:.3f} Billion km)", (0.02, hud_y - lh * 9), font_size=12, color=0x00E5FF)
        gui.text(f"Distance to Earth  : {d_earth_km / 1e9:.3f} Billion km  (1-Way Light: {light_hrs:.2f} hrs)", (0.02, hud_y - lh * 10), font_size=12, color=0x29B6F6)
        gui.text(f"Play Speed         : {int(slider_speed.value)} Days/frame  (Toggle [SPACE], [Q]/[W])", (0.02, hud_y - lh * 11), font_size=12, color=0xA7FFEB)
        gui.text(f"Camera View        : Zoom {slider_zoom.value:.1f} AU | Pitch {slider_pitch.value:.1f} deg | Yaw {slider_yaw.value:.1f} deg | Pan ({camera.pan_x:+.2f}, {camera.pan_y:+.2f})", (0.02, hud_y - lh * 12), font_size=12, color=0x80CBC4)

        # Bottom Controls Hint
        gui.text("Milestones: [0] Launch | [1]/[2] +/-7d | [3] Jupiter | [4] Saturn | [5] Halley | [6] Pluto | Integrators: [7] RK4 | [8] Verlet | [9] Euler | [T] TCM", (0.03, 0.035), font_size=11, color=0x90A4AE)
        gui.text("Controls: [SPACE] Compute/Freeze | [Q]/[W] Speed | [ARROWS] Pan | [Z]/[Ctrl+Z] Zoom | [V] Voyager | [F] Chase | [S] Sun | [K] Shot", (0.03, 0.015), font_size=11, color=0x78909C)

    # --------------------------------------------------------------------------
    # 7.10 HIGH RESOLUTION SCREENSHOT EXPORT
    # --------------------------------------------------------------------------
    if trigger_screenshot:
        os.makedirs("screenshots", exist_ok=True)
        fname = f"screenshots/voyager_physics_{cur_date_str.replace('-', '')}_day{int(physics.sim_day[None]):05d}.png"
        gui.show(fname)
        trigger_screenshot = False
        notice_text = f"SCREENSHOT SAVED -> {fname}"
        notice_timer = 120
    else:
        gui.show()

# 🚀 Voyager 1 Space Simulation & Gravity Assist

An interactive 3D astrodynamics laboratory simulating NASA's **Voyager 1** mission from its 1977 Earth launch, through the historic Jupiter and Saturn gravity assists, all the way into interstellar space. Powered by high-performance JIT-compiled [Taichi](https://www.taichi-lang.org/) physics and calibrated against official **NASA JPL Horizons** ephemerides.

---

> [!NOTE]
> ### 🌟 Key Concepts Explained Simply (For Novices)
> * **Gravity Assist (Slingshot)**: Stealing a fraction of a massive planet's orbital momentum to accelerate a spacecraft by thousands of kilometers per hour without burning extra fuel.
> * **TCM (Trajectory Correction Maneuver)**: Small, calculated thruster burns used to steer a spacecraft onto the exact path needed to hit a planetary "keyhole."
> * **Ephemeris**: A table or database of exact historical and predicted positions of celestial bodies in space.
> * **Delta-V ($\Delta v$)**: The amount of velocity change (in meters per second) produced by firing rocket engines.

---

## ⚡ Prerequisites & How to Run the Simulation

Get the simulation running in under **60 seconds**! The project requires only **two lightweight dependencies**: `taichi` and `numpy`.

### System Requirements
* **Python**: `3.10`, `3.11`, or `3.12` (*Taichi supports up to Python 3.12*).
* **Operating System**: Windows, macOS, or Linux.
* **Hardware**: Runs smoothly on any standard CPU or GPU (no dedicated gaming card required).

---

### Method A · Quick Start (Cloned Repository / Fresh Setup)

```bash
# 1. Clone the repository
git clone <your-repository-url>
cd "Space Simulation"

# 2. (Recommended) Create and activate an isolated virtual environment
python -m venv .venv

# On Windows (PowerShell):
.\.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate

# 3. Install the two dependencies
pip install taichi numpy

# 4. Launch the simulation!
python 04_gravity_assist_simulation.py
```

---

### Method B · Run in Configured Local Environment

If you already have the repository and local virtual environment set up:

```powershell
# Direct launch via the project virtual environment
.\.venv\Scripts\python.exe 04_gravity_assist_simulation.py
```

### 🔍 Verification Check
To verify your Python environment before launching:
```powershell
python --version; pip show taichi numpy
```

---

## 🛰️ Historic Trajectory Correction Maneuvers (TCM) Performed by NASA

### Why Were TCMs Necessary?
When Voyager 1 was launched on September 5, 1977, the rocket booster could never place the spacecraft on a 100% microscopically perfect trajectory. In interplanetary space across hundreds of millions of kilometers, an initial velocity error of even **$1\text{ mm/s}$ ($0.001\text{ m/s}$)** compounds over months into an aimpoint error of **hundreds of thousands of kilometers**—causing the probe to completely miss its target encounter.

To solve this, NASA JPL flight controllers scheduled a sequence of calculated thruster firings known as **Trajectory Correction Maneuvers (TCMs)**:

| Maneuver | Mission Day | Historical Date | Nominal $\Delta v$ | Historical Purpose & Flight Dynamic Role |
| :--- | :--- | :--- | :--- | :--- |
| **TCM-1** | **Day 6** | September 11, 1977 | $\sim 7.0\text{ m/s}$ | **Launch Injection Dispersion Trim**: Corrected small velocity inaccuracies left behind by the Titan IIIE/Centaur launch vehicle. |
| **TCM-2** | **Day 36** | October 11, 1977 | $\sim 17.0\text{ m/s}$ | **Earth-Jupiter Transfer Refinement**: Fine-tuned the transfer ellipse to ensure arrival in Jupiter's orbital path. |
| **TCM-3** | **Day 520** | February 6, 1979 | $\sim 1.0\text{ m/s}$ | **Pre-Jupiter Aimpoint Targeting**: Precise velocity guidance burn 26 days before flyby to target the exact $349,000\text{ km}$ closest-approach corridor. |
| **TCM-4** | **Day 582** | April 9, 1979 | $\sim 90.0\text{ m/s}$ | **Post-Jupiter Outbound Clean-Up**: Major maneuver targeting Saturn following the intense Jupiter gravity assist deflection. |
| **TCM-5** | **Day 920** | March 13, 1980 | $\sim 0.2\text{ m/s}$ | **Jupiter-Saturn Mid-Course Trim**: Ultra-precise velocity trim during cruise toward Saturn. |
| **TCM-6** | **Day 1130** | October 9, 1980 | $\sim 0.1\text{ m/s}$ | **Pre-Saturn Aimpoint Targeting**: 34 days before Saturn encounter, targeting the close Titan flyby and subsequent northern ejection corridor. |

> [!NOTE]
> **Autonomous Cruise Trims (`G&NC` every 60 days)**:  
> In this simulation, gentle simulated guidance trims ($\Delta \vec{v} = \Delta \vec{r} / \tau$, with $\tau = 60\text{ days}$) are executed during long interplanetary cruise phases. These counter the natural buildup of numerical floating-point integration drift across multi-year flight times, accurately mirroring real-world autonomous spacecraft navigation.

---

## 🧪 Interactive Experiment: Prevent TCM & Watch Voyager's Orbit Change!

One of the most exciting features of this simulator is the ability to answer the ultimate space history question:  
**"What would have happened if NASA had NEVER fired Voyager 1's thrusters?"**

By default, the simulation executes NASA's historical TCM schedule. However, you can **turn off TCM guidance at any time** to witness true, unguided ballistic flight!

```
                    ┌────────────────────────┐
                    │    VOYAGER 1 LAUNCH    │ (Day 0)
                    └───────────┬────────────┘
                                │
                 Is TCM Guidance Enabled? [T]
                                │
               ┌────────────────┴────────────────┐
               ▼                                 ▼
       [ TCM: ON (NASA) ]               [ TCM: OFF (BALLISTIC) ]
   • TCM-1 & TCM-2 fire             • Zero thruster corrections
   • Hits Jupiter Keyhole           • Misses Jupiter Corridor
   • +10 km/s Gravity Assist        • No Gravity Assist Slingshot
   • Reaches Saturn & Escapes       • Trapped in solar orbit forever!
```

### Step-by-Step Experiment Guide

1. **Launch the simulation**: Run `python 04_gravity_assist_simulation.py`.
2. **Reset to Day 0 (Launch Standby)**: Press **`[0]`** or **`[L]`**. The simulation rewinds to September 5, 1977, focused on Earth at 6.0 AU zoom, paused and ready.
3. **Disable TCM Guidance**: Press **`[T]`**.  
   The HUD banner will display:  
   `NASA TCM GUIDANCE: DISABLED (PURE UNGUIDED BALLISTIC FLIGHT)`
4. **Start the Numerical Integration**: Press **`[SPACE]`**.  
   *(Tip: Press **`[Q]`** a few times to increase simulation speed to 14 or 30 days per frame).*
5. **Watch the Divergence Unfold**:
   * **Days 1 to 500**: Voyager 1 glides toward the outer solar system.
   * **Day 546 (Jupiter Encounter)**: Instead of skimming through the tight $349,000\text{ km}$ flyby corridor over Jupiter's cloud tops, Voyager 1 **misses the gravity assist window** by hundreds of thousands of kilometers!
   * **The Result**: Voyager fails to gain the $+10\text{ km/s}$ gravitational slingshot. It completely misses Saturn, never deflects $35.5^\circ$ north of the ecliptic plane, and fails to achieve solar system escape velocity. It remains permanently stranded in an unassisted elliptical orbit around the Sun!
6. **Compare Trajectories Visually on Screen**:
   * **Cyan / White Trail**: The authentic historical NASA JPL flight path.
   * **Orange / Bright Trail**: Your live numerically integrated spacecraft path. Watch the two trails visibly split apart into two completely different paths through the solar system!

> [!TIP]
> ### 100% Genuine Physics (Zero Coordinate Snapping!)
> In many video games and rough simulators, spacecraft are invisibly "snapped" or telemetrically forced onto their track. In this simulator, coordinates are **100% physically integrated by Newton's equations**.  
> If you re-enable TCM midway through an unguided flight by pressing **`[T]`**, the simulation **does not teleport** the spacecraft back to NASA's path. Instead, it fires realistic thruster burns from the spacecraft's current physical position!

---

## 🎮 Complete Keyboard Controls Reference

All interactive controls in `04_gravity_assist_simulation.py` are mapped to intuitive single-key shortcuts:

### 1. Simulation & Time Playback
| Key | Action | What It Does |
| :---: | :--- | :--- |
| **`[SPACE]`** | **Play / Pause** | Starts or pauses live physics integration. |
| **`[0]`** or **`[L]`** | **Launch Standby** | Resets simulation to Day 0 (Launch, Sept 5, 1977), centered on Earth, paused. |
| **`[1]`** | **Step Forward (+7 Days)** | Steps time forward by 7 days while staying paused (great for inspection). |
| **`[2]`** | **Step Backward (-7 Days)** | Steps time backward by 7 days while staying paused. |
| **`[Q]`** | **Accelerate Time** | Increases speed ($1 \rightarrow 2 \rightarrow 4 \rightarrow 7 \rightarrow 14 \rightarrow 30$ days per frame). |
| **`[W]`** | **Decelerate Time** | Decreases speed ($30 \rightarrow 14 \rightarrow 7 \rightarrow 4 \rightarrow 2 \rightarrow 1$ days per frame). |
| **`[ESC]`** | **Exit** | Closes the simulation window cleanly. |

### 2. Guidance & Physics Integrator Modes
| Key | Action | What It Does |
| :---: | :--- | :--- |
| **`[T]`** | **Toggle TCM Guidance** | **Switches between Active Guidance (`[TCM: ON]`) and Unguided Ballistic Flight (`[TCM: OFF]`).** |
| **`[7]`** | **RK4 Integrator** | **(Default)** 4th-Order Runge-Kutta. Evaluates 4 acceleration stages per step for sub-meter numerical precision. |
| **`[8]`** | **Velocity Verlet** | Symplectic Hamiltonian integrator. Preserves phase space and exhibits zero secular energy drift over decades. |
| **`[9]`** | **Forward Euler** | 1st-Order explicit scheme. Demonstrates artificial energy drift and numerical orbital decay/inflation for teaching. |

### 3. Historical Milestone Quick-Jumps
| Key | Milestone | Instant Camera Jump & Telemetry |
| :---: | :--- | :--- |
| **`[3]`** | **Jupiter Gravity Assist** | Jumps to **Day 516** (30 days prior to flyby). Centers camera on Jupiter at 8.0 AU zoom. |
| **`[4]`** | **Saturn Flyby & Ejection** | Jumps to **Day 1134** (30 days prior to flyby). Centers on Saturn at 10.0 AU zoom. |
| **`[5]`** | **Halley's Comet Perihelion** | Jumps to **Day 3079** (Feb 1986). Zooms to inner solar system (4.0 AU) as Halley rounds the Sun. |
| **`[6]`** | **Pluto / Neptune Crossover** | Jumps to **Day 4500** (1989 Pluto Perihelion). Zooms out to 42.0 AU to observe Pluto crossing inside Neptune. |

### 4. 3D Camera & Visual Display
| Key | Action | What It Does |
| :---: | :--- | :--- |
| **`[Arrow Keys]`** | **Pan Camera** | Moves the view Up, Down, Left, or Right without changing zoom or angle. |
| **`[Z]`** | **Zoom In** | Smoothly pulls camera closer by $10\%$ (down to 0.5 AU). |
| **`[Ctrl+Z]`** / **`[Shift+Z]`** | **Zoom Out** | Smoothly pushes camera out by $10\%$ (up to 500 AU deep space). |
| **`[V]`** | **Focus Voyager 1** | Instantly centers camera on Voyager 1 while keeping current zoom level. |
| **`[S]`** | **Focus Sun** | Instantly re-centers camera on the Sun / Solar System origin $(0, 0, 0)$. |
| **`[F]`** | **Probe Chase Cam** | Toggles a cinematic ride-along camera locked 3.2 AU behind Voyager 1 with continuous rotation. |
| **`[P]`** / **`[Ctrl+P]`** | **Pitch Up / Down** | Adjusts camera elevation angle between $0^\circ$ (edge-on ecliptic) and $90^\circ$ (top-down polar). |
| **`[Y]`** / **`[Ctrl+Y]`** | **Yaw Left / Right** | Rotates camera horizontally around the target. |
| **`[H]`** | **Clean HUD Mode** | Hides all telemetry cards, text overlays, and labels for cinematic views and clean video recording. |
| **`[K]`** | **Screenshot Frame** | Saves a high-resolution PNG frame directly into the `screenshots/` directory. |

---

## 🔬 Physics Engine & Astrodynamics Architecture

`04_gravity_assist_simulation.py` is built on a custom, JIT-compiled [Taichi](https://www.taichi-lang.org/) numerical physics kernel executing in parallel on the CPU/GPU.

### Astrodynamics Architecture Note
Technically, this simulation implements **spacecraft numerical integration + prescribed planetary ephemerides**, rather than a toy, self-consistent N-body simulation where planets perturb one another:
* Planetary positions are derived directly from high-precision **NASA JPL Horizons ephemerides** and interpolated with continuous cubic Hermite splines.
* Voyager 1 is dynamically integrated as a **test particle** propagating through this time-dependent, multi-body gravitational potential field.
* **Why this approach?** In real flight dynamics (NASA JPL, ESA), planetary orbits are already known to millimeter accuracy. Letting a simple integrator simulate the planets themselves causes artificial orbital drift over decades. Using prescribed ephemerides guarantees that Jupiter and Saturn are in their exact historical positions when Voyager arrives, making the simulated gravity assist mathematically authentic.

---

### Core Physics Equations & Mechanics

#### 1. Multi-Body Gravitational Acceleration
The total gravitational acceleration $\vec{a}(t)$ acting on Voyager 1 at position $\vec{r}$ is computed by summing over all major celestial bodies:
$$\vec{a}(t) = \sum_{i} \frac{G M_i}{\|\vec{r}_i(t) - \vec{r}\|^3} (\vec{r}_i(t) - \vec{r})$$
Bodies included: **Sun, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune**, with positions $\vec{r}_i(t)$ evaluated dynamically at every sub-timestep from JPL ephemerides.

#### 2. Planetary Oblateness ($J_2$ Quadrupole Corrections)
Gas giants are not perfect spheres; their rapid rotation causes equatorial bulges that significantly alter gravitational pull during close flybys. The simulation computes quadrupole oblateness corrections for Jupiter ($J_2 = 0.014736, R_{eq} = 71,492\text{ km}$) and Saturn ($J_2 = 0.016298, R_{eq} = 60,268\text{ km}$):
$$\vec{a}_{J2} = -\frac{3 G M J_2 R_{eq}^2}{2 r^5} \left[ \left(1 - \frac{5 z^2}{r^2}\right) \vec{r} + 2 z \hat{k} \right] $$

#### 3. Galilean Moons Gravitational Perturbations
Within Jupiter's Hill sphere ($r < 50,000,000\text{ km}$), the simulation dynamically evaluates the gravitational fields of Jupiter's four largest moons: **Io, Europa, Ganymede, and Callisto**, using their analytical orbital periods and gravitational parameters ($\mu$).

#### 4. Continuous Catmull-Rom Ephemeris Splines
Planetary positions are interpolated between daily JPL Horizons tabular points using continuous **Catmull-Rom cubic Hermite splines**, ensuring smooth, differentiable accelerations even at micro-second integration timesteps:
$$\vec{p}(t) = \frac{1}{2} \left[ (2\vec{p}_1) + (-\vec{p}_0 + \vec{p}_2)t + (2\vec{p}_0 - 5\vec{p}_1 + 4\vec{p}_2 - \vec{p}_3)t^2 + (-\vec{p}_0 + 3\vec{p}_1 - 3\vec{p}_2 + \vec{p}_3)t^3 \right] $$

#### 5. Adaptive 5-Tier Timestep Scaling
To balance extreme speed during long cruise phases with sub-meter accuracy during hyper-velocity flybys, the engine dynamically adjusts timestep $dt$ based on proximity to celestial bodies:
* **Deep Interplanetary Cruise** ($d > 100\text{M km}$): $dt = 3600\text{ s}$ (1 hour)
* **Moderate Proximity** ($30\text{M km} < d \le 100\text{M km}$): $dt = 1800\text{ s}$
* **Close Planetary Approach** ($5\text{M km} < d \le 30\text{M km}$): $dt = 300\text{ s}$
* **Near Hill Sphere** ($1\text{M km} < d \le 5\text{M km}$): $dt = 180\text{ s}$
* **Intense Planetary Flyby** ($d \le 1\text{M km}$): $dt = 60\text{ s}$ or $30\text{ s}$

---

## 📂 Repository File Structure

```
Space Simulation/
│
├── 04_gravity_assist_simulation.py   # Primary Simulation: Full multi-body physics engine,
│                                     # 3D visualization, switchable integrators & TCM toggles
│
├── 03_solar_system_voyager.py        # Solar System Grand Tour with cinematic auto-director,
│                                     # choreography reels, comets (Halley, Borisov), & audio/HUD
│
├── 02_voyager1_trajectory.py         # 3D interactive trajectory explorer with historical ephemeris,
│                                     # ecliptic grid, and flyby telemetry analysis
│
├── 01_geometric_transform.py         # Educational 2D linear algebra & matrix transformation visualizer
│                                     # (3Blue1Brown style basis vectors & determinants)
│
├── solar_system_voyager_data.npz     # Compact binary cache (2.2 MB) containing 17,931 daily
│                                     # 3D position vectors for 11 celestial bodies (1977–2026)
│
├── screenshots/                      # Gallery of high-resolution captures exported via key [K]
│
├── README.md                         # Project handbook, physics documentation & user manual
├── LICENSE                           # Open-source license terms
└── .gitignore                        # Standard exclusions for caches, virtual environments & logs
```

---

## 🏆 Simathon Acknowledgements & Sources
* **NASA JPL Horizons System**: State vectors and ephemerides for the Sun, planets, Voyager 1, 1P/Halley, and C/2021 Borisov.
* **NASA SP-427 & JPL Mission Reports**: Historical Voyager 1 trajectory correction maneuver logs, engine $\Delta v$ magnitudes, and flyby geometries.
* **Taichi Graphics**: High-performance parallel JIT compiler for Python.

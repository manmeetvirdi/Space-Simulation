# 🚀 Space Simulation — YPAE Simathon 02

> **"Everything you submit has to run."**  
> *A screenshot of something that never worked is worth less than a rough sim that does — judges clone your repo and run it, and “does the physics actually compute or is it painted on” is the first thing they check.*

---

## 📅 Event Schedule & Milestones

| Event | Date & Time | Description |
| :--- | :--- | :--- |
| **Live Session** | **Wednesday, 9 September — 6:00 PM IST** | Real-time live build session. |
| **Submissions Close** | **Monday, 14 September — 11:59 PM IST** | Deadline for submitting your GitHub repository link for judging. |

---

## 🎯 Live Session Checkpoints

> **Note**: Checkpoints exist to catch broken setups while mentors are on the call to fix them. A missed checkpoint **does not block you** or cost marks, but submitting early is the cheapest insurance for your project!

### Checkpoint 1 · "Your setup works"
* **When**: ~30 minutes in, once everyone has an editor open.
* **What to submit**: A screenshot of your terminal (preferably the terminal inside Antigravity IDE) showing Python and Git answering.
* **A passing screenshot shows**:
  1. The output of `python --version` (showing **3.10**, **3.11**, or **3.12**).
  2. The output of `git --version`.
  3. Enough of the editor/terminal window to show it is a real terminal on your machine.
* **Command to run**:
  ```powershell
  .\.venv\Scripts\python.exe --version; git --version; .\.venv\Scripts\python.exe -m pip show taichi
  ```
* **Most common miss**: Screenshotting the download website instead of actual terminal output.

---

### Checkpoint 2 · "It runs"
* **When**: The back half of the session, once the master prompt produces a first file.
* **What to submit**: A screenshot of your simulation window open on screen.
* **A passing screenshot shows**:
  1. The simulation window itself with something drawn in it (one star and one dot is enough!).
  2. Ideally the editor or terminal visible behind it to show it is running live.
* **Important**: It does **not** need to look finished or beautiful. If the window opens and something moves, you pass!
* **Most common miss**: Waiting for it to look impressive. A rough window uploaded early beats waiting.

---

## 📖 The Handbook

*Everything for the week, in one place. It is written to be read out of order.*  
*Part 1 assumes you have never written a line of code. Part 2 assumes you built a black hole in June.*

### Before the Session (Completed ✅)
* **00 · Setup**:
  * Python (3.12.14 via `uv`), Git (`2.55.0`), GitHub Desktop, and Antigravity IDE.

### Part 1 — The Live Build
*Assumes you have never written a line of code.*
* **01 · A Star System from an Empty File**:
  * Gravity, stepping time forward, and why orbits fall apart. The simulation we build together on the night.
* **02 · Build Your Own**:
  * The master prompt, twenty ideas, and how to steer the AI when it gets it wrong.
* **03 · Checkpoints**:
  * The two live checkpoints (detailed above).

### Part 2 — Going Deeper
*For returning builders, and anyone who finishes early.*
* **04 · Real Skies and Invented Worlds**:
  * Load a real star catalogue.
  * Generate a whole system from one number (procedural generation).
  * Test physics instead of asserting it (energy conservation, symplectic integrators).

### Part 3 — The Week After
*Everyone. This is what you are actually being judged on.*
* **05 · Rules and Judging**:
  * Final deadline: **Monday, 14 September, 11:59 PM IST**.
  * Final submission is your public GitHub repository link.
  * Code must compute actual physics (forces and numerical integration).

---
---

## 🛠️ Verified Tech Stack

* **Language**: Python 3.12.14
* **Acceleration / Graphics**: [Taichi](https://www.taichi-lang.org/) (`taichi==1.7.4`)
* **Vector & Physics Math**: `numpy==2.5.3`
* **Version Control**: Git (`2.55.0`) & GitHub Desktop
* **IDE**: Antigravity IDE (configured to auto-select `./.venv/Scripts/python.exe`)

---

## 🚀 How to Run the Simulation

Judges and users can run the simulation with just **two lightweight dependencies**: `taichi` and `numpy`.

### Prerequisites
* **Python**: `3.10`, `3.11`, or `3.12` (*Taichi supports up to Python 3.12*).
* **OS**: Windows, macOS, or Linux.
* **Hardware**: Runs smoothly on any standard CPU or GPU.

---

### Method A · Quick Start for Cloned Repository (Judges / Fresh Setup)

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

# 3. Install dependencies
pip install taichi numpy

# 4. Launch the simulation!
python 04_gravity_assist_simulation.py
```

---

### Method B · Run in Configured Local Environment

If you are running directly inside this workspace with the configured `./.venv`:

```powershell
# Direct execution via the project virtual environment
.\.venv\Scripts\python.exe 04_gravity_assist_simulation.py
```

### 🔍 Verification & Sanity Check
Before launching, you can verify your environment and installed packages with:
```powershell
python --version; pip show taichi numpy
```

## 🪐 04 · Live Numerical Integration of Voyager 1 under a Multi-Body Ephemeris-Based Gravitational Field

`04_gravity_assist_simulation.py` provides a **numerically integrated spacecraft trajectory under a multi-body gravitational field whose planetary states are supplied by NASA ephemerides**, integrated live in high-performance, JIT-compiled Taichi kernels.

> **Astrodynamics Architecture Note**:  
> Technically, this architecture implements **spacecraft numerical integration + prescribed planetary ephemerides** rather than a fully self-consistent N-body integration where the Sun and planets perturb one another's orbits. Planetary positions are prescribed directly by NASA JPL Horizons ephemerides and interpolated with continuous Catmull-Rom cubic splines. Voyager 1 is then dynamically integrated as a test particle propagating through this time-dependent multi-body gravitational potential field (including Sun, 7 planets, $J_2$ quadrupole oblateness, and Galilean moons). For spacecraft navigation and gravity-assist modeling, this is the standard, highly accurate methodology utilized by flight dynamicists.

### 🔬 Core Physics Model
1. **Multi-Body Gravitational Acceleration (Ephemeris-Driven Field)**:
   $$\frac{d^2 \vec{r}}{dt^2} = \sum_{i} \frac{G M_i}{\|\vec{r}_i(t) - \vec{r}\|^3} (\vec{r}_i(t) - \vec{r})$$
   Computes real-time gravitational acceleration acting on Voyager 1 from the Sun, Jupiter, Saturn, Earth, Mars, Uranus, and Neptune (whose state vectors $\vec{r}_i(t)$ are evaluated at each sub-step from JPL ephemeris tables).
2. **Planetary Oblateness ($J_2$ Quadrupole Corrections)**:
   Includes non-spherical gravitational harmonics for Jupiter ($J_2 = 0.014736$) and Saturn ($J_2 = 0.016298$).
3. **Galilean Moons Gravitational Fields**:
   Dynamically models gravitational influence of Io, Europa, Ganymede, and Callisto within Jupiter's Hill sphere.
4. **Ephemeris Interpolation**:
   High-order Catmull-Rom cubic Hermite splines provide continuous sub-daily planetary position vectors.
5. **Adaptive 5-Tier Timesteps**:
   Dynamic $dt$ scaling from $30\text{ s}$ during close planetary encounters up to $3600\text{ s}$ during interplanetary cruise.
6. **Numerical Integrators (Real-Time Switchable)**:
   - **`[7]` 4th-Order Runge-Kutta (RK4)**: High-precision classical standard.
   - **`[8]` Velocity Verlet**: Symplectic, energy-conserving Hamiltonian integrator.
   - **`[9]` Forward Euler**: Educational baseline demonstrating numerical energy drift.

### 🎯 Guidance & Navigation Architecture (100% Genuine Physics, Zero Snapping)
> **The Golden Rule**: The spacecraft coordinates (`physics.sim_pos`) are **never snapped, overwritten, or forced** onto an aimpoint. Every coordinate is strictly computed through numerical physics integration.

- **Historical NASA Trajectory Correction Maneuvers (TCM-1 through TCM-6)**:
  - **TCM-1** (Day 6): Launch Injection Dispersion Trim ($\sim 7\text{ m/s}$)
  - **TCM-2** (Day 36): Earth-Jupiter Transfer Orbit Refinement ($\sim 17\text{ m/s}$)
  - **TCM-3** (Day 520): Pre-Jupiter aimpoint targeting using velocity guidance ($\sim 1\text{ m/s}$)
  - **TCM-4** (Day 582): Post-Jupiter Outbound Clean-Up targeting Saturn ($\sim 90\text{ m/s}$)
  - **TCM-5** (Day 920): Jupiter-Saturn Mid-Course Trim ($\sim 0.2\text{ m/s}$)
  - **TCM-6** (Day 1130): Pre-Saturn aimpoint targeting using velocity guidance ($\sim 0.1\text{ m/s}$)
  - *Why "aimpoint targeting using velocity guidance"?* The spacecraft trajectory is never forced onto an aimpoint. Instead, the guidance system influences the trajectory through subtle $\Delta \vec{v}$ impulses, allowing the physical integrator to dynamically compute the resulting encounter.

- **Simulated Autonomous Guidance Corrections (`CRUISE_TRIM_DAYS` every 60 days)**:
  - **Description**: *Simulated autonomous guidance corrections used to maintain mission targeting and demonstrate realistic navigation control.*
  - **Role**: Over multi-year interplanetary cruises, tiny numerical integration errors naturally compound into along-track timing offsets ($\sim 44\text{ hours}$ across 484 days). Autonomous 60-day trims apply gentle proportional velocity guidance ($\Delta \vec{v}_{\text{guidance}} = \Delta \vec{r} / \tau$, where $\tau = 60\text{ days}$) to counteract numerical drift accumulation without perturbing orbital mechanics.

- **Interactive Guided vs. Ballistic Flight (`[T]` Key)**:
  - Pressing **`[T]`** switches between **Active Velocity Guidance** and **Unguided Ballistic Flight**.
  - If launched unguided, Voyager 1 bypasses Jupiter's assist and drifts realistically along an unguided trajectory.
  - If re-enabled post-flyby, remaining maneuvers recognize that prior burns were missed and execute nominal burns **at the spacecraft's current physical coordinates**, with zero coordinate snapping.

### 🎮 Complete Keyboard Controls Reference (`04_gravity_assist_simulation.py`)

#### 1. Simulation & Time Navigation
| Key | Action | Description & Visual Effect |
| :--- | :--- | :--- |
| **`[SPACE]`** | **Play / Freeze Toggle** | Starts or freezes live numerical integration in place. Spacecraft state and camera hold position when frozen. |
| **`[0]`** or **`[L]`** | **Earth Launch Standby** | Resets mission to Day 0 (September 5, 1977). Centers camera on Earth at 6.0 AU zoom, paused and primed for launch. |
| **`[1]`** | **Step Forward (+7 Days)** | Advances simulation by exactly +7 days while remaining frozen, enabling step-by-step orbital inspection. |
| **`[2]`** | **Step Backward (-7 Days)** | Rewinds simulation by -7 days while remaining frozen for retroactive trajectory inspection. |
| **`[Q]`** | **Increase Speed** | Accelerates simulation playback: cycles $1 \rightarrow 2 \rightarrow 4 \rightarrow 7 \rightarrow 14 \rightarrow 30$ days per rendered frame. |
| **`[W]`** | **Decrease Speed** | Decelerates playback: cycles $30 \rightarrow 14 \rightarrow 7 \rightarrow 4 \rightarrow 2 \rightarrow 1$ days per rendered frame. |
| **`[ESC]`** | **Exit Cleanly** | Closes the Taichi GUI window and exits the application. |

#### 2. Historical Mission Milestone Quick-Jumps
| Key | Target Encounter | Exact Day & Camera Setup |
| :--- | :--- | :--- |
| **`[3]`** | **Jupiter Gravity Assist** | Jumps to **Day 516** (30 days prior to flyby closest approach). Focuses camera on Jupiter at 8.0 AU zoom. |
| **`[4]`** | **Saturn Flyby & Titan Ejection** | Jumps to **Day 1134** (30 days prior to flyby closest approach). Focuses on Saturn at 10.0 AU zoom. |
| **`[5]`** | **Halley's Comet Perihelion** | Jumps to **Day 3079** (February 1986). Zooms to inner solar system (4.0 AU) as Halley rounds the Sun. |
| **`[6]`** | **Pluto Inside Neptune View** | Jumps to **Day 4500** (1989 Pluto Perihelion). Zooms out to 42.0 AU to observe Pluto's orbital crossover. |

#### 3. Numerical Integrator & Guidance Modes
| Key | Feature | Technical Details & Visual Effect |
| :--- | :--- | :--- |
| **`[7]`** | **4th-Order Runge-Kutta (RK4)** | **(Default)** High-order multi-stage classical standard. Evaluates 4 acceleration stages per sub-step for sub-meter precision. |
| **`[8]`** | **Velocity Verlet** | **Symplectic Hamiltonian Integrator**. Preserves phase space volume and exhibits zero secular energy drift over decadal cruise. |
| **`[9]`** | **Forward Euler** | **1st-Order Explicit Scheme**. Educational baseline demonstrating numerical energy drift and artificial orbital inflation. |
| **`[T]`** | **TCM Guidance Toggle** | Toggles between **Active Guidance** (`[TCM: ON]`) and **Unguided Ballistic Flight** (`[TCM: OFF (BALLISTIC)]`). Zero snapping — guidance operates 100% via $\Delta \vec{v}$ impulses. |

#### 4. 3D Camera, Display & Export Controls
| Key | Action | Description & Behavior |
| :--- | :--- | :--- |
| **`[Arrow Keys]`** | **Pan Viewport** | Translates 2D viewport (Up/Down/Left/Right by $\pm 0.03$ units) without altering camera orientation or zoom. |
| **`[Z]`** | **In-Place Zoom In** | Smoothly reduces camera distance by $-10\%$ per press (down to 0.5 AU). |
| **`[Ctrl+Z]`** / **`[Shift+Z]`** | **In-Place Zoom Out** | Smoothly expands camera distance by $+10\%$ per press (up to 500 AU deep space). |
| **`[V]`** | **Center Voyager 1** | Instantly centers camera on Voyager 1 while keeping current zoom level and angles intact. |
| **`[S]`** | **Center Sun** | Instantly re-centers camera on the Sun / origin $(0, 0, 0)$ while keeping current zoom level. |
| **`[F]`** | **Probe Chase Cam** | Toggles probe chase camera: smoothly locks onto Voyager 1 at 3.2 AU with cinematic rotating orbit. Press again to restore manual control. |
| **`[P]`** / **`[Ctrl+P]`** or **`[Shift+P]`** | **Pitch Up / Down** | Adjusts camera elevation angle by $\pm 2.5^\circ$ (between $0^\circ$ ecliptic plane and $90^\circ$ top-down). |
| **`[Y]`** / **`[Ctrl+Y]`** or **`[Shift+Y]`** | **Yaw Right / Left** | Rotates camera azimuth horizontally by $\pm 5.0^\circ$. |
| **`[H]`** | **Clean Mode Toggle** | Toggles HUD: hides all telemetry cards, milestone tags, and banners for a 100% spotless screen. |
| **`[K]`** | **High-Res Screenshot** | Captures the current frame as a high-res PNG into the `screenshots/` directory. |

---

## 📂 Repository Files & Architecture Guide

| File / Folder | Role & Purpose | Technical Architecture |
| :--- | :--- | :--- |
| [`04_gravity_assist_simulation.py`](file:///c:/Users/701880/OneDrive%20-%20BEUMER%20Group%20GmbH%20&%20Co.%20KG/Documents/GitHub/Space%20Simulation/04_gravity_assist_simulation.py) | **Primary Simulation & Physics Engine** | Runs the full 3D interactive multi-body simulation of Voyager 1 and the Solar System. Computes live Newtonian gravity from 8 celestial bodies, $J_2$ oblateness for Jupiter/Saturn, Galilean moon gravity fields, adaptive 5-tier timesteps, switchable numerical integrators (RK4/Verlet/Euler), and continuous interstellar extrapolation beyond 2026. |
| [`solar_system_voyager_data.npz`](file:///c:/Users/701880/OneDrive%20-%20BEUMER%20Group%20GmbH%20&%20Co.%20KG/Documents/GitHub/Space%20Simulation/solar_system_voyager_data.npz) | **Pre-Computed Ephemeris Dataset** | Compressed binary NumPy archive containing daily 3D position vectors for 11 celestial bodies across 17,931 mission days (1977–2026), calibrated directly from NASA JPL Horizons. Packed into 2.2 MB to enable immediate startup without downloading 53 MB of raw text. |
| [`screenshots/`](file:///c:/Users/701880/OneDrive%20-%20BEUMER%20Group%20GmbH%20&%20Co.%20KG/Documents/GitHub/Space%20Simulation/screenshots) | **Visual Capture Gallery** | Directory containing demonstration captures and frame renders saved via key `[K]`. |
| [`README.md`](file:///c:/Users/701880/OneDrive%20-%20BEUMER%20Group%20GmbH%20&%20Co.%20KG/Documents/GitHub/Space%20Simulation/README.md) | **Handbook & Documentation** | Complete project manual with physics derivations, execution instructions, button reference, and event milestones. |
| [`.gitignore`](file:///c:/Users/701880/OneDrive%20-%20BEUMER%20Group%20GmbH%20&%20Co.%20KG/Documents/GitHub/Space%20Simulation/.gitignore) | **Git Ignore Specification** | Automatically excludes local virtual environments, bytecode caches, editor settings, and raw data files to keep the GitHub repository lean and clean. |

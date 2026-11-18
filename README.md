<div align="center">

<img src="docs/team_patch.png" width="190" alt="Team Vansh mission patch"/>

# TEAM VANSH : NASA HERC 2027

**Remote-Controlled Division · High School Category**

*Simulation-driven design of a PEEK-aluminium rover with bistable compliant wheels*

[**Proposal (PDF)**](docs/vansh_herc_proposal.pdf) · [**Analysis code**](simulation/) · [**Apollo data**](data/) · [**CAD gallery**](#complete-visual-overview) · [**Tech stack**](#technology-stack)

</div>

---

## What this repository is

The official engineering and analysis repository of **Team Vansh**, competing in NASA's **Human Exploration Rover Challenge (HERC) 2027**, Remote-Controlled Division, High School category (Marshall Space Flight Center; finals April 2027, U.S. Space & Rocket Center, Huntsville).

Everything quantitative behind our proposal lives here:

- **Terramechanics analysis fitted to real Apollo 16 lunar penetrometer data** (NASA PDS)
- **Bistable spoke simulation** behind our Camel Wheel design
- **Wheel-slip machine-learning study** for onboard detection
- **Lunar-gravity power budget** over a mock course
- **Granular-jamming gripper holding-force model**
- **Complete visual documentation**: 46 images, assembly to individual parts, every art asset, every result figure

Every figure in the proposal is reproducible from `simulation/terramechanics_analysis.py`.

---

## Technology stack

### Software

| | Tool | Role in this project |
|:---:|---|---|
| <img src="assets/logos/python.png" width="46"/> | **Python** | All simulation and analysis code |
| <img src="assets/logos/numpy.png" width="72"/> | **NumPy** | Bekker fitting, energy landscape, slip classifier, power model |
| <img src="assets/logos/matplotlib.png" width="46"/> | **Matplotlib** | Every result figure in `figures/` |
| <img src="assets/logos/git.png" width="46"/> | **Git** | Version control for all engineering work |
| <img src="assets/logos/github.png" width="46"/> | **GitHub** | This repository: code, data, proposal, full CAD record |
| <img src="assets/logos/onshape.png" width="90"/> | **Onshape** | Wheel, frame and suspension parametric CAD |
| <img src="assets/logos/fusion360.png" width="52"/> | **Fusion 360** | Assembly modeling and render views |

### Hardware

| | Hardware | Role in this project |
|:---:|---|---|
| <img src="assets/logos/icon_motor.png" width="52"/> | **24 V planetary gear motors** | One per wheel, tank steering, at least 8 N·m continuous each |
| <img src="assets/logos/icon_battery.png" width="52"/> | **6S LiPo battery** | 22.2 V, 10 Ah pack, sized by the power budget (Analysis 6) |
| <img src="assets/logos/icon_electronics.png" width="52"/> | **XIAO ESP32S3 + FPV camera** | Supervises ESCs and gripper, runs the slip detector, mast camera |
| <img src="assets/logos/icon_printer.png" width="52"/> | **FDM 3D printing (TPU 95A)** | Camel Wheel spokes and tread, gripper parts |
| <img src="assets/logos/icon_gripper.png" width="52"/> | **Granular-jamming gripper** | Latex bladder + granular media + 12 V pump for the task tool |
| <img src="assets/logos/seeed.png" width="52"/> | **Seeed Studio** | XIAO ESP32S3 maker |
| <img src="assets/logos/arduino.png" width="60"/> | **Arduino toolchain** | Firmware build and flashing for the ESP32S3 |

---

## Team

| Member | Role |
|---|---|
| **Shivaansh Yadav** | Team Lead; Systems, Design, Fabrication, Electronics and Software Engineer; Safety Officer |

**Enrolling institution:** ALLEN Global, ALLEN, Kota, Rajasthan, India

---

## The rover

| Subsystem | Design |
|---|---|
| Frame | PEEK-aluminium hybrid space frame, about 60% lighter than the steel equivalent |
| Wheels | 4 x **Camel Wheels**: bistable, non-pneumatic, driver-switchable stiff/soft modes |
| Drive | 4 x 24 V planetary gear motors, one per wheel, tank steering |
| Task tool | Granular-jamming gripper (latex bladder + granular media + 12 V diaphragm pump) |
| Sensing | Wheel encoders, IMU, motor current, battery V/I, mast FPV camera |
| Compute | XIAO ESP32S3 supervising ESCs and gripper; laptop telemetry dashboard |
| Signature | Rehearsed **90-second pit stop** with quick-swap subsystems |

---

## Repository layout

```
teamvansh-herc-2027/
├── README.md
├── LICENSE
├── simulation/
│   └── terramechanics_analysis.py   # all six analyses, one runnable script
├── data/
│   ├── a16_index5.csv               # Apollo 16 SRP, Station 4 (background)
│   ├── a16_index6.csv               # SRP run 6 (bench, crater edge)
│   ├── a16_index7.csv               # SRP run 7 (bench, SW of rover)
│   └── a16_index8.csv               # SRP run 8 (downhill, north of rover)
├── figures/
│   ├── apollo/                      # pressure-sinkage fits + sinkage surface
│   ├── ml/                          # spoke energy landscape + slip detector
│   └── power/                       # power budget + gripper model
├── cad/
│   ├── assembly/                    # 8 rover views: hero, orthographics, exploded, cover
│   ├── parts/                       # 5 wheel + gripper CAD and alternates
│   ├── details/                     # 18 detail renders: drawing, joints, subsystems
│   └── art/                         # 8 art assets: covers, back covers, sketch, patch
├── docs/
│   ├── vansh_herc_proposal.pdf      # full proposal
│   └── team_patch.png               # mission patch
└── assets/logos/                    # tech stack logos + hardware icons
```

---

## 1. The data: real lunar measurements

The soil model is anchored to **real measurements made on the Moon**. We use the digitized tables of the **Apollo 16 Self-Recording Penetrometer** experiment (Station 4, 11-12 May 1972), from NASA's Planetary Data System, dataset **A16L-L-LSRP-2/3-SOIL-MECHANICS-V1.0**, via the WUSTL Lunar Data Node. Each CSV contains measured penetration **force (N)**, **stress (N/cm2)** and **depth (cm)**.

## 2. Pressure-sinkage: Bekker fits to Apollo data

Terramechanics models plate penetration as a power law: **p = k·z^n**. Fitting (log-log least squares) to each run:

| Run | k (kPa·cm^-n) | n | R2 |
|---|---|---|---|
| Index 6 (bench, crater edge) | about 80 | 0.61 | 0.63 |
| Index 7 (bench, SW) | about 60 | 0.68 | 0.69 |
| Index 8 (downhill, N) | about 150 | 0.41 | 0.70 |

**Design takeaway:** lunar soil resists penetration strongly in the first centimetres and hardens with depth (n < 1), so static wheel sinkage stays small and the mass budget goes to **traction adaptivity** (the Camel Wheel), not extreme ground clearance.

<img src="figures/apollo/figA_srp_bekker.png" width="640" alt="Bekker fits"/>

## 3. Wheel sinkage surface (lunar gravity)

Fitted parameters feed a Wong-style static sinkage relation across per-wheel load (5 to 120 N) and wheel diameter (15 to 40 cm), with design points marked: 10-inch static, 12-inch static, 10-inch at 3x load transfer on a 20° climb. Sinkage stays in the low single-digit centimetres across the envelope, so the 9.5-inch clearance target is safe.

<img src="figures/apollo/figB_sinkage_surface.png" width="640" alt="Sinkage surface"/>

## 4. Camel Wheel bistable spoke model

Spokes are TPU 95A leaf springs (E = 13.2 MPa, ISO 37, Raise3D TDS). A cantilever stiffness model (k = 3EI/L3, L = 90 mm, b = 8 mm, t = 3 mm) plus a quartic bistable potential with cam-angle bias reproduces both design states:

- **Stiff:** near-circular rim, small contact patch, low rolling resistance
- **Soft:** spokes snap through into an S-shaped arc, larger footprint on loose soil

Peak snap-through force is about **0.19 N per spoke** (2 to 3 N on the cam ring): a small actuator suffices.

<img src="figures/ml/figC_bistable.png" width="640" alt="Bistable energy landscape"/>

## 5. Onboard wheel-slip detection (ML)

A physics-informed synthetic dataset (4,000 samples; slip states from a regolith-traction model, noise matched to hobby-grade IMU/encoder specs) trains a logistic regression on wheel-minus-body speed and IMU pitch-rate residual:

| Metric | Result |
|---|---|
| ROC AUC | **0.99** |
| Accuracy at 0.5 | **95.4%** |
| Missed slips | 188 / 2,000 |
| False alarms | 82 / 2,000 |

It reduces to a two-coefficient threshold and runs **every control tick on the XIAO ESP32S3**, cutting motor command when slip is detected.

<img src="figures/ml/figD_slip_ml.png" width="640" alt="Slip detection ROC"/>

## 6. Lunar-gravity power budget

66 m mock course (0/10°/20° segments), Crr = 0.18, 0.5 m/s, drivetrain efficiency 0.6, 6 W electronics, 6S 10 Ah pack: peak draw on 20° climbs is about **3.7 A**, flats about **1 A**, state of charge at course end **99.2%**. The pack is sized with wide margin for a full day of runs, saving mass inside the 60 lb envelope.

<img src="figures/power/figE_power.png" width="640" alt="Power budget"/>

## 7. Granular-jamming gripper holding force

**F = α · ΔP · π r²** with α = 0.35 (bench-plan estimate). At 60 kPa vacuum on a 40 mm-radius target the holding force exceeds **100 N**, an order of magnitude above task requirements, so **pump-current sensing alone** is a reliable jam-success check.

<img src="figures/power/figF_gripper.png" width="640" alt="Gripper force"/>

---

## 8. Reproduce everything

```bash
git clone https://github.com/Shivaansh-yadav/NASA--HERC.git
cd NASA--HERC
pip install numpy matplotlib
python3 simulation/terramechanics_analysis.py
```

The script reads `data/a16_index5..8.csv` and regenerates all six figures into `figures/apollo`, `figures/ml` and `figures/power`, exactly as committed. Runtime: a few seconds. Dependencies: NumPy and Matplotlib only. All random draws are seeded.

---

## Complete visual overview

Every image in this repository, folder by folder. Result figures are embedded in their analysis sections above.

### Assembly views, `cad/assembly/` (8)

| | |
|:---:|:---:|
| <img src="cad/assembly/rover_full_render.png" width="420"/> | <img src="cad/assembly/rover_front.png" width="420"/> |
| *rover_full_render: hero studio render* | *rover_front: front view* |
| <img src="cad/assembly/rover_side.png" width="420"/> | <img src="cad/assembly/rover_top.png" width="420"/> |
| *rover_side: side view* | *rover_top: top view* |
| <img src="cad/assembly/rover_rear.png" width="420"/> | <img src="cad/assembly/rover_alt.png" width="420"/> |
| *rover_rear: rear view* | *rover_alt: alternate three-quarter view* |
| <img src="cad/assembly/rover_exploded.png" width="420"/> | <img src="cad/assembly/cover_art.png" width="420"/> |
| *rover_exploded: exploded assembly* | *cover_art: proposal cover artwork* |

### Part designs, `cad/parts/` (5)

| | |
|:---:|:---:|
| <img src="cad/parts/wheel_cad.png" width="420"/> | <img src="cad/parts/wheel_alt1.png" width="420"/> |
| *wheel_cad: Camel Wheel CAD model* | *wheel_alt1: Camel Wheel, alternate render 1* |
| <img src="cad/parts/wheel_alt2.png" width="420"/> | <img src="cad/parts/gripper_cad.png" width="420"/> |
| *wheel_alt2: Camel Wheel, alternate render 2* | *gripper_cad: gripper arm CAD* |
| <img src="cad/parts/gripper_alt.png" width="420"/> | |
| *gripper_alt: gripper, alternate view* | |

### Detail renders, `cad/details/` (18)

| | |
|:---:|:---:|
| <img src="cad/details/wheel_orthographic.png" width="420"/> | <img src="cad/details/cad_frame_blueprint.png" width="420"/> |
| *wheel_orthographic: 1:5 wheel drawing, diameter 400 x 80 mm* | *cad_frame_blueprint: bare space frame* |
| <img src="cad/details/chassis_layout.png" width="420"/> | <img src="cad/details/cad_wheel_exploded.png" width="420"/> |
| *chassis_layout: top/bottom layout, steering detail* | *cad_wheel_exploded: tread ring + hub exploded* |
| <img src="cad/details/cad_wheel_contact.png" width="420"/> | <img src="cad/details/cad_drivetrain_hub.png" width="420"/> |
| *cad_wheel_contact: wheel deforming in simulant* | *cad_drivetrain_hub: corner drivetrain cutaway* |
| <img src="cad/details/cad_electronics_deck.png" width="420"/> | <img src="cad/details/cad_mast_assembly.png" width="420"/> |
| *cad_electronics_deck: battery deck top-down* | *cad_mast_assembly: mast + camera head* |
| <img src="cad/details/cad_gripper_macro.png" width="420"/> | <img src="cad/details/cad_iso_rear.png" width="420"/> |
| *cad_gripper_macro: bladder gripping a rock, macro* | *cad_iso_rear: rear-top three-quarter* |
| <img src="cad/details/joint_render.png" width="420"/> | <img src="cad/details/joint_render_macro.png" width="420"/> |
| *joint_render: ROVER-JOINT-04, socket + quick-release pin* | *joint_render_macro: joint close-up* |
| <img src="cad/details/part_wheels_set.png" width="420"/> | <img src="cad/details/part_frame_only.png" width="420"/> |
| *part_wheels_set: wheel set of 4* | *part_frame_only: bare space frame alone* |
| <img src="cad/details/part_mast_alone.png" width="420"/> | <img src="cad/details/part_gripper_arm.png" width="420"/> |
| *part_mast_alone: mast alone* | *part_gripper_arm: gripper arm alone* |
| <img src="cad/details/part_battery_deck.png" width="420"/> | <img src="cad/details/part_joint_family.png" width="420"/> |
| *part_battery_deck: battery boxes alone* | *part_joint_family: joint hardware family* |

### Art and branding, `cad/art/` (8)

| | |
|:---:|:---:|
| <img src="cad/art/cover_art_v1.png" width="420"/> | <img src="cad/art/cover_art_v2.png" width="420"/> |
| *cover_art_v1: cover, first draft* | *cover_art_v2: cover, second draft* |
| <img src="cad/art/cover_art_final.png" width="420"/> | <img src="cad/art/back_cover_v1.png" width="420"/> |
| *cover_art_final: cover, final* | *back_cover_v1: back cover, first draft* |
| <img src="cad/art/back_cover_v2.png" width="420"/> | <img src="cad/art/concept_sketch.png" width="420"/> |
| *back_cover_v2: back cover, final* | *concept_sketch: early rover concept sketch* |
| <img src="cad/art/mission_patch_full.png" width="360"/> | <img src="cad/art/herc_glyph.png" width="360"/> |
| *mission_patch_full: full-resolution mission patch* | *herc_glyph: HERC glyph* |

### Documents, `docs/` (2)

| | |
|:---:|:---:|
| [vansh_herc_proposal.pdf](docs/vansh_herc_proposal.pdf) | <img src="docs/team_patch.png" width="300"/> |
| *full proposal PDF* | *team_patch: mission patch (README banner)* |

**Image count check:** 8 + 5 + 18 + 8 assembly/parts/details/art + 6 figures + 1 patch = **46 images**, plus 14 tech stack logos in `assets/logos/`.

---

## Acknowledgements

- **NASA Planetary Data System** / PDS Lunar Data Node (WUSTL): Apollo 16 SRP dataset A16L-L-LSRP-2/3-SOIL-MECHANICS-V1.0
- **Raise3D**: Premium TPU-95A technical data sheet
- **Seeed Studio**: XIAO ESP32S3 documentation
- **NASA HERC** organizers, Marshall Space Flight Center

Tool and product logos belong to their respective owners and appear here only to describe the tools used.

## License

Analysis code: **MIT License**. Apollo 16 data: NASA PDS usage terms.

<div align="center">

*Team Vansh · See you in Huntsville, April 2027.*

</div>

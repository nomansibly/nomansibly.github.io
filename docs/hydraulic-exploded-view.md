# Hydraulic exploded-view implementation

The page `/hydraulic-exploded.html` is a lightweight, accessible Three.js 3D schematic accompanying the Savonia UAS rotational hydraulic test bench case study.

## What is real vs illustrative

- **Real project evidence:** The images `assets/hydraulic-cad-hd.webp` and `assets/hydraulic-prototype-hd.webp` document the team's CAD presentation and built prototype.
- **3D viewer:** `assets/hydraulic-exploded.js` constructs an approximate, **non-dimensional** schematic using Three.js primitive geometry, based on documented component categories.
- **Not claimed:** Original SolidWorks geometry, tolerances, assembly interference, fit verification, manufactured dimensions, FEA or measured motion are **not** represented by the schematic.

## Features

- Drag/scroll orbit and zoom using `OrbitControls`.
- Explode slider (0–100%) with animated translations for six named part groups.
- Select a component by list or clicking its geometry; component information is sourced from the portfolio's project description.
- Reset the camera and turntable presentation mode.
- Keyboard-accessible slider and buttons, reduced-motion handling, on-demand visibility rendering, responsive layout and static-image fallback.
- Optional `?embed=1` mode renders inside the Hardware & CAD tab through a lazy-loaded iframe.

## Upgrading to source CAD

When the original SolidWorks assembly is available **with permission to publish**, export separate components with meaningful names and consistent pivots to GLB/glTF (e.g. through a suitable CAD exporter or conversion pipeline). Replace the procedural `buildFrame/buildGuard/buildGear/buildShaft/buildDrive/buildSensor` functions with a `GLTFLoader` pipeline, map source mesh names into the same component IDs, and replace the manually chosen `movements` with physically justified assembly-axis offsets. Only after inspecting dimensions and constraints should tolerances, keyway fits or a true section-cut be described as validated features.

Three.js is pinned at version 0.187.0 via an import map. The viewer requires WebGL and network access to the CDN; a static CAD image appears if the module cannot initialize.

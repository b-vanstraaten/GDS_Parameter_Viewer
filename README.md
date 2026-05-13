# GDS Parameter Viewer

Interactive GDS viewer for quantum dot device gate layouts. Renders GDS files using PyQtGraph, maps GDS layers to QCodes `Parameter` objects, and supports real-time voltage control via scroll or manual input. Shapes on the same layer that touch are merged automatically.

## Installation

```bash
pip install git+https://github.com/b-vanstraaten/gds_viewer.py.git
```

With optional QuTech dependencies (core-tools, sqdl-client):

```bash
pip install "GDS-Parameter-Viewer[qutech] @ git+https://github.com/b-vanstraaten/gds_viewer.py.git"
```

## Quick start

```python
from pathlib import Path
from qcodes import Parameter
from GDS_Parameter_Viewer.GDSViewer import GDSViewer

GDS_PATH = Path("example_gds/simple_device.gds")


class Gates:
    # Physical gates
    P1: Parameter = make_gate("P1")
    P2: Parameter = make_gate("P2")
    B12: Parameter = make_gate("B12")
    # Virtual gates
    vP1: Parameter = make_gate("vP1")
    vP2: Parameter = make_gate("vP2")
    vB12: Parameter = make_gate("vB12")


mapping = {
    "barriers": {
        "layers": [0],
        "real_gates": {0: "B12"},
        "virtual_gates": {0: "vB12"},
    },
    "plungers": {
        "layers": [1],
        "real_gates": {0: "P1", 1: "P2"},
        "virtual_gates": {0: "vP1", 1: "vP2"},
    },
}

gates = Gates()
viewer = GDSViewer(GDS_PATH, gates=gates, mapping=mapping)

# Set a gate voltage programmatically
gates.B12(-500)
```

## Mapping structure

The `mapping` dict groups GDS layers into named gate groups:

```python
mapping = {
    "<group_name>": {
        "layers": [<layer_number>, ...],   # GDS layer numbers to include; touching shapes are merged
        "real_gates": {<shape_index>: "<gate_name>", ...},    # physical gate parameters
        "virtual_gates": {<shape_index>: "<gate_name>", ...}, # virtual gate parameters
    },
}
```

- **`layers`** — list of GDS layer numbers. All shapes across these layers are loaded; shapes that touch are merged into a single polygon.
- **`real_gates`** — maps shape index (after merging) to a physical QCodes `Parameter` name on the `gates` object.
- **`virtual_gates`** — same, but for virtual gate parameters.

Shape indices are assigned in the order shapes appear after merging, starting at 0.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).

"""
Author: b-vanstraaten
Date: 13/05/2026
"""

from pathlib import Path

import numpy as np
from qcodes import Parameter

from GDS_Parameter_Viewer.GDSViewer import GDSViewer
from _make_gds import make_gds
from _functions import make_gate

GDS_PATH = Path(__file__).parent / "example_gds" / "simple_device.gds"


# ---------------------------------------------------------------------------
# Gate definitions
# ---------------------------------------------------------------------------

class Gates:
    """Container for physical and virtual gate voltage parameters."""
    # Physical gates
    P1: Parameter = make_gate("P1")
    P2: Parameter = make_gate("P2")
    B12: Parameter = make_gate("B12")

    # Virtual gates
    vP1: Parameter = make_gate("vP1")
    vP2: Parameter = make_gate("vP2")
    vB12: Parameter = make_gate("vB12")


# ---------------------------------------------------------------------------
# Layer → gate mapping
# ---------------------------------------------------------------------------

# Shapes on the same layer that are touching are merged by default,
# regardless of their GDS datatype.
#
# Structure per group:
#   layers       – GDS layer numbers to include (merged if touching)
#   real_gates   – shape index → physical gate name in Gates
#   virtual_gates – shape index → virtual gate name in Gates

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

# Build the GDS file: two layers, three gates (P1, P2 on layer 1; B12 on layer 0)
make_gds(GDS_PATH)

gates = Gates()

viewer = GDSViewer(GDS_PATH, gates=gates, mapping=mapping)

# Example: drive barrier gate to its minimum voltage
gates.B12(-500)

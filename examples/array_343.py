"""
Author: b-vanstraaten
Date: 13/05/2026
"""

from pathlib import Path
from GDS_Parameter_Viewer.GDSViewer import GDSViewer
from _functions import make_gates_class_from_dataset
from core_tools.data.sqdl import init_sqdl, load_by_uuid

GDS_PATH = Path(__file__).parent / 'example_gds' / '343.gds'


# %TODO fill in the complete mapping
mapping = {
    "barriers": {
        "layers": [5, 51],
        "real_gates": {
            7: "B1",
            5: "B2",
            4: 'B3',
            3: 'B4',
            2: 'B5',
            6: 'B6'
        },
        "virtual_gates": {},
    },
    "plungers": {
        "layers": [21],
        "real_gates": {},
        "virtual_gates": {},
    },
    'screening': {
        "layers": [31],
        "real_gates": {},
        "virtual_gates": {},
    },
    'ohmics': {
        "layers": [3],
        "real_gates": {},
        "virtual_gates": {},
    }
}

init_sqdl('MV-343_array')
ds = load_by_uuid(1762172270177283691)

gates = make_gates_class_from_dataset(ds)

# 3. Initialize and show
viewer = GDSViewer(GDS_PATH,
                gates=gates,
                mapping=mapping
        )





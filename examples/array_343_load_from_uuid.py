"""
Author: b-vanstraaten
Date: 13/05/2026
"""

from pathlib import Path
from GDS_Parameter_Viewer.GDSViewer import GDSViewer
from _functions import make_gates_class_from_dataset

# for qutech people
from core_tools.data.sqdl import init_sqdl, load_by_uuid

GDS_PATH = Path(__file__).parent / 'example_gds' / '343.gds'


# %TODO fill in the complete mapping
mapping = {'barriers': {'layers': [5, 51], 'real_gates': {0: 'NBL', 1: 'NBR', 2: 'B5', 3: 'B4', 4: 'B3', 5: 'B2', 6: 'B6', 7: 'B1', 8: 'WBR', 9: 'EBR', 10: 'B11', 11: 'B9', 12: 'B7', 13: 'B8', 14: 'B10', 15: 'B12', 16: 'WBL', 17: 'EBL', 18: 'SBL', 19: 'SBL'}, 'virtual_gates': {}}, 'ohmics': {'layers': [3], 'real_gates': {0: '', 2: 'NBL'}, 'virtual_gates': {}}, 'plungers': {'layers': [21], 'real_gates': {0: 'P6', 1: 'P2', 2: 'NP', 3: 'P3', 4: 'P1', 5: 'P7', 6: 'EP', 7: 'WP', 8: 'P4', 9: 'P5', 10: 'P8', 11: 'P10', 12: 'P9', 13: 'SP'}, 'virtual_gates': {}}, 'screening': {'layers': [31], 'real_gates': {2: 'NS', 3: 'WS', 6: 'ES', 10: 'SS'}, 'virtual_gates': {}}}

init_sqdl('MV-343_array')
ds = load_by_uuid(1762172270177283691)

gates = make_gates_class_from_dataset(ds)

# 3. Initialize and show
viewer = GDSViewer(GDS_PATH,
                gates=gates,
                mapping=mapping
        )





"""
Author: b-vanstraaten
Date: 31/03/2026
Description: GDS Viewer with Layer Toggling and 200ms Hardware Polling.
"""
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets, QtGui, QtCore

HIGHLIGHT_COLOR = 'r'
HIGHLIGHT_WIDTH = 3
NORMAL_BORDER_COLOR = 'k'

class MergedGate(QtWidgets.QGraphicsPathItem):
    def __init__(self, points, layer_key, layer_number):
        super().__init__()
        self.layer_key = layer_key
        self.layer_number = layer_number
        self.gate_id = f'{layer_key}:{layer_number}'

        path = QtGui.QPainterPath()
        if len(points) > 0:
            path.moveTo(points[0][0], points[0][1])
            for p in points[1:]: path.lineTo(p[0], p[1])
            path.closeSubpath()
        self.setPath(path)

        self.props = {
            'real': {'name': '', 'val': 0.0, 'inst': None},
            'virtual': {'name': '', 'val': 0.0, 'inst': None}
        }

        self.normal_pen = pg.mkPen(NORMAL_BORDER_COLOR, width=1, cosmetic=True)
        self.hover_pen = pg.mkPen(HIGHLIGHT_COLOR, width=HIGHLIGHT_WIDTH, cosmetic=True)
        self.setPen(self.normal_pen)

    def set_hover(self, is_hovered):
        self.setPen(self.hover_pen if is_hovered else self.normal_pen)

    def redraw_color(self, v_min, v_max, cmap_obj):
        val = self.props['real']['val']
        denom = (v_max - v_min) if v_max != v_min else 1.0
        norm_val = np.clip((val - v_min) / denom, 0, 1)
        self.setBrush(pg.mkBrush(cmap_obj.map(norm_val)))


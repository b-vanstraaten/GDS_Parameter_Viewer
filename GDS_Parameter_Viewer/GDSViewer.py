"""
Author: b-vanstraaten
Date: 31/03/2026
Description: GDS Viewer with Layer Toggling and 200ms Hardware Polling.
"""
import sys
from collections import defaultdict

import gdstk
import matplotlib.pyplot as plt
import numpy as np
import pyqtgraph as pg
from IPython import get_ipython
from pyqtgraph.Qt import QtWidgets, QtCore

from GDS_Parameter_Viewer.Gate import MergedGate
from GDS_Parameter_Viewer.GateWindow import GateWindow

# === Configuration ===
VOLTAGE_MIN_MAX = (-4000.0, 4000.0)
VOLTAGE_STEP = 1.0  # mV per scroll notch
SIDEBAR_WIDTH = 250
POLL_INTERVAL_MS = 200  # 5Hz update rate
DEFAULT_CMAP = 'Blues_r'
SIZE_X = 1200
SIZE_Y = 800

app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)


def extract(mapping, key):
    return {k: v[key] for k, v in mapping.items()}


class GDSViewer(QtWidgets.QMainWindow):
    def __init__(self, gds_path, gates=None, mapping = None,
                 **kwargs):
        super().__init__()
        self.hw = gates
        self.mapping = mapping

        self.all_gates = []
        self.layer_to_polygons = defaultdict(list)
        self.open_windows = {}
        self.current_hover_gate = None

        self.color_vmin = kwargs.get('color_vmin', -200.0)
        self.color_vmax = kwargs.get('color_vmax', 0.0)
        self.current_pg_cmap = self.get_pg_cmap(DEFAULT_CMAP)

        self.layer_mapping = extract(mapping, 'layers')
        self.gate_mapping = extract(mapping, 'real_gates')
        self.virtual_gate_mapping = extract(mapping, 'virtual_gates')

        self._setup_ui()
        if gds_path:
            self.process_gds(gds_path)

        self.apply_gate_mapping(self.gate_mapping, mode='real')
        self.apply_gate_mapping(self.virtual_gate_mapping, mode='virtual')

        # Event filter for Ctrl+Scroll
        self.plot_view.viewport().installEventFilter(self)

        self.poll_timer = QtCore.QTimer()
        self.poll_timer.timeout.connect(self._poll_hardware)
        self.poll_timer.start(POLL_INTERVAL_MS)

        # Check if we are running inside an IPython/PyCharm environment
        shell = get_ipython()
        if shell:
            shell.run_line_magic('gui', 'qt')

        self.resize(SIZE_X, SIZE_Y)
        self.show()
        self.auto_scale_limits()

    def _setup_ui(self):
        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        layout = QtWidgets.QHBoxLayout(cw)

        side = QtWidgets.QWidget()
        side.setFixedWidth(SIDEBAR_WIDTH)
        side_l = QtWidgets.QVBoxLayout(side)

        side_l.addWidget(QtWidgets.QLabel("<b>Layers</b>"))
        self.layer_list = QtWidgets.QListWidget()
        self.layer_list.setDragDropMode(QtWidgets.QAbstractItemView.DragDropMode.InternalMove)
        self.layer_list.itemChanged.connect(self._on_layer_toggle)
        self.layer_list.model().rowsMoved.connect(lambda: QtCore.QTimer.singleShot(10, self.update_layer_z_orders))
        side_l.addWidget(self.layer_list)

        side_l.addSpacing(20)
        side_l.addWidget(QtWidgets.QLabel("<b>Color Range (mV)</b>"))
        self.vmin_spin = QtWidgets.QDoubleSpinBox()
        self.vmin_spin.setRange(-5000, 5000)
        self.vmin_spin.setValue(self.color_vmin)
        self.vmin_spin.valueChanged.connect(self._on_limit_ui_changed)
        side_l.addWidget(self.vmin_spin)

        self.vmax_spin = QtWidgets.QDoubleSpinBox()
        self.vmax_spin.setRange(-5000, 5000)
        self.vmax_spin.setValue(self.color_vmax)
        self.vmax_spin.valueChanged.connect(self._on_limit_ui_changed)
        side_l.addWidget(self.vmax_spin)

        self.btn_autoscale = QtWidgets.QPushButton("Auto-Scale Colors")
        self.btn_autoscale.clicked.connect(self.auto_scale_limits)
        side_l.addWidget(self.btn_autoscale)
        side_l.addStretch()
        layout.addWidget(side)

        self.plot_view = pg.PlotWidget(background='w')
        layout.addWidget(self.plot_view)
        self.plot_view.scene().sigMouseMoved.connect(self._on_mouse_move)
        self.plot_view.scene().sigMouseClicked.connect(self._on_mouse_click)
        self.plot_view.setAspectLocked(True)
        self.statusBar().showMessage("Ready. Hover + Ctrl + Scroll to adjust.")

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.Type.Wheel and
                source is self.plot_view.viewport() and
                self.current_hover_gate):

            if event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
                delta = event.angleDelta().y()
                steps = delta / 120
                self._handle_scroll_value(self.current_hover_gate, steps)
                event.accept()
                return True
        return super().eventFilter(source, event)

    def _handle_scroll_value(self, gate, steps):
        """
        Adjusts the gate voltage based on scroll steps, prioritizing
        the virtual gate if it exists.
        """
        # Determine which gate role to target
        role = 'virtual' if gate.props.get('virtual') is not None else 'real'

        # Calculate and constrain the new value
        current_val = gate.props[role]['val']
        new_val = np.clip(current_val + (steps * VOLTAGE_STEP), *VOLTAGE_MIN_MAX)

        # Update only if the value actually changed
        if new_val != current_val:
            self.update_gate_value(gate, role, new_val)

    def update_gate_value(self, gate, role, val):
        target = gate.props[role]
        if target['inst']:
            try:
                target['inst'].set(val)
            except Exception as e:
                print(f"Set Error: {e}")

        target['val'] = val
        gate.redraw_color(self.color_vmin, self.color_vmax, self.current_pg_cmap)

        if gate.gate_id in self.open_windows:
            self.open_windows[gate.gate_id].update_ui_values(
                gate.props['real']['val'], gate.props['virtual']['val']
            )

        n = target['name'] or gate.gate_id
        self.statusBar().showMessage(f"Gate: {n} | Value: {val:.3f} mV")

    def process_gds(self, file_path):
        lib = gdstk.read_gds(file_path)
        top_cells = lib.top_level()
        if not top_cells:
            return

        # Build reverse map once, not per cell
        rev_map = {
            l: label
            for label, layers in self.layer_mapping.items()
            for l in layers
        } if self.layer_mapping else {}

        # Collect all cells to process
        all_cells = {cell.name: cell for cell in lib.cells}

        # Accumulate geometry across all cells
        raw_layers = defaultdict(list)

        for cell in all_cells.values():
            # Flatten each cell to resolve references and transformations
            flat = cell.flatten()

            for poly in flat.polygons:
                target = rev_map.get(poly.layer, poly.layer)
                raw_layers[target].append(poly)

            for path in flat.paths:
                target = rev_map.get(path.layers[0], path.layers[0])
                raw_layers[target].extend(path.to_polygons())

        # Track which layer labels already have a list item
        existing_labels = {
            self.layer_list.item(i).data(QtCore.Qt.ItemDataRole.UserRole)
            for i in range(self.layer_list.count())
        }

        for layer_label in raw_layers.keys():
            merged = gdstk.boolean(raw_layers[layer_label], [], "or")

            # Only add to layer list if not already present
            if layer_label not in existing_labels:
                lyp_info = self.lyp_data.get(layer_label, {}) if hasattr(self, "lyp_data") else {}
                display_name = lyp_info.get("name", str(layer_label))
                is_visible = lyp_info.get("visible", True)

                item = QtWidgets.QListWidgetItem(display_name)
                item.setData(QtCore.Qt.ItemDataRole.UserRole, layer_label)
                item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(
                    QtCore.Qt.CheckState.Checked if is_visible else QtCore.Qt.CheckState.Unchecked
                )
                self.layer_list.addItem(item)

            for i, shape in enumerate(merged):
                gate = MergedGate(shape.points, layer_label, i)
                self.plot_view.addItem(gate)
                self.all_gates.append(gate)
                self.layer_to_polygons[layer_label].append(gate)

        # Call these once after all cells are processed
        self.update_layer_z_orders()
        self.plot_view.autoRange()
        self.update_all_gate_colors()

    def _poll_hardware(self):
        any_change = False
        for gate in self.all_gates:
            gate_changed = False
            for role in ['real', 'virtual']:
                target = gate.props[role]
                if target['inst']:
                    try:
                        v = target['inst'].get()
                        if v != target['val']:
                            target['val'] = v
                            gate_changed = True
                            any_change = True
                    except:
                        pass

            if gate_changed and gate.gate_id in self.open_windows:
                self.open_windows[gate.gate_id].update_ui_values(
                    gate.props['real']['val'], gate.props['virtual']['val']
                )

        if any_change: self.update_all_gate_colors()

    def _on_mouse_move(self, pos):
        vb = self.plot_view.getViewBox()
        view_pos = vb.mapSceneToView(pos)

        visible = sorted([g for g in self.all_gates if g.isVisible()], key=lambda x: x.zValue(), reverse=True)
        found = None
        for g in visible:
            if g.path().contains(g.mapFromScene(pos)):
                found = g
                break

        if found != self.current_hover_gate:
            if self.current_hover_gate: self.current_hover_gate.set_hover(False)
            self.current_hover_gate = found
            if found:
                found.set_hover(True)
                n = found.props['real']['name'] or found.gate_id
                self.statusBar().showMessage(
                    f"Gate: {n} | Value: {found.props['real']['val']:.3f} mV | Ctrl+Scroll to set")

    def _on_mouse_click(self, event):
        if self.current_hover_gate: self._open_editor(self.current_hover_gate)

    def _open_editor(self, gate_obj):
        if gate_obj.gate_id in self.open_windows:
            self.open_windows[gate_obj.gate_id].activateWindow()
            return
        win = GateWindow(gate_obj)
        win.val_changed.connect(lambda role, val: self.update_gate_value(gate_obj, role, val))
        win.mapping_changed.connect(lambda role, name: self.sync_gate_to_hardware(gate_obj, role, name))
        win.closed.connect(lambda k: self.open_windows.pop(k, None))
        win.show()
        self.open_windows[gate_obj.gate_id] = win

    def sync_gate_to_hardware(self, gate_obj, role, name):
        target = gate_obj.props[role]
        target['name'] = name

        # Try to link to hardware
        if hasattr(self.hw, name):
            inst = getattr(self.hw, name)
            target['inst'] = inst
            # Reload the value from the new hardware immediately
            target['val'] = inst.get()
        else:
            target['inst'] = None

        # Refresh the visualization color
        gate_obj.redraw_color(self.color_vmin, self.color_vmax, self.current_pg_cmap)

        # CRITICAL: Push the reloaded value back to the GateWindow UI
        if gate_obj.gate_id in self.open_windows:
            self.open_windows[gate_obj.gate_id].update_ui_values(
                gate_obj.props['real']['val'],
                gate_obj.props['virtual']['val']
            )

        self.statusBar().showMessage(f"Mapped {role} to {name}. Value reloaded.")

        layer = gate_obj.layer_key
        if role == 'real':
            self.mapping[layer]['real_gates'][gate_obj.layer_number] = name

        elif role == 'virtual':
            self.mapping[layer]['virtual_gates'][gate_obj.layer_number] = name

        print(self.mapping)

    def get_pg_cmap(self, name):
        plt_cmap = plt.get_cmap(name)
        pos = np.linspace(0, 1, 256)
        colors = (plt_cmap(pos) * 255).astype(np.ubyte)
        return pg.ColorMap(pos, colors)

    def _on_layer_toggle(self, item):
        layer = item.data(QtCore.Qt.ItemDataRole.UserRole)
        vis = (item.checkState() == QtCore.Qt.CheckState.Checked)
        for g in self.layer_to_polygons[layer]: g.setVisible(vis)

    def update_layer_z_orders(self):
        count = self.layer_list.count()
        for i in range(count):
            layer = self.layer_list.item(i).data(QtCore.Qt.ItemDataRole.UserRole)
            for gate in self.layer_to_polygons[layer]: gate.setZValue(count - i)

    def _on_limit_ui_changed(self):
        self.color_vmin, self.color_vmax = self.vmin_spin.value(), self.vmax_spin.value()
        self.update_all_gate_colors()

    def auto_scale_limits(self):
        vals = [g.props['real']['val'] for g in self.all_gates if g.props['real']['name']]
        if vals:
            self.vmin_spin.setValue(min(vals))
            self.vmax_spin.setValue(max(vals))

    def update_all_gate_colors(self):
        for g in self.all_gates: g.redraw_color(self.color_vmin, self.color_vmax, self.current_pg_cmap)

    def apply_gate_mapping(self, mapping, mode='real'):
        assert mode in ['real', 'virtual'], f'Invalid mode {mode}'
        g_map = {g.gate_id: g for g in self.all_gates}
        for layer, d in mapping.items():
            for number, name in d.items():
                gid = f"{layer}:{number}"
                if gid in g_map: self.sync_gate_to_hardware(g_map[gid], mode, name)

    def get_gate_mapping(self):
        real_gates = {}
        virtual_gates = {}

        for gate in self.all_gates:

            layer_key = gate.layer_key
            layer_number = gate.layer_number

            if layer_key not in real_gates:
                real_gates[layer_key] = {}
                virtual_gates[layer_key] = {}

            if gate.props['real']['inst'] is not None:
                gate_name = gate.props['real']['name']
                real_gates[layer_key][layer_number] = gate_name

            if gate.props['virtual']['inst'] is not None:
                virtual_gate_name = gate.props['virtual']['name']
                virtual_gates[layer_key][layer_number] = virtual_gate_name

        return real_gates, virtual_gates

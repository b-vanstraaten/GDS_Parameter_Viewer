from pyqtgraph.Qt import QtWidgets, QtCore

# === Configuration ===
VOLTAGE_MIN_MAX = (-4000.0, 4000.0)
VOLTAGE_STEP = 1.0  # mV per scroll notch


class GateWindow(QtWidgets.QWidget):
    val_changed = QtCore.Signal(str, float)
    mapping_changed = QtCore.Signal(str, str)
    closed = QtCore.Signal(str)

    def __init__(self, gate_obj):
        super().__init__()
        self.gate_id = gate_obj.gate_id
        self.setWindowFlags(QtCore.Qt.WindowType.Window | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle(f"Gate Editor: {self.gate_id}")

        layout = QtWidgets.QFormLayout(self)
        self.edits = {
            'real': {
                'name': QtWidgets.QLineEdit(gate_obj.props['real']['name']),
                'val': self._create_sb(gate_obj.props['real']['val'])
            },
            'virtual': {
                'name': QtWidgets.QLineEdit(gate_obj.props['virtual']['name']),
                'val': self._create_sb(gate_obj.props['virtual']['val'])
            }
        }

        for role in ['real', 'virtual']:
            self.edits[role]['name'].returnPressed.connect(
                lambda r=role: self.mapping_changed.emit(r, self.edits[r]['name'].text())
            )
            sb = self.edits[role]['val']
            sb._typing = False
            sb.lineEdit().textEdited.connect(lambda _, s=sb: setattr(s, '_typing', True))
            sb.lineEdit().returnPressed.connect(
                lambda r=role, s=sb: (setattr(s, '_typing', False), self.val_changed.emit(r, s.value()))
            )
            sb.valueChanged.connect(
                lambda val, r=role, s=sb: self.val_changed.emit(r, val) if not s._typing else None
            )

        layout.addRow(QtWidgets.QLabel(f"<b>ID: {self.gate_id}</b>"))
        layout.addRow("Real Name:", self.edits['real']['name'])
        layout.addRow("Real Voltage:", self.edits['real']['val'])
        layout.addRow(QtWidgets.QFrame())
        layout.addRow("Virtual Name:", self.edits['virtual']['name'])
        layout.addRow("Virtual Voltage:", self.edits['virtual']['val'])

    def _create_sb(self, val):
        sb = QtWidgets.QDoubleSpinBox()
        sb.setRange(*VOLTAGE_MIN_MAX)
        sb.setSingleStep(VOLTAGE_STEP)
        sb.setValue(val)
        sb.setSuffix(" mV")
        sb.setDecimals(3)
        return sb

    def update_ui_values(self, real_v, virt_v):
        self.edits['real']['val'].blockSignals(True)
        self.edits['real']['val'].setValue(real_v)
        self.edits['real']['val'].blockSignals(False)
        self.edits['virtual']['val'].blockSignals(True)
        self.edits['virtual']['val'].setValue(virt_v)
        self.edits['virtual']['val'].blockSignals(False)

    def closeEvent(self, event):
        self.closed.emit(self.gate_id)
        super().closeEvent(event)
"""
Author: b-vanstraaten
Date: 13/05/2026
"""

from qcodes import Parameter


def make_gate(gate_name: str, value: float = 0.0) -> Parameter:
    """Create a QCoDeS Parameter representing a gate voltage.

    Args:
        gate_name: Name of the gate (used as both the parameter name and label).
        value: Initial voltage in mV. Defaults to 0.

    Returns:
        A Parameter initialised to ``value`` mV.
    """
    return Parameter(
        name=gate_name,
        label=gate_name,
        unit="mV",
        set_cmd=None,
        get_cmd=None,
        initial_value=value,
    )


def make_gates_class(
    gate_names: list[str],
    virtual_gate_names: list[str] | None = None,
    values: list[float] | None = None,
) -> type:
    """Dynamically create a Gates class containing QCoDeS Parameters.

    Args:
        gate_names: Names of the physical gates.
        virtual_gate_names: Names of the virtual gates. Defaults to none.
        values: Initial voltages (mV) for every gate, in the order
            ``gate_names + virtual_gate_names``. Defaults to 0 for all gates.

    Returns:
        A new ``Gates`` class whose attributes are the requested Parameters.
    """
    all_names = gate_names + (virtual_gate_names or [])
    all_values = values if values is not None else [0.0] * len(all_names)

    attributes = {name: make_gate(name, value) for name, value in zip(all_names, all_values)}
    return type("Gates", (object,), attributes)


def make_gates_class_from_dataset(dataset) -> type:
    """Reconstruct a Gates class from a QCoDeS dataset snapshot.

    Args:
        dataset: A QCoDeS dataset whose station snapshot contains a ``gates``
            instrument with recorded parameter values.

    Returns:
        A new ``Gates`` class whose Parameters are initialised to the values
        stored in the snapshot.
    """
    snapshot_params = dataset.snapshot["station"]["instruments"]["gates"]["parameters"]

    attributes = {
        name: make_gate(gate_name=p["name"], value=p["value"])
        for name, p in snapshot_params.items()
    }
    return type("Gates", (object,), attributes)
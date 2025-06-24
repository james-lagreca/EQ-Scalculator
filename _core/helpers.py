# In _core/helpers.py

import math

# Define base units and conversion factors to the base
_CONVERSIONS_TO_METER = {
    'm': 1.0,
    'km': 1000.0,
}
_CONVERSIONS_TO_METERSQ = {
    'm^2': 1.0,
    'km^2': 1e6,
}
# Base unit for Moment is Newton-meter (Nm)
_CONVERSIONS_TO_NM = {
    'Nm': 1.0,
    'dyne.cm': 1.0e-7 # 1 Nm = 1e7 dyne.cm
}

def convert_units(value, from_unit, to_unit):
    """Converts a value from one unit to another."""
    if from_unit == to_unit or from_unit is None or to_unit is None:
        return value

    # Length conversions
    if from_unit in _CONVERSIONS_TO_METER and to_unit in _CONVERSIONS_TO_METER:
        value_in_base = value * _CONVERSIONS_TO_METER[from_unit]
        return value_in_base / _CONVERSIONS_TO_METER[to_unit]

    # Area conversions
    if from_unit in _CONVERSIONS_TO_METERSQ and to_unit in _CONVERSIONS_TO_METERSQ:
        value_in_base = value * _CONVERSIONS_TO_METERSQ[from_unit]
        return value_in_base / _CONVERSIONS_TO_METERSQ[to_unit]
        
    # Moment conversions
    if from_unit in _CONVERSIONS_TO_NM and to_unit in _CONVERSIONS_TO_NM:
        value_in_base = value * _CONVERSIONS_TO_NM[from_unit]
        return value_in_base / _CONVERSIONS_TO_NM[to_unit]

    raise ValueError(f"Cannot convert from '{from_unit}' to '{to_unit}'")


import math
import numpy as np
import pandas as pd
from .helpers import convert_units

def _calculate_deterministic(form, x, a, b, direction):
    """Helper function to perform the core math for an equation."""
    try:
        if x is None or not isinstance(x, (int, float)) or pd.isna(x): return None
        x = float(x)
        if form == "log10(Y) = a + b * log10(X)":
            if direction == 'forward':
                if x <= 0: return None
                return 10**(a + b * math.log10(x))
            else: # inverse
                if x <= 0: return None
                return 10**((math.log10(x) - a) / b)
        elif form == "Y = a + b * log10(X)":
            if direction == 'forward':
                if x <= 0: return None
                return a + b * math.log10(x)
            else: # inverse
                return 10**((x - a) / b)
        elif form == "log10(Y) = a + b * X":
            if direction == 'forward':
                return 10**(a + b * x)
            else: # inverse
                if x <= 0: return None
                return (math.log10(x) - a) / b
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
    return None

def _get_target_segment(model_params, converted_input, direction):
    if converted_input is None: return None
    
    for segment in model_params:
        is_in_range = False
        if direction == 'forward':
            min_x, max_x = segment.get('range_x') or (None, None)
            if (min_x is None or converted_input >= min_x) and (max_x is None or converted_input < max_x):
                is_in_range = True
        else:  # 'inverse' direction
            min_x, max_x = segment.get('range_x') or (None, None)
            y_at_min_x = _calculate_deterministic(segment['equation_form'], min_x, segment['coefficients']['a'], segment['coefficients']['b'], 'forward') if min_x is not None else None
            y_at_max_x = _calculate_deterministic(segment['equation_form'], max_x, segment['coefficients']['a'], segment['coefficients']['b'], 'forward') if max_x is not None else None
            
            min_y, max_y = (y_at_min_x, y_at_max_x) if y_at_min_x is None or y_at_max_x is None or y_at_min_x < y_at_max_x else (y_at_max_x, y_at_min_x)
            if (min_y is None or converted_input >= min_y) and (max_y is None or converted_input < max_y):
                is_in_range = True

        if is_in_range:
            return segment

    if not model_params: return None
    return model_params[0] if converted_input < (model_params[0].get('range_x') or [0])[0] else model_params[-1]


def solve_relationship(model_params, input_val, input_unit, direction='forward'):
    x_key = 'x' if direction == 'forward' else 'y'
    y_key = 'y' if direction == 'forward' else 'x'
    try:
        model_input_unit = model_params[0]['units'][x_key]
        converted_input = convert_units(input_val, input_unit, model_input_unit) if model_input_unit else input_val
    except (ValueError, TypeError) as e:
        return None, str(e)
    target_segment = _get_target_segment(model_params, converted_input, direction)
    if not target_segment:
        return None, "Could not identify a model segment."
    result = _calculate_deterministic(target_segment['equation_form'], converted_input, target_segment['coefficients']['a'], target_segment['coefficients']['b'], direction)
    if result is None: return None, "Mathematical error during calculation."
    return result, target_segment['units'][y_key]

def check_if_extrapolating(model_params, input_val, input_unit, direction='forward'):
    x_key = 'x' if direction == 'forward' else 'y'
    try:
        model_input_unit = model_params[0]['units'][x_key]
        converted_input = convert_units(input_val, input_unit, model_input_unit) if model_input_unit else input_val
    except (ValueError, TypeError):
        return None
    
    is_within_any_range = False
    for segment in model_params:
        if direction == 'forward':
            min_x, max_x = segment.get('range_x') or (None, None)
            if (min_x is None or converted_input >= min_x) and (max_x is None or converted_input < max_x):
                is_within_any_range = True; break
        else: # 'inverse'
            min_x, max_x = segment.get('range_x') or (None, None)
            y_at_min_x = _calculate_deterministic(segment['equation_form'], min_x, segment['coefficients']['a'], segment['coefficients']['b'], 'forward') if min_x is not None else None
            y_at_max_x = _calculate_deterministic(segment['equation_form'], max_x, segment['coefficients']['a'], segment['coefficients']['b'], 'forward') if max_x is not None else None
            min_y, max_y = (y_at_min_x, y_at_max_x) if y_at_min_x is None or y_at_max_x is None or y_at_min_x < y_at_max_x else (y_at_max_x, y_at_min_x)
            if (min_y is None or converted_input >= min_y) and (max_y is None or converted_input < max_y):
                is_within_any_range = True; break
    
    if not is_within_any_range:
        return "Warning: Input is outside the model's recommended validity range. Result is an extrapolation."
    return None

def solve_one_simulation_run(model_params, input_val, input_unit, direction='forward', include_model_uncertainty=True):
    x_key = 'x' if direction == 'forward' else 'y'
    y_key = 'y' if direction == 'forward' else 'x'
    try:
        model_input_unit = model_params[0]['units'][x_key]
        converted_input = convert_units(input_val, input_unit, model_input_unit) if model_input_unit else input_val
    except (ValueError, TypeError):
        return None, None
    target_segment = _get_target_segment(model_params, converted_input, direction)
    if not target_segment:
        return None, "Could not identify a model segment."
    a, b = target_segment['coefficients']['a'], target_segment['coefficients']['b']
    if include_model_uncertainty:
        if 'std_dev_a' in target_segment:
            try: a = np.random.normal(loc=a, scale=float(target_segment['std_dev_a']))
            except (ValueError, TypeError): pass
        if 'log10_y_std_dev' in target_segment and direction == 'forward':
            std_dev = target_segment.get('log10_y_std_dev', 0)
            deterministic_result = _calculate_deterministic(target_segment['equation_form'], converted_input, a, b, direction)
            if deterministic_result is not None and deterministic_result > 0:
                log10_y = math.log10(deterministic_result)
                log10_y_random = np.random.normal(loc=log10_y, scale=std_dev)
                return 10**log10_y_random, target_segment['units'][y_key]
            else: return None, "Cannot apply log10 uncertainty to non-positive result."
    result = _calculate_deterministic(target_segment['equation_form'], converted_input, a, b, direction)
    return result, target_segment['units'][y_key]

def calculate_curve(model_params, x_values, input_unit, direction='forward'):
    y_values, output_unit = [], ""
    for x in x_values:
        y, unit_or_error = solve_relationship(model_params, x, input_unit, direction)
        y_values.append(y)
        if y is not None and not output_unit and isinstance(unit_or_error, str):
            output_unit = unit_or_error
    return y_values, output_unit
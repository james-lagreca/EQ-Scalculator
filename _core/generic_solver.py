# In _core/generic_solver.py

import math
import numpy as np
from .helpers import convert_units

def _calculate_deterministic(form, x, a, b, direction):
    """Helper function to perform the core math for an equation."""
    try:
        # Ensure x is a number for math operations
        if x is None: return None
        x = float(x)

        if form == "log10(Y) = a + b * log10(X)":
            if direction == 'forward': 
                if x <= 0: return None # log10(x) is undefined for x <= 0
                return 10**(a + b * math.log10(x))
            else: 
                if x <= 0: return None
                return 10**((math.log10(x) - a) / b)
        elif form == "Y = a + b * log10(X)":
            if direction == 'forward': 
                if x <= 0: return None
                return a + b * math.log10(x)
            else: 
                return 10**((x - a) / b)
        elif form == "log10(Y) = a + b * X":
            if direction == 'forward': 
                return 10**(a + b * x)
            else:
                if x <= 0: return None
                return (math.log10(x) - a) / b
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
    return None

def _get_target_segment(model_params, converted_input, direction):
    """
    Finds the appropriate model segment for a given input value.
    If the value is outside all defined ranges, it selects the
    first or last segment to allow for extrapolation.
    """
    if converted_input is None:
        return None
        
    # 1. Try to find a segment where the input is strictly within range
    for segment in model_params:
        min_x, max_x = segment.get('range_x') or (None, None)
        
        is_in_range = False
        if direction == 'forward':
            if (min_x is None or converted_input >= min_x) and \
               (max_x is None or converted_input < max_x):
                is_in_range = True
        else:  # 'inverse' direction
            y_at_min_x = _calculate_deterministic(segment['equation_form'], min_x, segment['coefficients']['a'], segment['coefficients']['b'], 'forward')
            y_at_max_x = _calculate_deterministic(segment['equation_form'], max_x, segment['coefficients']['a'], segment['coefficients']['b'], 'forward')
            
            # Handle cases where function might be decreasing
            min_y, max_y = (y_at_min_x, y_at_max_x) if y_at_min_x is None or y_at_max_x is None or y_at_min_x < y_at_max_x else (y_at_max_x, y_at_min_x)

            if (min_y is None or converted_input >= min_y) and \
               (max_y is None or converted_input < max_y):
                is_in_range = True

        if is_in_range:
            return segment

    # 2. If not in any range, choose a segment for extrapolation.
    # Assumes segments are ordered in the JSON file.
    if direction == 'forward':
        first_segment_min = model_params[0].get('range_x', [None, None])[0]
        if first_segment_min is not None and converted_input < first_segment_min:
            return model_params[0]
        else:
            return model_params[-1]
    else: # 'inverse'
        y_at_first_min = _calculate_deterministic(model_params[0]['equation_form'], model_params[0].get('range_x')[0], model_params[0]['coefficients']['a'], model_params[0]['coefficients']['b'], 'forward')
        if y_at_first_min is not None and converted_input < y_at_first_min:
             return model_params[0]
        else:
             return model_params[-1]

def solve_relationship(model_params, input_val, input_unit, direction='forward'):
    """
    Solves a scaling relationship. This function will now always attempt to
    calculate a value, even if it requires extrapolation. It returns the 
    result and its unit, or an error message if a mathematical error occurs.
    """
    x_key = 'x' if direction == 'forward' else 'y'
    y_key = 'y' if direction == 'forward' else 'x'

    model_input_unit = model_params[0]['units'][x_key]
    
    try:
        converted_input = convert_units(input_val, input_unit, model_input_unit) if model_input_unit else input_val
    except ValueError as e:
        return None, str(e)

    target_segment = _get_target_segment(model_params, converted_input, direction)
    
    if not target_segment:
        return None, "Could not identify a model segment for calculation."

    result = _calculate_deterministic(
        target_segment['equation_form'], 
        converted_input, 
        target_segment['coefficients']['a'], 
        target_segment['coefficients']['b'], 
        direction
    )
    
    if result is None:
        return None, "Mathematical error during calculation (e.g., log of zero)."
        
    return result, target_segment['units'][y_key]

def check_if_extrapolating(model_params, input_val, input_unit, direction='forward'):
    """
    Performs a strict check to see if the input value falls outside the
    defined validity range of all segments in a model.
    Returns a warning string if it's outside the range, otherwise returns None.
    """
    x_key = 'x' if direction == 'forward' else 'y'
    try:
        converted_input = convert_units(input_val, input_unit, model_params[0]['units'][x_key]) if model_params[0]['units'][x_key] else input_val
    except ValueError:
        return None # Can't check range if units are wrong

    is_within_any_range = False
    for segment in model_params:
        min_x, max_x = segment.get('range_x') or (None, None)
        
        if direction == 'forward':
            if (min_x is None or converted_input >= min_x) and \
               (max_x is None or converted_input < max_x):
                is_within_any_range = True
                break
        else: # 'inverse'
            y_at_min_x = _calculate_deterministic(segment['equation_form'], min_x, segment['coefficients']['a'], segment['coefficients']['b'], 'forward')
            y_at_max_x = _calculate_deterministic(segment['equation_form'], max_x, segment['coefficients']['a'], segment['coefficients']['b'], 'forward')
            min_y, max_y = (y_at_min_x, y_at_max_x) if y_at_min_x is None or y_at_max_x is None or y_at_min_x < y_at_max_x else (y_at_max_x, y_at_min_x)

            if (min_y is None or converted_input >= min_y) and \
               (max_y is None or converted_input < max_y):
                is_within_any_range = True
                break

    if not is_within_any_range:
        return "Warning: Input is outside the model's recommended validity range. The result is an extrapolation."
    
    return None

def solve_one_simulation_run(model_params, input_val, input_unit, direction='forward'):
    """
    Performs a single stochastic calculation for a Monte Carlo simulation.
    This will now also extrapolate if the input value is out of range.
    """
    x_key = 'x' if direction == 'forward' else 'y'
    y_key = 'y' if direction == 'forward' else 'x'
    model_input_unit = model_params[0]['units'][x_key]
    
    converted_input = convert_units(input_val, input_unit, model_input_unit) if model_input_unit else input_val
    
    target_segment = _get_target_segment(model_params, converted_input, direction)
    
    if not target_segment:
        return None, "Could not identify a model segment."

    a = target_segment['coefficients']['a']
    b = target_segment['coefficients']['b']
    
    if 'std_dev_a' in target_segment and isinstance(target_segment['std_dev_a'], str):
        try:
            low_a, high_a = map(float, target_segment['std_dev_a'].split(' to '))
            mean_a = (low_a + high_a) / 2
            std_a = (high_a - mean_a)
            a_random = np.random.normal(loc=a, scale=std_a)
        except (ValueError, TypeError):
             a_random = a
    else:
        a_random = a
        
    result = _calculate_deterministic(target_segment['equation_form'], converted_input, a_random, b, direction)
    
    if 'log10_y_std_dev' in target_segment and result is not None and direction == 'forward':
        std_dev = target_segment['log10_y_std_dev']
        log10_y = math.log10(result)
        log10_y_random = np.random.normal(loc=log10_y, scale=std_dev)
        result = 10**log10_y_random
    
    return result, target_segment['units'][y_key]

# --- THIS FUNCTION WAS MISSING AND HAS BEEN ADDED BACK ---
def calculate_curve(model_params, x_values, input_unit, direction='forward'):
    """Calculates the Y values for a given range of X values to plot a curve."""
    y_values = []
    output_unit = ""
    for x in x_values:
        y, unit_or_error = solve_relationship(model_params, x, input_unit, direction)
        y_values.append(y)
        if y is not None and not output_unit:
            output_unit = unit_or_error
    return y_values, output_unit

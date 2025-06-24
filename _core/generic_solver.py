# In _core/generic_solver.py

import math
import numpy as np
from .helpers import convert_units

# In _core/generic_solver.py

def solve_relationship(model_params, input_val, input_unit, direction='forward'):
    """
    Solves a scaling relationship for a given input value (deterministic).
    """
    # In inverse mode, the roles of X and Y are swapped.
    x_key = 'x' if direction == 'forward' else 'y'
    y_key = 'y' if direction == 'forward' else 'x'

    model_input_unit = model_params[0]['units'][x_key]
    
    if model_input_unit:
        try:
            converted_input = convert_units(input_val, input_unit, model_input_unit)
        except ValueError as e:
            return None, str(e)
    else:
        converted_input = input_val

    for segment in model_params:
        a = segment['coefficients']['a']
        b = segment['coefficients']['b']
        form = segment['equation_form']
        
        # --- START: MORE ROBUST MODIFIED LOGIC ---
        if direction == 'forward':
            min_x, max_x = segment.get('range_x') or (None, None)
            if (min_x is not None and converted_input < min_x) or \
               (max_x is not None and converted_input > max_x):
                continue
        else:  # direction == 'inverse'
            min_x, max_x = segment.get('range_x') or (None, None)

            if min_x is None and max_x is None:
                # If the segment has no x-range, it's always valid.
                pass
            else:
                # Calculate the Y-range from the X-range to see if our input fits.
                y_at_min_x = _calculate_deterministic(form, min_x, a, b, 'forward') if min_x is not None else None
                y_at_max_x = _calculate_deterministic(form, max_x, a, b, 'forward') if max_x is not None else None
                
                # If a calculation failed (e.g. log(0)), treat that boundary as open.
                min_y, max_y = y_at_min_x, y_at_max_x

                # Ensure min_y is the smaller one for the comparison.
                if min_y is not None and max_y is not None and min_y > max_y:
                    min_y, max_y = max_y, min_y

                # Check if the input Y-value is outside the calculated Y-range of this segment.
                if (min_y is not None and converted_input < min_y) or \
                   (max_y is not None and converted_input > max_y):
                    continue
        # --- END: MORE ROBUST MODIFIED LOGIC ---

        output_unit = segment['units'][y_key]
        result = _calculate_deterministic(form, converted_input, a, b, direction)
        
        if result is not None:
             return result, output_unit

    return None, "Input value is outside the valid range for all segments of this model."

def calculate_curve(model_params, x_values, input_unit, direction='forward'):
    """Calculates the Y values for a given range of X values to plot a curve."""
    y_values = []
    output_unit = ""
    for x in x_values:
        y, unit = solve_relationship(model_params, x, input_unit, direction)
        y_values.append(y)
        if y is not None and not output_unit:
            output_unit = unit
    return y_values, output_unit

# --- NEW MONTE CARLO FUNCTION ---
def solve_one_simulation_run(model_params, input_val, input_unit, direction='forward'):
    """
    Performs a single stochastic calculation for a Monte Carlo simulation.
    It introduces randomness based on the model's defined uncertainty.
    """
    x_key = 'x' if direction == 'forward' else 'y'
    y_key = 'y' if direction == 'forward' else 'x'
    model_input_unit = model_params[0]['units'][x_key]
    
    if model_input_unit:
        converted_input = convert_units(input_val, input_unit, model_input_unit)
    else:
        converted_input = input_val

    # Find the correct segment for the deterministic input
    target_segment = None
    for segment in model_params:
        min_range, max_range = segment.get('range_x') or (None, None)
        if direction == 'forward':
            if (min_range is None or converted_input >= min_range) and \
               (max_range is None or converted_input < max_range):
                target_segment = segment
                break
        else: # For inverse, just use the first segment for now
            target_segment = segment
            break
    
    if not target_segment:
        return None, "Input outside valid range."

    # --- Introduce randomness based on uncertainty ---
    a = target_segment['coefficients']['a']
    b = target_segment['coefficients']['b']
    form = target_segment['equation_form']
    
    # Case 1: Uncertainty on the 'a' coefficient (Leonard 2014)
    if 'std_dev_a' in target_segment and isinstance(target_segment['std_dev_a'], str):
        try:
            low_a, high_a = map(float, target_segment['std_dev_a'].split(' to '))
            # Assume range is +/- 1 std dev from the mean 'a'
            mean_a = (low_a + high_a) / 2
            std_a = (high_a - mean_a)
            a_random = np.random.normal(loc=a, scale=std_a)
        except (ValueError, TypeError):
             a_random = a # Fallback if parsing fails
    else:
        a_random = a
        
    result = _calculate_deterministic(form, converted_input, a_random, b, direction)
    
    # Case 2: Uncertainty on the final log10(Y) value (Somerville, Yang)
    if 'log10_y_std_dev' in target_segment and result is not None and direction == 'forward':
        std_dev = target_segment['log10_y_std_dev']
        log10_y = math.log10(result)
        log10_y_random = np.random.normal(loc=log10_y, scale=std_dev)
        result = 10**log10_y_random
    
    return result, target_segment['units'][y_key]

def _calculate_deterministic(form, x, a, b, direction):
    """Helper function to perform the core math for an equation."""
    try:
        if form == "log10(Y) = a + b * log10(X)":
            if direction == 'forward': return 10**(a + b * math.log10(x))
            else: return 10**((math.log10(x) - a) / b)
        elif form == "Y = a + b * log10(X)":
            if direction == 'forward': return a + b * math.log10(x)
            else: return 10**((x - a) / b)
        elif form == "log10(Y) = a + b * X":
            if direction == 'forward': return 10**(a + b * x)
            else: return (math.log10(x) - a) / b
    except (ValueError, ZeroDivisionError):
        return None
    return None


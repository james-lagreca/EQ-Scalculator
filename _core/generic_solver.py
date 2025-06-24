# In _core/generic_solver.py

import math
from .helpers import convert_units # Assuming helpers.py is in the same _core/ directory

def solve_relationship(model_params, input_val, input_unit, direction='forward'):
    """
    Solves a scaling relationship for a given input value, with support for inverse calculations.
    This is the core engine of the calculator.

    Args:
        model_params (list): A list of dictionaries for a specific relationship.
        input_val (float): The user's input value.
        input_unit (str): The unit of the user's input value.
        direction (str): 'forward' or 'inverse'.

    Returns:
        A tuple of (result, result_unit_or_error_message).
    """
    # In inverse mode, the roles of X and Y are swapped.
    x_key = 'x' if direction == 'forward' else 'y'
    y_key = 'y' if direction == 'forward' else 'x'

    model_input_unit = model_params[0]['units'][x_key]
    
    # Use the helper function to convert the user's input to what the model expects.
    if model_input_unit:
        try:
            # Note: For inverse, we check if the input value is within the model's OUTPUT range.
            # A full implementation would pre-calculate these inverted ranges. For now, we check later.
            converted_input = convert_units(input_val, input_unit, model_input_unit)
        except ValueError as e:
            return None, str(e)
    else:
        converted_input = input_val

    # Find the correct segment. For inverse, we check against the output of the forward equation.
    for segment in model_params:
        a = segment['coefficients']['a']
        b = segment['coefficients']['b']
        form = segment['equation_form']
        
        # --- Check if the input is in the valid range ---
        # For forward, we check the input directly.
        if direction == 'forward':
            min_range, max_range = segment['range_x']
            in_range = True
            if min_range is not None and converted_input < min_range:
                in_range = False
            if max_range is not None and converted_input > max_range:
                in_range = False
            if not in_range:
                continue # Try the next segment
        
        # --- Apply the correct mathematical formula ---
        output_unit = segment['units'][y_key]

        # Standard log-log relation (e.g., Leonard 2014)
        if form == "log10(Y) = a + b * log10(X)":
            if direction == 'forward':
                if converted_input <= 0: return None, "Input must be positive for log-log scale."
                log10_y = a + b * math.log10(converted_input)
                result = 10**log10_y
                return result, output_unit
            else: # Inverse
                if converted_input <= 0: return None, "Input must be positive for log-log scale."
                # log10(X) = (log10(Y) - a) / b
                log10_x = (math.log10(converted_input) - a) / b
                result = 10**log10_x
                return result, output_unit
        
        # Semi-log relation (e.g., Leonard 2014, Mw from L)
        elif form == "Y = a + b * log10(X)":
            if direction == 'forward':
                if converted_input <= 0: return None, "Input must be positive for log scale."
                result = a + b * math.log10(converted_input)
                return result, output_unit
            else: # Inverse
                # log10(X) = (Y - a) / b
                log10_x = (converted_input - a) / b
                result = 10**log10_x
                return result, output_unit

        # Log-linear relation (e.g., Yang 2020)
        elif form == "log10(Y) = a + b * X":
            if direction == 'forward':
                log10_y = a + b * converted_input
                result = 10**log10_y
                return result, output_unit
            else: # Inverse
                if converted_input <= 0: return None, "Input must be positive for log scale."
                # X = (log10(Y) - a) / b
                result = (math.log10(converted_input) - a) / b
                return result, output_unit
        else:
            return None, f"Unknown equation form: {form}"

    return None, "Input value is outside the valid range for all segments of this model."


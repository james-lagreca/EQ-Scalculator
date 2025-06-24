# File: tests/test_solver.py

import pytest
import json
import os
import sys

# Add the root directory to the Python path to allow imports from _core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from _core.generic_solver import solve_relationship

# --- Test Data Loading ---
@pytest.fixture(scope="module")
def loaded_models():
    """Loads all .json model files for testing."""
    all_models = {}
    models_dir = "scaling_models"
    for author_dir in os.listdir(models_dir):
        author_path = os.path.join(models_dir, author_dir)
        if os.path.isdir(author_path):
            for file in os.listdir(author_path):
                if file.endswith(".json"):
                    file_path = os.path.join(author_path, file)
                    with open(file_path, 'r') as f:
                        all_models.update(json.load(f))
    return all_models

# --- Test Cases ---
# Each tuple represents one test: (paper, fault_type, relation, input_val, input_unit, direction, expected_output)
test_cases = [
    # --- Yang et al. 2020 ---
    # Test case from Figure 6B (Australia+Ungava Fit)
    # For Mw = 6.0, log10(SRL) = -1.93 + 0.50 * 6.0 = 1.07. Expected SRL = 10**1.07 = 11.749 km
    ("Yang et al. 2020", "SCR - Reverse", "SRL_from_Mw", 6.0, None, 'forward', 11.749),
    
    # Inverse test for the same relationship
    ("Yang et al. 2020", "SCR - Reverse", "SRL_from_Mw", 11.749, 'km', 'inverse', 6.0),

    # --- Leonard 2014 ---
    # Test case from Table 4 for Mw from L (SCR Dip-Slip) for L > 2.5km
    # For L = 10km, Mw = 4.32 + 1.667 * log10(10) = 5.987
    ("Leonard 2014", "SCR Dip-Slip", "Mw_from_L", 10.0, 'km', 'forward', 5.987),

    # Inverse test for the same relationship
    ("Leonard 2014", "SCR Dip-Slip", "Mw_from_L", 5.987, None, 'inverse', 10.0),
    
    # Test a different unit from Table 3 (M0 from L) which expects meters
    # For L=1000m (1km), log10(M0) = 6.382 + 3.0 * log10(1000) = 6.382 + 9 = 15.382. Expected M0 = 10**15.382
    ("Leonard 2014", "SCR Dip-Slip", "M0_from_L", 1.0, 'km', 'forward', 10**15.382),

    # --- Somerville 2014 --- NEW TEST CASES ---
    # Test case from Table 3, using Combined Methods model.
    # For M0 = 2.8E25 dyne.cm, log10(A) = -14.946 + 0.66667 * log10(2.8E25) = 2.0188. Expected A = 10**2.0188 = 104.42 km^2
    ("Somerville 2014", "SCR - Combined Methods", "A_from_M0", 2.8e25, 'dyne.cm', 'forward', 104.42),

    # Inverse test for the same relationship
    ("Somerville 2014", "SCR - Combined Methods", "A_from_M0", 104.42, 'km^2', 'inverse', 2.8e25)
]

@pytest.mark.parametrize("paper, fault_type, relation, input_val, input_unit, direction, expected", test_cases)
def test_all_relationships(loaded_models, paper, fault_type, relation, input_val, input_unit, direction, expected):
    """
    A single test function that validates multiple relationships using parametrized data.
    """
    # 1. Get the model parameters from the loaded data.
    model_key = relation
        
    model_params = loaded_models[paper]['fault_types'][fault_type][model_key]

    # 2. Call the solver with the test data and specified direction
    result, result_unit = solve_relationship(model_params, input_val, input_unit, direction)
    
    # 3. Assert that the result is correct
    assert result is not None, f"Solver returned an error: {result_unit}"
    assert result == pytest.approx(expected, rel=1e-2) # Check if result is close to expected


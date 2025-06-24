# The main application file for the EQ-Scalculator

import streamlit as st
import json
import os
import pandas as pd
import plotly.express as px
from _core.generic_solver import solve_relationship

# --- Parameter Alias Configuration ---
# This dictionary maps various names from different papers to a single,
# canonical name for consistency in the UI.
PARAMETER_ALIASES = {
    'L': 'L',           # Rupture Length
    'W': 'W',           # Rupture Width
    'A': 'A',           # Rupture Area
    'D': 'AD',          # Leonard's 'Average Displacement' maps to 'AD'
    'AD': 'AD',         # Yang's 'Average Displacement'
    'MD': 'MD',         # Yang's 'Maximum Displacement'
    'M0': 'M0',         # Seismic Moment
    'Mw': 'Mw',         # Moment Magnitude
    'SRL': 'SRL',       # Surface Rupture Length
    'L_SR': 'SRL'       # Leonard's 'Surface Rupture Length'
}

@st.cache_data
def load_all_models(models_dir="scaling_models"):
    """
    Loads all .json model files, creating a unified list of canonical parameters.
    """
    all_models = {}
    canonical_params = set()
    
    for author_dir in os.listdir(models_dir):
        author_path = os.path.join(models_dir, author_dir)
        if os.path.isdir(author_path):
            for file in os.listdir(author_path):
                if file.endswith(".json"):
                    file_path = os.path.join(author_path, file)
                    with open(file_path, 'r') as f:
                        try:
                            model_data = json.load(f)
                            all_models.update(model_data)
                            # Scan for parameters and convert to canonical names
                            for paper in model_data.values():
                                for fault in paper['fault_types'].values():
                                    for key in fault.keys():
                                        y, x = key.split('_from_')
                                        canonical_params.add(PARAMETER_ALIASES.get(y, y))
                                        canonical_params.add(PARAMETER_ALIASES.get(x, x))
                        except Exception as e:
                            st.error(f"Error parsing {file_path}: {e}")
    
    return all_models, sorted(list(canonical_params))

# --- UI Setup ---
st.set_page_config(layout="wide")
st.title("Earthquake Scaling Relationship Calculator (EQ-Scalculator)")
st.markdown("Select an input and output parameter, then choose a model from the sidebar to see the result.")

# --- Data Loading ---
all_models, canonical_params = load_all_models()

if not all_models:
    st.error("No scaling models found. Make sure you have .json files in subdirectories.")
    st.stop()

# --- User Input Sidebar ---
st.sidebar.header("Calculation Setup")

st.sidebar.markdown("##### 1. Select Parameters")
input_var = st.sidebar.selectbox("Input Parameter", canonical_params, index=canonical_params.index('Mw') if 'Mw' in canonical_params else 0)
output_var = st.sidebar.selectbox("Output Parameter", canonical_params, index=canonical_params.index('SRL') if 'SRL' in canonical_params else 1)

# --- Model Filtering Logic (with Aliases) ---
available_models = {}
for paper_name, paper_data in all_models.items():
    for fault_name, fault_data in paper_data['fault_types'].items():
        for rel_key, rel_data in fault_data.items():
            y_param, x_param = rel_key.split('_from_')
            
            # Get canonical names for the relationship's parameters
            canonical_y = PARAMETER_ALIASES.get(y_param, y_param)
            canonical_x = PARAMETER_ALIASES.get(x_param, x_param)
            
            # Check for forward and inverse matches using canonical names
            is_forward_match = (canonical_x == input_var and canonical_y == output_var)
            is_inverse_match = (canonical_y == input_var and canonical_x == output_var)
            
            if is_forward_match or is_inverse_match:
                model_id = f"{paper_name} - {fault_name}"
                direction = 'forward' if is_forward_match else 'inverse'
                # Store everything needed to run the calculation
                available_models[model_id] = (paper_name, fault_name, rel_key, direction)

st.sidebar.markdown("##### 2. Select Model")
if not available_models:
    st.sidebar.warning(f"No model found that directly relates `{input_var}` and `{output_var}`.")
    st.stop()

selected_model_id = st.sidebar.selectbox("Available Models for this Pair", list(available_models.keys()))

st.sidebar.markdown(f"##### 3. Enter Value for `{input_var}`")
input_value = st.sidebar.number_input(f"Value", format="%.4f", value=6.0)

# Provide sensible unit options based on the canonical name
if 'A' in input_var: unit_options = ['km^2', 'm^2']
elif any(c in input_var for c in ['L', 'W', 'D', 'SRL']): unit_options = ['km', 'm']
else: unit_options = ['N/A']
input_unit = st.sidebar.selectbox("Input Unit:", unit_options)
if input_unit == 'N/A': input_unit = None

# --- Calculation and Display ---
col1, col2 = st.columns([1, 2])

# Unpack the model information needed for the calculation
paper_name, fault_name, rel_key, direction = available_models[selected_model_id]
relation_params = all_models[paper_name]['fault_types'][fault_name][rel_key]

result, result_unit_or_error = solve_relationship(relation_params, input_value, input_unit, direction)

with col1:
    st.subheader("Calculation Result")
    if result is not None:
        st.success(f"**Calculated `{output_var}`:**")
        result_str = f"{result:.4f}"
        unit_str = result_unit_or_error or ""
        st.metric(label=f"{output_var} ({unit_str})", value=result_str)
    else:
        st.error(f"**Error:** {result_unit_or_error}")

with col2:
    st.subheader("Visualization & Model Details")
    if result is not None:
        chart_data = pd.DataFrame({'Parameter': [f"{input_var} ({input_unit or ''})", f"{output_var} ({unit_str})"],'Value': [input_value, result],'Type': ['Input', 'Output']})
        fig = px.bar(chart_data, x='Parameter', y='Value', color='Type', title='Comparison of Input and Output', labels={'Value': 'Parameter Value'}, color_discrete_map={'Input': '#1f77b4', 'Output': '#2ca02c'})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(f"**Model:** `{paper_name}`")
    st.markdown(f"**Fault Type:** `{fault_name}`")
    st.markdown(f"**Relationship Used:** `{rel_key}`")
    with st.expander("Show Raw Model Parameters"):
        st.json(relation_params)

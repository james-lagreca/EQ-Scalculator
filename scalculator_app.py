# The main application file for the EQ-Scalculator

import streamlit as st
import json
import os
import pandas as pd
import numpy as np
import io
import plotly.express as px
from _core.generic_solver import solve_relationship, calculate_curve, solve_one_simulation_run, check_if_extrapolating
from _core.helpers import convert_units

# --- Parameter Alias Configuration ---
PARAMETER_ALIASES = {
    'L': 'L', 'W': 'W', 'A': 'A', 'D': 'AD', 'AD': 'AD', 'MD': 'MD',
    'M0': 'M0', 'Mw': 'Mw', 'SRL': 'SRL', 'L_SR': 'SRL'
}

# --- Unit Options Dictionary ---
UNIT_OPTIONS = {
    'Length (L/SRL)': ['km', 'm'], 'Magnitude (Mw/M0)': ['N/A'],
    'A': ['km^2', 'm^2'], 'L': ['km', 'm'], 'W': ['km', 'm'], 'SRL': ['km', 'm'],
    'AD': ['m'], 'MD': ['m'],
    'Mw': ['N/A'], 'M0': ['Nm', 'dyne.cm'],
    'Slip Rate': ['mm/yr', 'm/Myr']
}

DISPLACEMENT_PARAMS = ['AD', 'MD']

# --- Hanks & Kanamori (1979) Conversion Functions ---
def m0_to_mw(m0_val, m0_unit):
    if m0_val is None or m0_unit is None or not isinstance(m0_val, (int, float)) or pd.isna(m0_val): return None
    try:
        m0_in_dyne_cm = convert_units(m0_val, m0_unit, 'dyne.cm')
        if m0_in_dyne_cm <= 0: return None
        return (2/3) * np.log10(m0_in_dyne_cm) - 10.7
    except (ValueError, TypeError): return None

def mw_to_m0(mw_val, target_unit):
    if mw_val is None or target_unit is None or not isinstance(mw_val, (int, float)) or pd.isna(mw_val): return None
    try:
        m0_in_dyne_cm = 10**((mw_val + 10.7) * 1.5)
        return convert_units(m0_in_dyne_cm, 'dyne.cm', target_unit)
    except (ValueError, TypeError): return None

# --- Data Loading Function (cached for performance) ---
@st.cache_data
def load_all_models(models_dir="scaling_models"):
    all_models, canonical_params = {}, set()
    if not os.path.exists(models_dir):
        st.error(f"Models directory not found: '{models_dir}'"); return {}, []
    json_files = [os.path.join(dp, f) for dp, dn, fn in os.walk(models_dir) for f in fn if f.endswith('.json')]
    for file_path in json_files:
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                model_data = json.load(f)
                all_models.update(model_data)
                for paper in model_data.values():
                    for fault in paper['fault_types'].values():
                        for key in fault.keys():
                            y, x = key.split('_from_')
                            canonical_params.add(PARAMETER_ALIASES.get(y, y))
                            canonical_params.add(PARAMETER_ALIASES.get(x, x))
            except Exception as e: st.error(f"Error parsing {file_path}: {e}")
    return all_models, sorted(list(canonical_params))

# --- Main App ---
st.set_page_config(layout="wide", page_title="EQ-Scalculator")
st.title("Earthquake Scaling Relationship Calculator")

st.sidebar.title("Advanced Options")
group_lengths = st.sidebar.toggle("Group L and SRL as 'Length'", value=True)
group_magnitudes = st.sidebar.toggle("Group M₀ and Mw as 'Magnitude'", value=True)

all_models, canonical_params = load_all_models()
if not all_models:
    st.error("No scaling models were loaded."); st.stop()

# --- Helper Functions ---
display_params = list(canonical_params)
if group_lengths:
    display_params = [p for p in display_params if p not in ['L', 'SRL']] + ['Length (L/SRL)']
if group_magnitudes:
    display_params = [p for p in display_params if p not in ['M0', 'Mw']] + ['Magnitude (Mw/M0)']
display_params = sorted(list(set(display_params)))

def get_param_aliases(param):
    if group_lengths and param == 'Length (L/SRL)': return ['L', 'SRL']
    if group_magnitudes and param == 'Magnitude (Mw/M0)': return ['M0', 'Mw']
    return [param]

def find_available_models(input_var, output_var):
    """
    Correctly finds all models that define a relationship between two parameters,
    determining the direction internally without creating confusing "(Inverse)" names.
    """
    models = {}
    input_aliases = get_param_aliases(input_var)
    output_aliases = get_param_aliases(output_var)
    
    for p_name, p_data in all_models.items():
        for f_name, f_data in p_data['fault_types'].items():
            for rk in f_data.keys():
                y, x = rk.split('_from_')
                cy, cx = PARAMETER_ALIASES.get(y, y), PARAMETER_ALIASES.get(x, x)
                
                model_id = f"{p_name} - {f_name}"
                
                # Forward direction: Input matches X, Output matches Y
                if (cx in input_aliases and cy in output_aliases):
                    if group_lengths and cx in ['L', 'SRL']:
                        model_id += f" (from {cx})"
                    models[model_id] = (p_name, f_name, rk, 'forward')
                
                # Inverse direction: Input matches Y, Output matches X
                elif (cy in input_aliases and cx in output_aliases):
                    if group_lengths and cy in ['L', 'SRL']:
                         model_id += f" (from {cy})"
                    models[model_id] = (p_name, f_name, rk, 'inverse')

    if group_magnitudes and set(input_aliases + output_aliases) == {'M0', 'Mw'}:
        models['Hanks & Kanamori (1979) Definition'] = ('virtual', 'virtual', 'virtual', 'virtual')
        
    return models

def get_unit_key(param_name):
    if param_name in UNIT_OPTIONS: return param_name
    return param_name.split(" (")[0]

# --- App Tabs ---
tab1, tab2, tab3 = st.tabs(["Deterministic Calculation", "Monte Carlo Simulation", "Explore Relationships"])

# --- TAB 1: DETERMINISTIC CALCULATION (Unchanged) ---
with tab1:
    st.header("Deterministic Calculation")
    calc_mode_det = st.radio("Calculation Mode", ["Single Input", "File Upload (Batch)"], key="det_mode", horizontal=True)
    st.divider()
    st.subheader("1. Configuration")
    setup_cols = st.columns(4)
    input_var_s = setup_cols[0].selectbox("Input Parameter", display_params, index=0, key="s_in")
    output_var_s = setup_cols[1].selectbox("Output Parameter", display_params, index=1, key="s_out")
    available_models_s = find_available_models(input_var_s, output_var_s)
    selected_model_id_s = setup_cols[2].selectbox("Available Models", list(available_models_s.keys()) if available_models_s else ["No model found"], key="s_mod", disabled=not available_models_s)
    target_output_unit_s = setup_cols[3].selectbox("Output Unit", UNIT_OPTIONS.get(get_unit_key(output_var_s), ['N/A']), key="s_out_unit")
    
    st.divider()
    st.subheader("2. Input Data")
    if calc_mode_det == "Single Input":
        input_cols = st.columns(2)
        input_value_s = input_cols[0].number_input(f"Value for {input_var_s}", format="%.4f", value=6.0, key="s_val")
        input_unit_s = input_cols[1].selectbox("Input Unit", UNIT_OPTIONS.get(get_unit_key(input_var_s), ['N/A']), key="s_unit_single")
    else: # BATCH MODE
        uploaded_file_s = st.file_uploader("Upload a CSV or Excel file", type=['csv', 'xlsx'], key="batch_uploader_s")
        if uploaded_file_s:
            df_peek_s = pd.read_csv(io.StringIO(uploaded_file_s.getvalue().decode('utf-8')), nrows=0) if uploaded_file_s.name.endswith('.csv') else pd.read_excel(uploaded_file_s, nrows=0)
            batch_cols = st.columns(2)
            input_col_s = batch_cols[0].selectbox("Select input column:", df_peek_s.columns, key="b_in_col_s")
            input_unit_s = batch_cols[1].selectbox("Units of input data:", UNIT_OPTIONS.get(get_unit_key(input_var_s), ['N/A']), key="b_unit_s")

    st.divider()
    st.subheader("3. Optional: Recurrence Interval")
    calc_recurrence_s = st.toggle("Calculate Recurrence Interval", help="Requires a displacement output (AD or MD).")
    if calc_recurrence_s:
        if calc_mode_det == "File Upload (Batch)" and 'uploaded_file_s' in locals() and uploaded_file_s:
            rec_cols = st.columns(2)
            slip_rate_col_s = rec_cols[0].selectbox("Slip Rate Column:", [None] + list(df_peek_s.columns), key="s_slip_rate_col")
            if slip_rate_col_s is None:
                fallback_slip_rate_s = rec_cols[0].number_input("Fallback Slip Rate for all rows", value=2.0, format="%.4f")
            slip_rate_unit_s = rec_cols[1].selectbox("Slip Rate Unit (for all rows)", UNIT_OPTIONS['Slip Rate'], key="s_slip_unit_batch")
        else: # SINGLE INPUT MODE
            rec_cols = st.columns(2)
            slip_rate_val_s = rec_cols[0].number_input("Fault Slip Rate", value=2.0, format="%.4f", key="s_slip_rate_single")
            slip_rate_unit_s = rec_cols[1].selectbox("Slip Rate Unit", UNIT_OPTIONS['Slip Rate'], key="s_slip_unit_single")

    st.divider()
    if st.button("Calculate", use_container_width=True, type="primary", key="det_calc_btn", disabled=not available_models_s):
        if calc_mode_det == "Single Input":
            res, res_info, warning_msg = None, "An unknown error occurred.", None
            if selected_model_id_s == 'Hanks & Kanamori (1979) Definition':
                res = m0_to_mw(input_value_s, input_unit_s) if 'M0' in get_param_aliases(input_var_s) else mw_to_m0(input_value_s, 'Nm')
                res_info = None if 'M0' in get_param_aliases(input_var_s) else 'Nm'
            else:
                p, f, rk, d = available_models_s[selected_model_id_s]; rp = all_models[p]['fault_types'][f][rk]
                res, res_info = solve_relationship(rp, input_value_s, input_unit_s, d)
                if res is not None: warning_msg = check_if_extrapolating(rp, input_value_s, input_unit_s, d)
            st.subheader("Result")
            res_cols = st.columns(2)
            final_res, final_unit = None, None
            with res_cols[0]:
                st.markdown("##### Primary Calculation")
                if res is not None:
                    final_res, final_unit = res, res_info
                    if 'Magnitude' in output_var_s and res_info is not None: final_res, final_unit = m0_to_mw(res, res_info), "Mw"
                    elif target_output_unit_s not in ['N/A', None] and res_info is not None: final_res, final_unit = convert_units(res, res_info, target_output_unit_s), target_output_unit_s
                    st.metric(label=f"{output_var_s} ({final_unit or ''})", value=f"{final_res:.4f}")
                    if warning_msg: st.warning(warning_msg)
                else: st.error(f"Calculation failed: {res_info}")
            if calc_recurrence_s and final_res is not None:
                with res_cols[1]:
                    st.markdown("##### Recurrence Interval")
                    if output_var_s not in DISPLACEMENT_PARAMS or slip_rate_val_s <= 0: st.error("Select displacement output & positive slip rate.")
                    else:
                        try:
                            displacement_m = convert_units(final_res, final_unit, 'm')
                            slip_rate_m_per_yr = convert_units(slip_rate_val_s, slip_rate_unit_s, 'm/yr')
                            st.metric(label="Interval (years)", value=f"{displacement_m / slip_rate_m_per_yr:,.0f}")
                        except (ValueError, TypeError, ZeroDivisionError) as e: st.error(f"Error: {e}")
        else: # BATCH LOGIC
            if 'uploaded_file_s' in locals() and uploaded_file_s is not None and 'input_col_s' in locals():
                with st.spinner("Processing batch file..."):
                    df = pd.read_csv(uploaded_file_s) if uploaded_file_s.name.endswith('.csv') else pd.read_excel(uploaded_file_s)
                    output_col_name = f"{output_var_s.replace(' ', '_')}_({target_output_unit_s or 'native'})"
                    def solver(val):
                        if pd.isna(val): return None
                        res, info = None, None
                        if selected_model_id_s == 'Hanks & Kanamori (1979) Definition':
                            res, info = (m0_to_mw(val, input_unit_s), None) if 'M0' in get_param_aliases(input_var_s) else (mw_to_m0(val, 'Nm'), 'Nm')
                        else:
                            p,f,rk,d = available_models_s[selected_model_id_s]; rp = all_models[p]['fault_types'][f][rk]
                            res, info = solve_relationship(rp, val, input_unit_s, d)
                        if res is None: return None
                        if 'Magnitude' in output_var_s and info: res, info = m0_to_mw(res, info), None
                        elif target_output_unit_s not in ['N/A', None] and info: res = convert_units(res, info, target_output_unit_s)
                        return res
                    df[output_col_name] = df[input_col_s].apply(solver)
                    if calc_recurrence_s and output_var_s in DISPLACEMENT_PARAMS:
                        def recurrence_solver(row):
                            displacement = row[output_col_name]
                            if pd.isna(displacement): return None
                            slip_rate = fallback_slip_rate_s if 'slip_rate_col_s' not in locals() or slip_rate_col_s is None else row.get(slip_rate_col_s)
                            if pd.isna(slip_rate) or slip_rate <= 0: return None
                            try:
                                displacement_m = convert_units(displacement, target_output_unit_s, 'm')
                                slip_rate_m_yr = convert_units(slip_rate, slip_rate_unit_s, 'm/yr')
                                return displacement_m / slip_rate_m_yr
                            except (ValueError, TypeError, ZeroDivisionError): return None
                        df['Recurrence_yrs'] = df.apply(recurrence_solver, axis=1)

                    st.success("Batch complete!"); st.dataframe(df)
                    st.download_button("Download Results", df.to_csv(index=False).encode('utf-8'), f"det_results_{uploaded_file_s.name}", 'text/csv')

# --- TAB 2: MONTE CARLO SIMULATION (Updated with Slip Rate Uncertainty) ---
with tab2:
    st.header("Monte Carlo Simulation")
    mc_mode = st.radio("Input Mode", ["Single Mean Input", "File Upload (Batch)"], key="mc_mode", horizontal=True)
    st.divider()
    st.subheader("1. Configuration")
    mc_setup = st.columns(3)
    input_var_mc = mc_setup[0].selectbox("Input Parameter", display_params, index=0, key="mc_in")
    output_var_mc = mc_setup[1].selectbox("Output Parameter", display_params, index=1, key="mc_out")
    target_output_unit_mc = mc_setup[2].selectbox("Output Unit", UNIT_OPTIONS.get(get_unit_key(output_var_mc), ['N/A']), key="mc_out_unit")
    
    st.divider()
    st.subheader("2. Input Data & Simulation Parameters")
    if mc_mode == "Single Mean Input":
        mc_cols1 = st.columns(2)
        input_val_mc = mc_cols1[0].number_input(f"Mean Input Value for {input_var_mc}", value=6.0, format="%.4f", key="mc_val")
        input_unit_mc = mc_cols1[1].selectbox("Input Unit", UNIT_OPTIONS.get(get_unit_key(input_var_mc), ['N/A']), key="mc_unit_single")
        num_simulations = st.number_input("Number of Simulations", 100, 50000, 1000, 100, key="mc_sims")
    else: # BATCH MODE UI
        uploaded_file_mc = st.file_uploader("Upload a CSV or Excel file", type=['csv', 'xlsx'], key="mc_uploader")
        if uploaded_file_mc:
            df_peek_mc = pd.read_csv(io.StringIO(uploaded_file_mc.getvalue().decode('utf-8')), nrows=0) if uploaded_file_mc.name.endswith('.csv') else pd.read_excel(uploaded_file_mc, nrows=0)
            mc_batch_cols = st.columns(3)
            mc_input_col = mc_batch_cols[0].selectbox("Mean Input Value Column:", df_peek_mc.columns, key="mc_in_col")
            input_unit_mc = mc_batch_cols[1].selectbox("Units of Input Data:", UNIT_OPTIONS.get(get_unit_key(input_var_mc), ['N/A']), key="mc_unit_batch")
            num_simulations = mc_batch_cols[2].number_input("Simulations per Row", 100, 10000, 500, 100, key="mc_sims_batch")

    st.divider()
    st.subheader("3. Uncertainty Configuration")
    unc_cols = st.columns(2)
    with unc_cols[0]:
        st.markdown("##### Input Value Uncertainty (Epistemic)")
        if mc_mode == "File Upload (Batch)" and 'uploaded_file_mc' in locals() and uploaded_file_mc:
            unc_col = st.selectbox("Absolute Error (±) Column:", [None] + list(df_peek_mc.columns), key="mc_unc_col", help="Select a column containing the absolute error for each row. If 'None', the fallback percentage will be used.")
            if unc_col is None:
                fallback_unc_pct = st.number_input("Fallback Uncertainty (%) for all rows", value=5.0, min_value=0.0, key="mc_unc_pct_fallback")
        else:
            unc_type_single = st.radio("Type", ('None', 'Absolute Error (±)', 'Percentage (%)'), key="unc_type_single")
            input_uncertainty_single = 0.0
            if unc_type_single == 'Absolute Error (±)': input_uncertainty_single = st.number_input(f"Error (±)", value=0.1, min_value=0.0, format="%.4f", key="unc_abs")
            elif unc_type_single == 'Percentage (%)': input_uncertainty_single = st.number_input("Uncertainty (%)", value=5.0, min_value=0.0, key="unc_pct")
    
    with unc_cols[1]:
        st.markdown("##### Model Uncertainty (Aleatory)")
        include_model_unc = st.toggle("Include Model Regression Uncertainty", value=True)

    st.divider()
    st.subheader("4. Model Selection")
    available_models_mc = find_available_models(input_var_mc, output_var_mc)
    selected_models_mc = st.multiselect("Choose models:", list(available_models_mc.keys()), key="mc_select", default=list(available_models_mc.keys())[0] if available_models_mc else [])
    weights, total_weight = {}, 0
    if selected_models_mc:
        st.markdown("###### Assign Weights (must sum to 100%)")
        weight_cols = st.columns(len(selected_models_mc))
        for i, mid in enumerate(selected_models_mc):
            weights[mid] = weight_cols[i].number_input(f"'{mid.split(' - ')[0]}' (%)", 0, 100, int(100/len(selected_models_mc)), key=f"w_{mid}")
            total_weight += weights[mid]
        st.metric(label="Total Weight", value=f"{total_weight}%")
        if total_weight != 100: st.warning("Total weight must be 100%.")
    
    st.divider()
    st.subheader("5. Optional: Recurrence Interval")
    calc_recurrence_mc = st.toggle("Calculate Recurrence Interval Distribution", help="Requires a displacement output.")
    if calc_recurrence_mc:
        rec_unc_cols = st.columns(2)
        with rec_unc_cols[0]:
            st.markdown("###### Slip Rate Mean")
            if mc_mode == "File Upload (Batch)" and 'uploaded_file_mc' in locals() and uploaded_file_mc:
                slip_rate_col = st.selectbox("Slip Rate Column", [None] + list(df_peek_mc.columns), key="mc_slip_rate_col")
                if slip_rate_col is None: fallback_slip_rate = st.number_input("Fallback Slip Rate", value=2.0)
                mc_slip_rate_unit = st.selectbox("Slip Rate Unit", UNIT_OPTIONS['Slip Rate'], key="mc_slip_unit_batch")
            else:
                mc_slip_rate_val = st.number_input("Fault Slip Rate", value=2.0, format="%.4f", key="mc_slip_rate_single")
                mc_slip_rate_unit = st.selectbox("Slip Rate Unit", UNIT_OPTIONS['Slip Rate'], key="mc_slip_unit_single")
        with rec_unc_cols[1]:
            st.markdown("###### Slip Rate Uncertainty")
            if mc_mode == "File Upload (Batch)" and 'uploaded_file_mc' in locals() and uploaded_file_mc:
                slip_rate_unc_col = st.selectbox("Slip Rate Abs. Error (±) Column", [None] + list(df_peek_mc.columns), key="mc_slip_unc_col")
                if slip_rate_unc_col is None:
                    slip_rate_unc_pct_fallback = st.number_input("Fallback Slip Rate Uncertainty (%)", value=10.0, min_value=0.0)
            else:
                slip_unc_type = st.radio("Type", ('None', 'Absolute Error (±)', 'Percentage (%)'), key="slip_unc_type_single")
                slip_rate_uncertainty = 0.0
                if slip_unc_type == 'Absolute Error (±)': slip_rate_uncertainty = st.number_input("Slip Rate Error (±)", value=0.2, min_value=0.0, format="%.4f", key="slip_unc_abs")
                elif slip_unc_type == 'Percentage (%)': slip_rate_uncertainty = st.number_input("Slip Rate Uncertainty (%)", value=10.0, min_value=0.0, key="slip_unc_pct")
        
    st.divider()
    if st.button("Run Simulation", use_container_width=True, type="primary", key="mc_run", disabled=(total_weight != 100 or not selected_models_mc)):
        def run_mc_for_row(input_val, unc_val, unc_method, slip_rate_val, slip_rate_unit_val, slip_unc_val, slip_unc_method):
            disp_values, rec_values = [], []
            model_ids, model_weights = list(weights.keys()), np.array([w/100.0 for w in weights.values()])
            for _ in range(num_simulations):
                current_input = np.random.normal(loc=input_val, scale=unc_val) if unc_method == 'Absolute' and unc_val > 0 else \
                                np.random.normal(loc=input_val, scale=(unc_val/100.0)*input_val) if unc_method == 'Percentage' and unc_val > 0 else \
                                input_val
                chosen_model_id = np.random.choice(model_ids, p=model_weights)
                res, res_unit = None, None
                if chosen_model_id == 'Hanks & Kanamori (1979) Definition':
                    res, res_unit = (m0_to_mw(current_input, input_unit_mc), None) if 'M0' in get_param_aliases(input_var_mc) else (mw_to_m0(current_input, 'Nm'), 'Nm')
                else:
                    p,f,rk,d = available_models_mc[chosen_model_id]; rp = all_models[p]['fault_types'][f][rk]
                    res, res_unit = solve_one_simulation_run(rp, current_input, input_unit_mc, d, include_model_unc)
                if res is None: continue
                final_res, final_unit = res, res_unit
                if 'Magnitude' in output_var_mc and final_unit is not None: final_res, final_unit = m0_to_mw(res, final_unit), "Mw"
                elif target_output_unit_mc not in ['N/A', None] and final_unit is not None: final_res, final_unit = convert_units(res, final_unit, target_output_unit_mc), target_output_unit_mc
                if final_res is not None: disp_values.append(final_res)
                if calc_recurrence_mc and final_res is not None and slip_rate_val > 0:
                    current_slip_rate = np.random.normal(loc=slip_rate_val, scale=slip_unc_val) if slip_unc_method == 'Absolute' and slip_unc_val > 0 else \
                                        np.random.normal(loc=slip_rate_val, scale=(slip_unc_val/100.0)*slip_rate_val) if slip_unc_method == 'Percentage' and slip_unc_val > 0 else \
                                        slip_rate_val
                    try:
                        disp_m = convert_units(final_res, final_unit if final_unit else target_output_unit_mc, 'm')
                        slip_m_yr = convert_units(current_slip_rate, slip_rate_unit_val, 'm/yr')
                        if slip_m_yr > 0: rec_values.append(disp_m / slip_m_yr)
                    except: continue
            return disp_values, rec_values
        
        with st.spinner("Running simulations..."):
            if mc_mode == "Single Mean Input":
                unc_method = 'Absolute' if unc_type_single == 'Absolute Error (±)' else 'Percentage' if unc_type_single == 'Percentage (%)' else 'None'
                slip_unc_method = 'Absolute' if 'slip_unc_type' in locals() and slip_unc_type == 'Absolute Error (±)' else 'Percentage' if 'slip_unc_type' in locals() and slip_unc_type == 'Percentage (%)' else 'None'
                slip_rate = mc_slip_rate_val if 'mc_slip_rate_val' in locals() else 0
                slip_unit = mc_slip_rate_unit if 'mc_slip_rate_unit' in locals() else None
                slip_unc = slip_rate_uncertainty if 'slip_rate_uncertainty' in locals() else 0
                disp_results, rec_results = run_mc_for_row(input_val_mc, input_uncertainty_single, unc_method, slip_rate, slip_unit, slip_unc, slip_unc_method)
                if not disp_results: st.error("Simulation failed for all runs."); st.stop()
                st.subheader("Simulation Results")
                df1 = pd.DataFrame(disp_results, columns=[output_var_mc])
                df2 = pd.DataFrame(rec_results, columns=["Recurrence (yrs)"]) if rec_results else None
                plot_cols = st.columns(2) if calc_recurrence_mc and rec_results else st.columns(1)
                fig1 = px.histogram(df1, x=output_var_mc, title=f"Distribution of {output_var_mc}")
                plot_cols[0].plotly_chart(fig1, use_container_width=True)
                if df2 is not None and not df2.empty:
                    fig2 = px.histogram(df2, x="Recurrence (yrs)", title="Distribution of Recurrence Interval")
                    plot_cols[1].plotly_chart(fig2, use_container_width=True)
                st.divider()
                st.subheader("Summary Statistics")
                stat_cols = st.columns(2) if df2 is not None and not df2.empty else st.columns(1)
                with stat_cols[0]:
                    st.write(f"**Statistics for {output_var_mc}**")
                    st.dataframe(df1.describe(percentiles=[.16, .5, .84]))
                if df2 is not None and not df2.empty:
                    with stat_cols[1]:
                        st.write(f"**Statistics for Recurrence Interval**")
                        st.dataframe(df2.describe(percentiles=[.16, .5, .84]))
            else: # BATCH MODE LOGIC
                if 'uploaded_file_mc' in locals() and uploaded_file_mc and 'mc_input_col' in locals():
                    df = pd.read_csv(uploaded_file_mc) if uploaded_file_mc.name.endswith('.csv') else pd.read_excel(uploaded_file_mc)
                    results_list = []
                    for idx, row in df.iterrows():
                        val = pd.to_numeric(row[mc_input_col], errors='coerce')
                        if pd.isna(val): continue
                        row_unc_val, row_unc_method = (pd.to_numeric(row.get(unc_col, 0)), 'Absolute') if 'unc_col' in locals() and unc_col and unc_col in row and pd.notna(row[unc_col]) else \
                                                      (fallback_unc_pct, 'Percentage') if 'fallback_unc_pct' in locals() else (0, 'None')
                        row_slip_rate, row_slip_unit, row_slip_unc, row_slip_unc_method = 0, None, 0, 'None'
                        if calc_recurrence_mc:
                            row_slip_unit = mc_slip_rate_unit
                            row_slip_rate = fallback_slip_rate if 'slip_rate_col' not in locals() or slip_rate_col is None else pd.to_numeric(row.get(slip_rate_col, 0))
                            row_slip_unc, row_slip_unc_method = (pd.to_numeric(row.get(slip_rate_unc_col, 0)), 'Absolute') if 'slip_rate_unc_col' in locals() and slip_rate_unc_col and slip_rate_unc_col in row and pd.notna(row[slip_rate_unc_col]) else \
                                                                (slip_rate_unc_pct_fallback, 'Percentage') if 'slip_rate_unc_pct_fallback' in locals() else (0, 'None')
                        disp_res, rec_res = run_mc_for_row(val, row_unc_val, row_unc_method, row_slip_rate, row_slip_unit, row_slip_unc, row_slip_unc_method)
                        res_dict = {'input': val}
                        if disp_res: res_dict.update({f'{output_var_mc}_mean': np.mean(disp_res), f'{output_var_mc}_std': np.std(disp_res)})
                        if rec_res: res_dict.update({'recurrence_mean_yrs': np.mean(rec_res), 'recurrence_std_yrs': np.std(rec_res)})
                        results_list.append(res_dict)
                    if results_list:
                        results_df = pd.DataFrame(results_list)
                        st.success("Batch simulation complete!"); st.dataframe(results_df)
                        st.download_button("Download Summary", results_df.to_csv(index=False).encode('utf-8'), f"mc_results_{uploaded_file_mc.name}",'text/csv')
                    else: st.error("All batch simulations failed.")

# --- TAB 3: EXPLORE RELATIONSHIPS ---
with tab3:
    st.header("Explore and Compare Scaling Relationships")
    plot_cols = st.columns(4)
    x_var = plot_cols[0].selectbox("X-Axis Parameter", display_params, index=0, key="plot_x")
    y_var = plot_cols[1].selectbox("Y-Axis Parameter", display_params, index=1, key="plot_y")
    x_scale = plot_cols[2].selectbox("X-Axis Scale", ["linear", "log"], key="plot_x_scale", index=0)
    y_scale = plot_cols[3].selectbox("Y-Axis Scale", ["linear", "log"], index=1, key="plot_y_scale")
    plot_models = find_available_models(x_var, y_var)
    if not plot_models: st.warning(f"No models found relating **{x_var}** and **{y_var}**.")
    else:
        plot_df = pd.DataFrame()
        standard_units = {'A':'km^2', 'L':'km', 'W':'km', 'SRL':'km', 'AD':'m', 'MD':'m', 'M0':'Nm', 'Length (L/SRL)':'km', 'Magnitude (Mw/M0)':None}
        x_plot_unit, y_plot_unit = standard_units.get(get_unit_key(x_var)), standard_units.get(get_unit_key(y_var))
        if 'Magnitude' in x_var: x_range = np.linspace(4.5, 9.0, 200)
        elif 'M0' in get_param_aliases(x_var): x_range = np.logspace(15, 22, 200)
        else: x_range = np.logspace(-1, 4, 200)
        for mid, (p, f, k, d) in plot_models.items():
            if p == 'virtual': continue
            params = all_models[p]['fault_types'][f][k]
            native_x, native_y = (k.split('_from_')[1], k.split('_from_')[0])
            if d == 'inverse': native_x, native_y = native_y, native_x
            in_range, in_unit = x_range, x_plot_unit
            if group_magnitudes and 'Magnitude' in x_var and PARAMETER_ALIASES.get(native_x) == 'M0':
                native_unit = params[0]['units']['x'] if d == 'forward' else params[0]['units']['y']
                in_range, in_unit = [mw_to_m0(val, native_unit) for val in x_range], native_unit
            y_raw, y_unit_raw = calculate_curve(params, in_range, in_unit, d)
            y_values = []
            if y_unit_raw:
                if group_magnitudes and 'Magnitude' in y_var and PARAMETER_ALIASES.get(native_y) == 'M0':
                    y_values = [m0_to_mw(yv, y_unit_raw) for yv in y_raw]
                elif y_plot_unit:
                    try: y_values = [convert_units(yv, y_unit_raw, y_plot_unit) if yv is not None else None for yv in y_raw]
                    except ValueError: continue
                else: y_values = y_raw
            if y_values:
                temp_df = pd.DataFrame({'x_val': x_range, 'y_val': y_values, 'Model': mid})
                plot_df = pd.concat([plot_df, temp_df])
        plot_df.dropna(inplace=True)
        if not plot_df.empty:
            final_y_unit = None if (group_magnitudes and 'Magnitude' in y_var) else y_plot_unit
            final_x_unit = None if (group_magnitudes and 'Magnitude' in x_var) else x_plot_unit
            fig = px.line(plot_df, x='x_val', y='y_val', color='Model', log_x=(x_scale=='log'), log_y=(y_scale=='log'),
                          labels={'x_val':f"{x_var} ({final_x_unit or ''})", 'y_val':f"{y_var} ({final_y_unit or ''})"},
                          title=f"Comparison of {y_var} vs. {x_var}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Could not generate plot data for the selected models.")

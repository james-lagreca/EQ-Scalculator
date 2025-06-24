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

# --- Simplified Unit Options Dictionary ---
UNIT_OPTIONS = {
    # Grouped
    'Length (L/SRL)': ['km', 'm'],
    'Magnitude (Mw/M0)': ['N/A'],
    # Ungrouped Area/Length
    'A': ['km^2', 'm^2'],
    'L': ['km', 'm'],
    'W': ['km', 'm'],
    'SRL': ['km', 'm'],
    # Ungrouped Slip (default to meters)
    'AD': ['m'],
    'MD': ['m'],
    # Ungrouped Magnitude/Moment
    'Mw': ['N/A'],
    'M0': ['Nm', 'dyne.cm'],
}

# --- Hanks & Kanamori (1979) Conversion Functions ---
def m0_to_mw(m0_val, m0_unit):
    """Converts Seismic Moment (M0) to Moment Magnitude (Mw)."""
    if m0_val is None or m0_unit is None or not isinstance(m0_val, (int, float)): return None
    try:
        m0_in_dyne_cm = convert_units(m0_val, m0_unit, 'dyne.cm')
        if m0_in_dyne_cm <= 0: return None
        return (2/3) * np.log10(m0_in_dyne_cm) - 10.7
    except (ValueError, TypeError):
        return None

def mw_to_m0(mw_val, target_unit):
    """Converts Moment Magnitude (Mw) to Seismic Moment (M0) in the target unit."""
    if mw_val is None or target_unit is None or not isinstance(mw_val, (int, float)): return None
    try:
        m0_in_dyne_cm = 10**((mw_val + 10.7) * 1.5)
        return convert_units(m0_in_dyne_cm, 'dyne.cm', target_unit)
    except (ValueError, TypeError):
        return None

# --- Data Loading Function (cached for performance) ---
@st.cache_data
def load_all_models(models_dir="scaling_models"):
    all_models, canonical_params = {}, set()
    if not os.path.exists(models_dir):
        st.error(f"Models directory not found: '{models_dir}'")
        return {}, []
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
                            for paper in model_data.values():
                                for fault in paper['fault_types'].values():
                                    for key in fault.keys():
                                        y, x = key.split('_from_')
                                        canonical_params.add(PARAMETER_ALIASES.get(y, y))
                                        canonical_params.add(PARAMETER_ALIASES.get(x, x))
                        except Exception as e:
                            st.error(f"Error parsing {file_path}: {e}")
    return all_models, sorted(list(canonical_params))

# --- Main App ---
st.set_page_config(layout="wide", page_title="EQ-Scalculator")
st.title("Earthquake Scaling Relationship Calculator")

st.sidebar.title("Advanced Options")
group_lengths = st.sidebar.toggle("Group L and SRL as 'Length'", value=True, help="When ON, treats subsurface (L) and surface (SRL) length as one category for comparison.")
group_magnitudes = st.sidebar.toggle("Group M₀ and Mw as 'Magnitude'", value=True, help="When ON, treats M₀ and Mw as one category, converting between them automatically.")

all_models, canonical_params = load_all_models()
if not all_models:
    st.error("No scaling models were loaded.")
    st.stop()

display_params = list(canonical_params)
if group_lengths:
    display_params = [p for p in display_params if p not in ['L', 'SRL']]
    if 'Length (L/SRL)' not in display_params: display_params.insert(0, 'Length (L/SRL)')
if group_magnitudes:
    display_params = [p for p in display_params if p not in ['M0', 'Mw']]
    if 'Magnitude (Mw/M0)' not in display_params: display_params.insert(0, 'Magnitude (Mw/M0)')

def get_param_aliases(param):
    if group_lengths and param == 'Length (L/SRL)': return ['L', 'SRL']
    if group_magnitudes and param == 'Magnitude (Mw/M0)': return ['M0', 'Mw']
    return [param]

def find_available_models(input_var, output_var):
    models = {}
    input_aliases = get_param_aliases(input_var)
    output_aliases = get_param_aliases(output_var)
    for p_name, p_data in all_models.items():
        for f_name, f_data in p_data['fault_types'].items():
            for rk in f_data:
                y, x = rk.split('_from_'); cy, cx = PARAMETER_ALIASES.get(y,y), PARAMETER_ALIASES.get(x,x)
                
                model_id = f"{p_name} - {f_name}"
                if group_lengths and (cx in ['L', 'SRL']):
                    model_id += f" (from {cx})"
                
                if (cx in input_aliases and cy in output_aliases):
                    models[model_id] = (p_name, f_name, rk, 'forward')
                elif (cy in input_aliases and cx in output_aliases):
                    models[model_id] = (p_name, f_name, rk, 'inverse')

    if group_magnitudes and set(input_aliases + output_aliases) == {'M0', 'Mw'}:
        models['Hanks & Kanamori (1979) Definition'] = ('virtual', 'virtual', 'virtual', 'virtual')
    
    return models

tab1, tab2, tab3, tab4 = st.tabs(["Single Calculation", "Batch Processing", "Monte Carlo Simulation", "Explore Relationships"])

# --- TAB 1: SINGLE CALCULATION (with EXTRAPOLATION WARNING) ---
with tab1:
    st.header("Single Parameter Calculation")
    setup_cols = st.columns([2, 2, 3, 3])
    with setup_cols[0]:
        input_var_s = st.selectbox("Input Parameter", display_params, index=display_params.index('Magnitude (Mw/M0)') if 'Magnitude (Mw/M0)' in display_params else 0, key="s_in")
        input_value_s = st.number_input(f"Value for {input_var_s}", format="%.4f", value=6.0, key="s_val")

    with setup_cols[1]:
        output_var_s = st.selectbox("Output Parameter", display_params, index=display_params.index('Length (L/SRL)') if group_lengths and 'Length (L/SRL)' in display_params else (display_params.index('SRL') if not group_lengths and 'SRL' in display_params else 1), key="s_out")
        output_unit_options_s = UNIT_OPTIONS.get(output_var_s, ['N/A'])
        if len(output_unit_options_s) > 1:
            target_output_unit_s = st.selectbox("Output Unit", output_unit_options_s, key="s_out_unit")
        else:
            target_output_unit_s = output_unit_options_s[0]
            st.text_input("Output Unit", value=target_output_unit_s, disabled=True, key="s_out_unit_dis")

    available_models_s = find_available_models(input_var_s, output_var_s)
    
    with setup_cols[2]:
        selected_model_id_s = None
        if available_models_s:
            selected_model_id_s = st.selectbox("Available Models", list(available_models_s.keys()), key="s_mod")
        else:
            st.warning("No model found.")
    
    with setup_cols[3]:
        temp_param_for_units = input_var_s.split(" ")[0]
        c_in_unit = PARAMETER_ALIASES.get(temp_param_for_units, temp_param_for_units)
        if 'A' in c_in_unit: uo = ['km^2', 'm^2']
        elif any(c in c_in_unit for c in ['L','W','D','SRL']): uo = ['km', 'm']
        elif 'M0' in c_in_unit or 'Magnitude' in temp_param_for_units: uo = ['Nm', 'dyne.cm'] if 'M0' in get_param_aliases(input_var_s) else ['N/A']
        else: uo = ['N/A']
        input_unit_s = st.selectbox("Input Unit", uo, key="s_unit")
        if input_unit_s == 'N/A': input_unit_s = None
    
    st.divider()

    if selected_model_id_s:
        rc = st.columns([1,2])
        is_hk_model = selected_model_id_s == 'Hanks & Kanamori (1979) Definition'
        
        with rc[0]:
            st.subheader("Result")
            if st.button("Calculate", use_container_width=True, type="primary", key="s_calc"):
                res, res_info = None, "An unknown error occurred."
                warning_msg = None
                
                if is_hk_model:
                    is_m0_input = 'M0' in get_param_aliases(input_var_s)
                    res = m0_to_mw(input_value_s, input_unit_s) if is_m0_input else mw_to_m0(input_value_s, 'Nm')
                    res_info = None if is_m0_input else 'Nm'
                else:
                    p, f, rk, d = available_models_s[selected_model_id_s]
                    rp = all_models[p]['fault_types'][f][rk]
                    
                    input_val_for_solver = input_value_s
                    input_unit_for_solver = input_unit_s
                    native_x_param = rk.split('_from_')[1] if d == 'forward' else rk.split('_from_')[0]
                    if group_magnitudes and 'Magnitude' in input_var_s and PARAMETER_ALIASES.get(native_x_param) == 'M0':
                        native_unit = rp[0]['units']['x'] if d == 'forward' else rp[0]['units']['y']
                        input_val_for_solver = mw_to_m0(input_value_s, native_unit)
                        input_unit_for_solver = native_unit
                    
                    # --- MODIFIED: Call solver and extrapolation check separately ---
                    res, res_info = solve_relationship(rp, input_val_for_solver, input_unit_for_solver, d)
                    if res is not None:
                         warning_msg = check_if_extrapolating(rp, input_val_for_solver, input_unit_for_solver, d)
                    # --- END MODIFIED ---
                
                if res is not None:
                    res_u = res_info
                    if group_magnitudes and 'Magnitude' in output_var_s and res is not None and res_u is not None:
                        res = m0_to_mw(res, res_u)
                        res_u = None

                    final_res, final_unit = res, res_u
                    if target_output_unit_s != 'N/A' and res_u is not None:
                        try:
                            final_res = convert_units(res, res_u, target_output_unit_s)
                            final_unit = target_output_unit_s
                        except ValueError as e:
                            st.error(f"Unit conversion failed: {e}")
                            final_res = None
                    
                    if final_res is not None:
                        st.metric(label=f"{output_var_s} ({final_unit or ''})", value=f"{final_res:.4f}")
                        if warning_msg:
                            st.warning(warning_msg)
                else: 
                    st.error(f"Calculation failed: {res_info}")

        with rc[1]:
            st.subheader("Model Details")
            if is_hk_model:
                st.markdown("**Model:** `Hanks & Kanamori (1979)`\n\n**Type:** `Definitional Conversion`")
            else:
                p, f, rk, d = available_models_s[selected_model_id_s]
                st.markdown(f"**Model:** `{p}`\n\n**Fault Type:** `{f}`\n\n**Relationship:** `{rk}`")
                with st.expander("Show Raw Parameters"): st.json(all_models[p]['fault_types'][f][rk])

# --- TAB 2: BATCH PROCESSING ---
with tab2:
    st.header("Batch Processing from a File")
    # This tab is intentionally left unmodified as the user requested changes for single calculations.
    # The solver changes will allow extrapolation, but warnings are not added here.
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=['csv', 'xlsx'], key="batch_uploader")
    if uploaded_file:
        try:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            st.dataframe(df.head())
            
            st.markdown("---"); st.markdown("##### Configuration")
            b_cols = st.columns(4)
            with b_cols[0]:
                input_col = st.selectbox("Select input column:", df.columns, key="b_in_col")
            with b_cols[1]:
                input_var_b = st.selectbox("Input parameter type:", display_params, index=display_params.index('Magnitude (Mw/M0)') if 'Magnitude (Mw/M0)' in display_params else 0, key="b_in_var")
            with b_cols[2]:
                output_var_b = st.selectbox("Output parameter to calculate:", display_params, index=display_params.index('Length (L/SRL)') if 'Length (L/SRL)' in display_params else 1, key="b_out_var")
            with b_cols[3]:
                output_unit_options_b = UNIT_OPTIONS.get(output_var_b, ['N/A'])
                if len(output_unit_options_b) > 1:
                    target_output_unit_b = st.selectbox("Desired Output Unit", output_unit_options_b, key="b_out_unit")
                else:
                    target_output_unit_b = output_unit_options_b[0]
                    st.text_input("Output Unit", value=target_output_unit_b, disabled=True, key="b_out_unit_dis")

            temp_param_b = input_var_b.split(" ")[0]; c_in_unit_b = PARAMETER_ALIASES.get(temp_param_b, temp_param_b)
            if 'A' in c_in_unit_b: uo_b = ['km^2', 'm^2']
            elif any(c in c_in_unit_b for c in ['L','W','D','SRL']): uo_b = ['km', 'm']
            elif 'M0' in c_in_unit_b or 'Magnitude' in temp_param_b: uo_b = ['Nm', 'dyne.cm'] if 'M0' in get_param_aliases(input_var_b) else ['N/A']
            else: uo_b = ['N/A']
            input_unit_b = st.selectbox("Input data units:", uo_b, key="b_unit")
            if input_unit_b == 'N/A': input_unit_b = None
            
            available_models_b = find_available_models(input_var_b, output_var_b)
            selected_model_id_b = st.selectbox("Select model to apply:", list(available_models_b.keys()), key="b_model") if available_models_b else None
            
            if st.button("Process Batch File", disabled=(not selected_model_id_b), type="primary", key="b_proc_btn"):
                with st.spinner("Calculating..."):
                    output_unit_suffix = f"_{target_output_unit_b}".replace("^","") if target_output_unit_b != 'N/A' else ''
                    output_col_name = f"{output_var_b.split(' ')[0]}{output_unit_suffix}"
                    
                    if selected_model_id_b == 'Hanks & Kanamori (1979) Definition':
                        is_m0_input = 'M0' in get_param_aliases(input_var_b)
                        df[output_col_name] = df[input_col].apply(lambda x: m0_to_mw(pd.to_numeric(x, errors='coerce'), input_unit_b) if is_m0_input else mw_to_m0(pd.to_numeric(x, errors='coerce'), target_output_unit_b))
                    else:
                        p, f, rk, d = available_models_b[selected_model_id_b]; rp = all_models[p]['fault_types'][f][rk]
                        
                        def batch_solver(row_val):
                            val = pd.to_numeric(row_val, errors='coerce')
                            if pd.isna(val): return None
                            
                            native_x_param = rk.split('_from_')[1] if d == 'forward' else rk.split('_from_')[0]
                            val_for_solver, unit_for_solver = val, input_unit_b
                            if group_magnitudes and 'Magnitude' in input_var_b and PARAMETER_ALIASES.get(native_x_param) == 'M0':
                                native_unit = rp[0]['units']['x'] if d == 'forward' else rp[0]['units']['y']
                                val_for_solver = mw_to_m0(val, native_unit)
                                unit_for_solver = native_unit
                                if val_for_solver is None: return None
                            
                            res, res_u = solve_relationship(rp, val_for_solver, unit_for_solver, d)
                            
                            if res is None: return None

                            if group_magnitudes and 'Magnitude' in output_var_b and res is not None and res_u is not None:
                                res = m0_to_mw(res, res_u)
                                res_u = None
                            
                            if res is not None and target_output_unit_b != 'N/A' and res_u is not None:
                                try:
                                    return convert_units(res, res_u, target_output_unit_b)
                                except (ValueError, TypeError):
                                    return None
                            
                            return res

                        df[output_col_name] = df[input_col].apply(batch_solver)
                        
                    st.success("Batch processing complete!"); st.dataframe(df)
                    st.download_button("Download Results as CSV", df.to_csv(index=False).encode('utf-8'), f"results_{uploaded_file.name}", 'text/csv')
        except Exception as e:
            st.error(f"An error occurred: {e}")

# --- TAB 3: MONTE CARLO SIMULATION ---
with tab3:
    st.header("Monte Carlo Simulation")
    # This tab is intentionally left unmodified. The solver changes will allow extrapolation.
    mc_setup = st.columns(3)
    with mc_setup[0]:
        input_var_mc = st.selectbox("Input Parameter", display_params, index=display_params.index('Magnitude (Mw/M0)') if 'Magnitude (Mw/M0)' in display_params else 0, key="mc_in")
        input_val_mc = st.number_input(f"Mean Input Value for {input_var_mc}", value=6.0, format="%.4f", key="mc_val")
    with mc_setup[1]:
        output_var_mc = st.selectbox("Output Parameter", display_params, index=display_params.index('A') if 'A' in display_params else 1, key="mc_out")
        output_unit_options_mc = UNIT_OPTIONS.get(output_var_mc, ['N/A'])
        if len(output_unit_options_mc) > 1:
            target_output_unit_mc = st.selectbox("Output Unit", output_unit_options_mc, key="mc_out_unit")
        else:
            target_output_unit_mc = output_unit_options_mc[0]
            st.text_input("Output Unit", value=target_output_unit_mc, disabled=True, key="mc_out_unit_dis")
    with mc_setup[2]:
        num_simulations = st.number_input("Number of Simulations", 100, 50000, 10000, 100, key="mc_sims")
        temp_param_mc = input_var_mc.split(" ")[0]; c_in_unit_mc = PARAMETER_ALIASES.get(temp_param_mc, temp_param_mc)
        if 'A' in c_in_unit_mc: uo_mc = ['km^2', 'm^2']
        elif any(c in c_in_unit_mc for c in ['L','W','D','SRL']): uo_mc = ['km', 'm']
        elif 'M0' in c_in_unit_mc or 'Magnitude' in temp_param_mc: uo_mc = ['Nm', 'dyne.cm'] if 'M0' in get_param_aliases(input_var_mc) else ['N/A']
        else: uo_mc = ['N/A']
        input_unit_mc = st.selectbox("Input Unit", uo_mc, key="mc_unit")
        if input_unit_mc == 'N/A': input_unit_mc = None

    st.markdown("---")
    st.markdown("##### Add Uncertainty to Input Value (Optional)")
    unc_type = st.radio("Input Uncertainty Type", ('None', 'Standard Deviation', 'Percentage (%)'), horizontal=True, key="unc_type")
    input_uncertainty = 0.0
    if unc_type == 'Standard Deviation':
        input_uncertainty = st.number_input("Input Standard Deviation", value=0.1, format="%.4f", key="unc_std")
    elif unc_type == 'Percentage (%)':
        input_uncertainty = st.number_input("Input Uncertainty (%)", value=5.0, min_value=0.0, max_value=100.0, key="unc_pct")
    
    st.markdown("---")
    st.markdown("##### Select and Weight Models for Simulation")
    available_models_mc = find_available_models(input_var_mc, output_var_mc)
    
    if not available_models_mc:
        st.warning(f"No models found for the pair **{input_var_mc}** and **{output_var_mc}**.")
    else:
        selected_models = st.multiselect("Choose models to include in simulation:", list(available_models_mc.keys()), key="mc_select")
        weights, total_weight = {}, 0
        if selected_models:
            st.markdown("###### Assign Weights (must sum to 100)")
            weight_cols = st.columns(len(selected_models))
            for i, model_id in enumerate(selected_models):
                with weight_cols[i]:
                    help_txt = "Definitional, no aleatory uncertainty."
                    if model_id != 'Hanks & Kanamori (1979) Definition':
                        p, f, rk, d = available_models_mc[model_id]; rp = all_models[p]['fault_types'][f][rk]
                        has_unc = rp[0].get('std_dev_a') or rp[0].get('log10_y_std_dev')
                        help_txt = "Includes aleatory uncertainty." if has_unc else "Deterministic."
                    weights[model_id] = st.number_input(f"{model_id} (%)", 0, 100, int(100/len(selected_models)), key=f"w_{model_id}", help=help_txt)
                    total_weight += weights[model_id]
            st.metric(label="Total Weight", value=f"{total_weight}%")
            if total_weight != 100: st.warning("Total weight must be 100%.")
        
        st.markdown("---")
        if st.button("Run Simulation", disabled=(total_weight != 100 or not selected_models), type="primary", key="mc_run"):
            with st.spinner(f"Running {num_simulations} simulations..."):
                all_results = []
                model_ids, model_weights = list(weights.keys()), np.array([w/100.0 for w in weights.values()])
                for _ in range(num_simulations):
                    current_input = input_val_mc
                    if unc_type == 'Standard Deviation': current_input = np.random.normal(loc=input_val_mc, scale=input_uncertainty)
                    elif unc_type == 'Percentage (%)': current_input = np.random.normal(loc=input_val_mc, scale=(input_uncertainty/100.0)*input_val_mc)
                    chosen_model_id = np.random.choice(model_ids, p=model_weights)
                    
                    result, result_unit = None, None
                    if chosen_model_id == 'Hanks & Kanamori (1979) Definition':
                        is_m0_input = 'M0' in get_param_aliases(input_var_mc)
                        result = m0_to_mw(current_input, input_unit_mc) if is_m0_input else mw_to_m0(current_input, target_output_unit_mc)
                        result_unit = None if is_m0_input else target_output_unit_mc
                    else:
                        p, f, rk, d = available_models_mc[chosen_model_id]; rp = all_models[p]['fault_types'][f][rk]
                        result, result_unit = solve_one_simulation_run(rp, current_input, input_unit_mc, d)
                    
                    if result is None: continue

                    if group_magnitudes and 'Magnitude' in output_var_mc and result is not None and result_unit is not None:
                        result = m0_to_mw(result, result_unit)
                        result_unit = None

                    final_result = result
                    if result is not None and target_output_unit_mc != 'N/A' and result_unit is not None:
                        try:
                            final_result = convert_units(result, result_unit, target_output_unit_mc)
                        except (ValueError, TypeError):
                            final_result = None
                    
                    if final_result is not None: 
                        all_results.append(final_result)
                
                if all_results:
                    st.success("Simulation complete!")
                    output_label = f"{output_var_mc} ({target_output_unit_mc})" if target_output_unit_mc != 'N/A' else output_var_mc
                    results_df = pd.DataFrame(all_results, columns=[output_label])
                    fig = px.histogram(results_df, x=output_label, nbins=100, title=f"Distribution of {output_label}")
                    st.plotly_chart(fig, use_container_width=True)
                    st.subheader("Summary Statistics"); stat_cols = st.columns(4)
                    stat_cols[0].metric("Mean", f"{results_df[output_label].mean():.3f}")
                    stat_cols[1].metric("Std. Dev.", f"{results_df[output_label].std():.3f}")
                    stat_cols[2].metric("16th Percentile", f"{results_df[output_label].quantile(0.16):.3f}")
                    stat_cols[3].metric("84th Percentile", f"{results_df[output_label].quantile(0.84):.3f}")
                else:
                    st.error(f"Simulation failed. All {num_simulations} runs resulted in an error.")

# --- TAB 4: EXPLORE RELATIONSHIPS ---
with tab4:
    st.header("Explore and Compare Scaling Relationships")
    plot_cols = st.columns(4)
    with plot_cols[0]: x_var = st.selectbox("X-Axis Parameter", display_params, index=display_params.index('Magnitude (Mw/M0)') if 'Magnitude (Mw/M0)' in display_params else 0, key="plot_x")
    with plot_cols[1]: y_var = st.selectbox("Y-Axis Parameter", display_params, index=display_params.index('Length (L/SRL)') if 'Length (L/SRL)' in display_params else 1, key="plot_y")
    with plot_cols[2]: x_scale = st.selectbox("X-Axis Scale", ["linear", "log"], key="plot_x_scale")
    with plot_cols[3]: y_scale = st.selectbox("Y-Axis Scale", ["linear", "log"], index=1, key="plot_y_scale")
    
    plot_models = find_available_models(x_var, y_var)
    
    if not plot_models: st.warning(f"No models found relating **{x_var}** and **{y_var}**.")
    else:
        plot_df = pd.DataFrame()
        standard_units = {'A':'km^2', 'L':'km', 'W':'km', 'SRL':'km', 'AD':'m', 'MD':'m', 'M0':'Nm', 'Length (L/SRL)':'km', 'Magnitude (Mw/M0)':None}
        
        x_plot_unit = standard_units.get(x_var.split(" ")[0])
        y_plot_unit = standard_units.get(y_var)
        
        temp_x_var_for_range = x_var.split(" ")[0]
        if 'Magnitude' in temp_x_var_for_range:
            x_range = np.linspace(4.5, 9.0, 200)
            x_plot_unit = None
        elif 'M0' in get_param_aliases(x_var):
             x_range = np.logspace(15, 22, 200)
             x_plot_unit = 'Nm'
        else: # Covers Area and Length parameters
            x_range = np.logspace(-1, 4, 200) 
            x_plot_unit = standard_units.get(x_var) if x_var != 'Length (L/SRL)' else 'km'

        for mid, (p, f, k, d) in plot_models.items():
            y_values = []
            if p == 'virtual':
                x_is_mw = 'Mw' in get_param_aliases(x_var)
                y_values = [mw_to_m0(val, 'Nm') for val in x_range] if x_is_mw else [m0_to_mw(val, x_plot_unit) for val in x_range]
            else:
                params = all_models[p]['fault_types'][f][k]
                native_x_param, native_y_param = (k.split('_from_')[1], k.split('_from_')[0])
                if d == 'inverse': native_x_param, native_y_param = native_y_param, native_x_param
                
                input_range_for_calc = x_range
                input_unit_for_calc = x_plot_unit
                if group_magnitudes and 'Magnitude' in x_var and PARAMETER_ALIASES.get(native_x_param) == 'M0':
                    native_unit = params[0]['units']['x'] if d == 'forward' else params[0]['units']['y']
                    input_range_for_calc = [mw_to_m0(val, native_unit) for val in x_range]
                    input_unit_for_calc = native_unit
                
                y_vals_raw, y_unit_raw = calculate_curve(params, input_range_for_calc, input_unit_for_calc, d)
                
                y_values_converted = [convert_units(yv, y_unit_raw, y_plot_unit) if yv is not None and y_plot_unit and y_unit_raw else yv for yv in y_vals_raw]

                if group_magnitudes and 'Magnitude' in y_var and PARAMETER_ALIASES.get(native_y_param) == 'M0':
                    y_values = [m0_to_mw(yv, y_unit_raw) for yv in y_vals_raw]
                else:
                    y_values = y_values_converted

            temp_df = pd.DataFrame({'x_val': x_range, 'y_val': y_values, 'Model': mid})
            plot_df = pd.concat([plot_df, temp_df])
        
        plot_df.dropna(inplace=True)
        if not plot_df.empty:
            final_y_unit = None if group_magnitudes and 'Magnitude' in y_var else y_plot_unit
            final_x_unit = None if group_magnitudes and 'Magnitude' in x_var else x_plot_unit
            fig = px.line(plot_df, x='x_val', y='y_val', color='Model', log_x=(x_scale=='log'), log_y=(y_scale=='log'), labels={'x_val':f"{x_var} ({final_x_unit or ''})", 'y_val':f"{y_var} ({final_y_unit or ''})"}, title=f"Comparison of {y_var} vs. {x_var}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Could not generate plot data for the selected models and range.")


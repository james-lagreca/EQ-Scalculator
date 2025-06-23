import pandas as pd, numpy as np, json, math
import plotly.express as px

def run_solver(model, fault, driver_code, value, outputs, code_map):
    res = {}
    for lbl in outputs:
        tgt_code, tag = code_map[lbl]
        try:
            v = model.solve(driver_code, value, tgt_code, fault_type=fault)
            if tag == "x16": v /= 1e16
            res[lbl] = v
        except NotImplementedError:
            res[lbl] = np.nan
    return res

def df_to_download(df, label):
    return df.to_csv(index=False).encode(), f"{label}.csv"

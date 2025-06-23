import streamlit as st, importlib, pkgutil, pandas as pd, numpy as np
import plotly.express as px
import scaling_models as sm
from app_utils import run_solver, df_to_download
from scaling_models._core import helpers as hp

st.set_page_config("Scalculator", "🌐", layout="wide")
st.title("🧮  Scalculator")


def discover_models():
    mods = {}
    for info in pkgutil.iter_modules(sm.__path__):
        name = info.name
        if name.startswith(("test", "_")):      # skip helpers & tests
            continue
        mod = importlib.import_module(f"{sm.__name__}.{name}")
        if hasattr(mod, "MODELS"):              # keep only real paper wrappers
            mods[name] = mod
    return mods

MODELS = discover_models()   # ← call the function (delete the old one-liner)

# ── driver/outputs dict (label → (code, tag)) ───────────────────
code_map = {
    "Length (km)"            : ("L",  "km"),
    "Width (km)"             : ("W",  "km"),
    "Area (km²)"             : ("A",  "km²"),
    "Displacement (m)"       : ("D",  "m"),
    "Mw"                     : ("Mw", ""),
    "Moment (M0, ×10¹⁶ N·m)" : ("M0", "x16"),
}

# ── create tabs ─────────────────────────────────────────────────
tab_single, tab_batch, tab_mc, tab_plot = st.tabs(
    ["Scalculator", "Batch (Excel)", "Monte-Carlo", "Scaling Plots"]
)

# =================================================================
#  TAB 1  –  SINGLE-RUN
# =================================================================
with tab_single:
    st.header("Single calculation")

    paper   = st.selectbox("Paper", list(MODELS), key="s_paper")
    model   = MODELS[paper]
    fault   = st.selectbox("Fault type", list(model.MODELS), key="s_fault")

    value   = st.number_input("Input value", 0.0, format="%.3f", key="s_val")
    driver  = st.selectbox("Driver", list(code_map), key="s_drv")
    outputs = st.multiselect("Outputs", list(code_map),
                             default=list(code_map), key="s_out")

    if st.button("Compute", key="s_btn"):
        res = run_solver(model, fault, code_map[driver][0],
                         value, outputs, code_map)
        df = pd.DataFrame([res])
        st.dataframe(df.style.format(precision=4, na_rep="N/A"),
                     use_container_width=True)

        csv, name = df_to_download(df, "single_results")
        st.download_button("Download CSV", csv, name, use_container_width=True)

        st.caption(model.metadata(fault)["citation"])

# =================================================================
#  TAB 2  –  BATCH / EXCEL
# =================================================================
with tab_batch:
    st.header("Batch processing")

    paper  = st.selectbox("Paper", list(MODELS), key="b_paper")
    model  = MODELS[paper]
    fault  = st.selectbox("Fault type", list(model.MODELS), key="b_fault")

    uploaded   = st.file_uploader("Upload .xlsx or .csv", type=["xlsx","csv"])
    driver_col = st.text_input("Column with driver values", "Length", key="b_col")
    driver_par = st.selectbox("Driver parameter", list(code_map), key="b_drv")

    if uploaded and st.button("Run batch", key="b_btn"):
        df_in = (pd.read_csv(uploaded)
                 if uploaded.name.endswith(".csv")
                 else pd.read_excel(uploaded))

        rows = [run_solver(model, fault, code_map[driver_par][0],
                           row[driver_col], list(code_map), code_map)
                for _, row in df_in.iterrows()]
        df_out = pd.concat([df_in, pd.DataFrame(rows)], axis=1)
        st.dataframe(df_out, use_container_width=True)

        csv, name = df_to_download(df_out, "batch_results")
        st.download_button("Download results", csv, name,
                           use_container_width=True)

# =================================================================
#  TAB 3  –  MONTE-CARLO
# =================================================================
with tab_mc:
    st.header("Monte-Carlo exploration")

    paper  = st.selectbox("Paper", list(MODELS), key="m_paper")
    model  = MODELS[paper]
    fault  = st.selectbox("Fault type", list(model.MODELS), key="m_fault")

    mc_driver = st.selectbox("Driver", list(code_map), key="m_drv")
    μ         = st.number_input("Mean value", 0.0, format="%.3f", key="m_mu")
    σ         = st.number_input("Std-dev",  0.0, format="%.3f", key="m_sigma")
    N         = st.number_input("Simulations", 1000, step=100, key="m_N")
    outs_mc   = st.multiselect("Outputs", list(code_map),
                               default=list(code_map), key="m_out")

    if st.button("Run MC", key="m_btn"):
        vals = np.random.normal(μ, σ, int(N))
        data = [run_solver(model, fault, code_map[mc_driver][0],
                           v, outs_mc, code_map) for v in vals]
        df_mc = pd.DataFrame(data)

        st.write("Mean ± 1 σ")
        st.write(df_mc.agg(['mean', 'std']).transpose())

        for lbl in outs_mc:
            fig = px.histogram(df_mc, x=lbl, nbins=40,
                               title=f"Distribution of {lbl}")
            st.plotly_chart(fig, use_container_width=True)

# =================================================================
# TAB-4 – MULTI-PANEL  SCALING-RELATIONSHIP VIEWER
# =================================================================
with tab_plot:
    st.header("Scaling-relationship viewer")

    # ---------- tiny helpers ------------------------------------
    def _mask(arr, lo, hi):
        m_lo = np.ones_like(arr, bool) if lo is None else (arr >= lo)
        m_hi = np.ones_like(arr, bool) if hi is None else (arr <  hi)
        return m_lo & m_hi

    units = dict(A="km²", L="km", W="km", D="m", Mw="Mw", M0="N·m")

    # driver grids
    base_km = np.geomspace(0.05, 700, 300)   # L, W, A
    base_D  = np.linspace(0.01, 20, 250)     # Displacement
    base_Mw = np.linspace(4.0, 9.0, 250)     # Mw axis

    def grid_for(tok):
        return base_D  if tok == "D" else base_km

    # ---------- 1. harvest every family label -------------------
    fams = set()
    for mdl in MODELS.values():
        for cfg in mdl.MODELS.values():
            fams.update(
                f"{p.split('-')[0][3:]}–{p.split('-')[1][3:]}"
                for p in cfg["segments"]
            )
            for k in cfg["mw_relations"]:
                if k.startswith("Mw_log"):
                    drv = k[6:]
                    if len(drv) > 3:                       # guard
                        fams.add(f"Mw–{drv[3:]}")
                elif k.endswith(("_Mw", "-Mw")):
                    drv = k.split("_Mw")[0].split("-Mw")[0]
                    if len(drv) > 3:
                        fams.add(f"Mw–{drv[3:]}")
    fams = sorted(fams)

    if not fams:
        st.info("No relations to plot."); st.stop()

    # ---------- 2. colour & legend bookkeeping ------------------
    colour_iter = iter(px.colors.qualitative.Plotly)
    colour_map, legend_once = {}, set()
    subplot_traces = {fam: [] for fam in fams}

    # ---------- 3. build traces for every paper · fault ---------
    for paper_key, mdl in MODELS.items():
        for fault_key, cfg in mdl.MODELS.items():
            label = f"{paper_key} · {fault_key}"
            colour_map.setdefault(label, next(colour_iter))

            # -- geometry ↔ geometry -----------------------------
            for seg_key, rel in cfg["segments"].items():
                y_code, x_code = seg_key.split("-")
                fam = f"{y_code[3:]}–{x_code[3:]}"
                segs = rel if isinstance(rel, list) else [rel]

                grid = grid_for(x_code[3:])
                x_m_all = grid*1_000 if x_code.endswith(("L","W")) else \
                          grid*1e6  if x_code.endswith("A")        else grid

                for seg in segs:
                    keep = _mask(x_m_all, *hp._ranges(seg))
                    if not keep.any():  continue

                    y_m = [10**hp.piecewise_log(xx, seg) for xx in x_m_all[keep]]
                    if y_code.endswith("A"):
                        y_disp = np.array(y_m)/1e6
                    elif y_code.endswith(("L","W")):
                        y_disp = np.array(y_m)/1_000
                    else:
                        y_disp = y_m
                    x_disp = grid[keep]

                    subplot_traces[fam].append(
                        px.line(x=x_disp, y=y_disp).data[0].update(
                            name=label,
                            legendgroup=label,
                            showlegend=label not in legend_once,
                            line_color=colour_map[label]
                        )
                    )
                    legend_once.add(label)

            # -- Mw relations ------------------------------------
            for key, rel in cfg["mw_relations"].items():
                segs = rel if isinstance(rel, list) else [rel]

                if key.startswith("Mw_log"):             # Mw = a + b logX
                    drv_tok = key[6:]
                    if len(drv_tok) <= 3: continue
                    fam = f"Mw–{drv_tok[3:]}"
                    grid = grid_for(drv_tok[3:])
                    x_m_all = grid*1_000 if drv_tok.endswith(("L","W")) else \
                              grid*1e6  if drv_tok.endswith("A")        else grid
                    for seg in segs:
                        keep = _mask(x_m_all, *hp._ranges(seg))
                        if not keep.any(): continue
                        y_Mw = seg["a"] + seg["b"]*np.log10(x_m_all[keep])
                        subplot_traces[fam].append(
                            px.line(x=grid[keep], y=y_Mw).data[0].update(
                                name=label,
                                legendgroup=label,
                                showlegend=label not in legend_once,
                                line_color=colour_map[label],
                                line=dict(dash="dash")
                            )
                        )
                        legend_once.add(label)

                elif key.endswith(("_Mw", "-Mw")):       # logX = a + b Mw
                    drv_tok = key.split("_Mw")[0].split("-Mw")[0]
                    if len(drv_tok) <= 3: continue
                    fam = f"Mw–{drv_tok[3:]}"
                    for seg in segs:
                        Mw_axis = base_Mw
                        logX    = seg["a"] + seg["b"]*Mw_axis
                        x_m_all = 10**logX
                        keep    = _mask(x_m_all, *hp._ranges(seg))
                        if not keep.any(): continue
                        x_disp = x_m_all/1_000 if drv_tok.endswith(("L","W")) else \
                                 x_m_all/1e6  if drv_tok.endswith("A")        else x_m_all
                        subplot_traces[fam].append(
                            px.line(x=x_disp[keep], y=Mw_axis[keep]).data[0].update(
                                name=label,
                                legendgroup=label,
                                showlegend=label not in legend_once,
                                line_color=colour_map[label],
                                line=dict(dash="dash")
                            )
                        )
                        legend_once.add(label)

    # ---------- 4. build subplot grid ---------------------------
    from plotly.subplots import make_subplots
    rows = int(np.ceil(len(fams)/2))
    fig  = make_subplots(rows=rows, cols=2,
                         subplot_titles=fams,
                         horizontal_spacing=0.12,
                         vertical_spacing=0.12)

    r = c = 1
    for fam in fams:
        for tr in subplot_traces[fam]:
            fig.add_trace(tr, row=r, col=c)

        y_var, x_var = fam.split("–")
        fig.update_xaxes(title=f"{x_var} ({units.get(x_var,'')})", row=r, col=c)
        fig.update_yaxes(title=f"{y_var} ({units.get(y_var,'')})", row=r, col=c)

        # caps
        if x_var == "D": fig.update_xaxes(range=[0, 20], row=r, col=c)
        if y_var == "D": fig.update_yaxes(range=[0, 20], row=r, col=c)
        if x_var == "W": fig.update_xaxes(range=[0, 50], row=r, col=c)
        if y_var == "W": fig.update_yaxes(range=[0, 50], row=r, col=c)
        if x_var == "A": fig.update_xaxes(range=[0, 1e5], row=r, col=c)
        if y_var == "A": fig.update_yaxes(range=[0, 1e5], row=r, col=c)

        c += 1
        if c > 2:
            c = 1
            r += 1

    fig.update_layout(height=350*rows,
                      legend_title="Paper · Fault type",
                      legend_itemclick="toggle",
                      legend_groupclick="toggleitem")
    st.plotly_chart(fig, use_container_width=True)

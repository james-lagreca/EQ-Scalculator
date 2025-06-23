# ── scaling_models/yang_etal_2020/__init__.py ──────────────────
"""
Yang et al. (2020) – SCR reverse/strike-slip dataset.

• Surface-rupture length (SRL) coefficients are published in kilometres.
• Displacement coefficients are in metres.
This wrapper keeps those units when Mw is involved and delegates every
other path to the generic metre-based solver.
"""
import json, math, importlib.resources as pkg
from scaling_models._core import generic_solver as gs

# -------- load JSON (one fault model) ---------------------------
_cfg = json.loads(
    pkg.files(__package__)
        .joinpath("data", "yang_etal_2020_scr_rs.json").read_text()
)
MODELS = {"SCR_RS": _cfg}
__all__ = ["MODELS", "solve", "metadata"]

# -------- locate Mw–geometry keys -------------------------------
def _key(sub):
    """Return first mw_relations key that contains *sub* (case-insensitive)."""
    for k in _cfg["mw_relations"]:
        if sub.lower() in k.lower():
            return k
    return None

LEN_KEY  = _key("L")   or _key("SRL")      # Expect "logL_Mw" or "Mw_logL"
DISP_KEY = _key("D")   or _key("Disp")     # Expect "logD_Mw" or "Mw_logD"

# -------- forward & inverse helpers -----------------------------
def _mw_from_len_km(L_km, rel, inverse):
    logL = math.log10(L_km)
    return (logL - rel["a"]) / rel["b"] if inverse else rel["a"] + rel["b"]*logL

def _len_km_from_mw(Mw, rel, inverse):
    return 10 ** (rel["a"] + rel["b"]*Mw) if inverse else \
           10 ** ((Mw - rel["a"]) / rel["b"])

def _mw_from_disp(D_m, rel, inverse):
    logD = math.log10(D_m)
    return (logD - rel["a"]) / rel["b"] if inverse else rel["a"] + rel["b"]*logD

def _disp_from_mw(Mw, rel, inverse):
    return 10 ** (rel["a"] + rel["b"]*Mw) if inverse else \
           10 ** ((Mw - rel["a"]) / rel["b"])

# -------- public solver wrapper ---------------------------------
def solve(driver, value, target, fault_type="SCR_RS"):
    # ---- Mw ↔ Length (km) --------------------------------------
    if LEN_KEY and {"L", "Mw"} <= {driver, target}:
        rel      = _cfg["mw_relations"][LEN_KEY]
        inverse  = LEN_KEY.lower().startswith("log")      # logL_Mw form?
        if driver == "L":
            return _mw_from_len_km(value, rel, inverse)       # L(km) → Mw
        else:  # driver == "Mw"
            return _len_km_from_mw(value, rel, inverse)       # Mw → L(km)

    # ---- Mw ↔ Displacement (m) -------------------------------
    if DISP_KEY and {"D", "Mw"} <= {driver, target}:
        rel     = _cfg["mw_relations"][DISP_KEY]
        inverse = DISP_KEY.lower().startswith("log")          # logD_Mw form?
        if driver == "D":
            return _mw_from_disp(value, rel, inverse)         # D(m) → Mw
        else:  # driver == "Mw"
            return _disp_from_mw(value, rel, inverse)         # Mw → D(m)

    # ---- everything else → generic metre-based solver --------
    return gs.solve(_cfg, driver, value, target)

# -------- minimal metadata helper (for GUI captions) ------------
_METADATA = {
    "citation": "Yang H. et al. (2020) — SCR Australian surface-rupture scaling",
    "fault_type": "SCR_RS",
}
def metadata(_fault="SCR_RS"):
    return _METADATA

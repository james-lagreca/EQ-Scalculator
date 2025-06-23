"""
Leonard (2014) wrapper – handles Table-4 Mw relations
(km / km² / m units) and delegates everything else to the
generic metre-based solver.
"""
import json, math, importlib.resources as pkg
from scaling_models._core import generic_solver as gs
from scaling_models._core import helpers as hp      # for _ranges()
from pathlib import Path

# ── scaling_models/leonard_2014/__init__.py ──────────────────────
"""
Leonard (2014) scaling dispatcher.
JSON files keep the long, human-friendly fault labels:
    • "SCR - Strike Slip"
    • "SCR - Dip Slip"
    • "Interplate - Strike Slip"
    • "Interplate - Dip Slip"

Older code (tests, notebooks, etc.) still uses the short tags
    "SCR_SS"  "SCR_DS"  "IP_SS"  "IP_DS"

The _ALIAS table below maps the short tags onto the long ones so
both styles work transparently.
"""



# -----------------------------------------------------------------
# 1.  load every JSON into MODELS using **its own** long fault-type
# -----------------------------------------------------------------
data_dir = Path(__file__).resolve().parent / "data"
MODELS = {}
for p in data_dir.glob("*.json"):
    cfg = json.loads(p.read_text())
    MODELS[cfg["fault_type"]] = cfg          # long label as key

# -----------------------------------------------------------------
# 2.  alias: short tag  →  long tag
# -----------------------------------------------------------------
_ALIAS = {
    "SCR_SS": "SCR - Strike Slip",
    "SCR_DS": "SCR - Dip Slip",
    "IP_SS" : "Interplate - Strike Slip",
    "IP_DS" : "Interplate - Dip Slip",
}

for short, long in _ALIAS.items():
    MODELS[short] = MODELS[long]             # extra entry, same cfg

__all__ = ["MODELS", "solve", "metadata"]     # what import * sees
# -----------------------------------------------------------------
# 3.  the rest of the file (unit helpers, solve(), …) is unchanged
# -----------------------------------------------------------------
# … keep your existing code here …

# ---------- tiny helpers ----------------------------------------------
def _pick_segment(rel, x_km):
    """Return the segment dict that covers x_km (handles list or dict)."""
    segs = rel if isinstance(rel, list) else [rel]
    for s in segs:
        lo, hi = hp._ranges(s)          # helper understands range_km / range_km2
        if (lo is None or x_km >= lo) and (hi is None or x_km < hi):
            return s
    return segs[-1]                     # fallback = last segment

def _mw_from_geom(x_val, rel):          # x_val already km / km² / m
    seg = _pick_segment(rel, x_val)
    return seg["a"] + seg["b"] * math.log10(x_val)

def _geom_from_mw(Mw, rel):             # return km / km² / m
    seg = _pick_segment(rel, 0)         # range doesn’t matter for inverse
    return 10 ** ((Mw - seg["a"]) / seg["b"])

# ---------- public wrapper ---------------------------------------------
def solve(driver, value, target, fault_type="SCR_SS"):
    cfg = MODELS[fault_type]

    # -- Table-4 Mw relations (km / km² / m) ----------------------------
#  -- Mw forward -------------------------------------------------
    if target == "Mw":
        key = f"Mw_log{driver}"
        if key in mwrel:
            rel = mwrel[key]
            x_km = value                      # value already km or m
            if driver in ("L", "W"):          # convert km → km  (no change)
                x_km = value
            elif driver == "A":               # km² stays km²
                x_km = value
            elif driver == "D":               # metres stay metres
                x_km = value
            return rel["a"] + rel["b"] * math.log10(x_km)
         # value already km/km²/m

    if driver == "Mw":
        key = f"Mw_log{target}"
        if key in mwrel:
            rel = mwrel[key]
            x = 10 ** ((value - rel["a"]) / rel["b"])
            if target in ("L", "W"):    # keep km
                return x
            if target == "A":           # km²
                return x
            if target == "D":           # metres
                return x


    # -- Everything else: generic metre-based solver -------------------
    return gs.solve(cfg, driver, value, target)

# ---------- metadata stub ----------------------------------------------
_METADATA = {"citation": "Leonard M. (2014) – SCR & interplate scaling",}
def metadata(_fault=""):  return _METADATA

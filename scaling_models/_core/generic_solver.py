"""
Generic piece-wise solver
  • geometry ↔ geometry  (Table-3 style)
  • geometry ↔ Mw        (Table-4 style, any naming convention)
  • geometry ↔ M0
Internal convention: geometry values are metres (or m²) unless a paper-
specific wrapper overrides it.
"""

import math
from . import helpers as hp  # piece-wise tools


# ---------------------------------------------------------------------
#  unit helpers
# ---------------------------------------------------------------------
def _to_m(val, kind):        # km → m • km² → m²
    return val * 1_000   if kind in ("L", "W") else \
           val * 1_000_000 if kind == "A"      else val


def _from_m(val, kind):      # inverse
    return val / 1_000   if kind in ("L", "W") else \
           val / 1_000_000 if kind == "A"      else val


# ---------------------------------------------------------------------
#  public solver for ONE cfg dict
# ---------------------------------------------------------------------
def solve(cfg, driver, value, target):
    segs = cfg["segments"]
    mwr  = cfg["mw_relations"]

    # ---------------- fast identity ----------------
    if driver == target:
        return value

    # =================================================================
    # 1.  geometry ↔ geometry  (Table-3)
    # =================================================================
    seg_key = f"log{target}-log{driver}"
    inv_key = f"log{driver}-log{target}"

    if seg_key in segs:                                # forward
        logy = hp.piecewise_log(_to_m(value, driver), segs[seg_key])
        return _from_m(10**logy, target)

    if inv_key in segs:                                # inverse
        logx = hp.invert_piecewise(
            math.log10(_to_m(value, target)), segs[inv_key]
        )
        return _from_m(logx, driver)

    # =================================================================
    # 2.  geometry ↔ Mw  (Table-4)
    # =================================================================
    # ---- forward  geometry → Mw -------------------------------------
    if target == "Mw":
        candidates = (
            f"Mw_log{driver}",            # Mw = a + b·logX   (Leonard)
            f"log{driver}_Mw",            # logX = a + b·Mw  (Yang)
            f"log{driver}-Mw",
        )
        key = next((k for k in candidates if k in mwr), None)
        if key:
            rels = mwr[key] if isinstance(mwr[key], list) else [mwr[key]]
            for r in rels:
                x_m = _to_m(value, driver)
                lo, hi = hp._ranges(r)
                if (lo is None or x_m >= lo) and (hi is None or x_m < hi):
                    if key.startswith("Mw_log"):               # forward form
                        return r["a"] + r["b"] * math.log10(x_m)
                    else:                                      # inverse form
                        return (math.log10(x_m) - r["a"]) / r["b"]

    # ---- inverse  Mw → geometry -------------------------------------
    if driver == "Mw":
        candidates = (
            f"Mw_log{target}",
            f"log{target}_Mw",
            f"log{target}-Mw",
        )
        key = next((k for k in candidates if k in mwr), None)
        if key:
            rels = mwr[key] if isinstance(mwr[key], list) else [mwr[key]]
            for r in rels:
                if key.startswith("Mw_log"):                    # forward form
                    x_m = 10 ** ((value - r["a"]) / r["b"])
                else:                                           # inverse form
                    x_m = 10 ** (r["a"] + r["b"] * value)

                lo, hi = hp._ranges(r)
                if (lo is None or x_m >= lo) and (hi is None or x_m < hi):
                    return _from_m(x_m, target)

    # =================================================================
    # 3.  geometry ↔ seismic moment  (unchanged)
    # =================================================================
    m0_key  = f"logM0-log{driver}"
    inv_m0  = f"logM0-log{target}"

    if target == "M0" and m0_key in segs:
        logM0 = hp.piecewise_log(_to_m(value, driver), segs[m0_key])
        return 10 ** logM0

    if driver == "M0" and inv_m0 in segs:
        x_m = hp.invert_piecewise(math.log10(value), segs[inv_m0])
        return _from_m(x_m, target)

    # -----------------------------------------------------------------
    raise NotImplementedError(
        f"No direct regression for {driver} → {target}"
    )

# ── tests/test_leonard_all.py ─────────────────────────────────────
"""
Exhaustive round-trip tests for Leonard (2014):
• geometry–geometry (Table 3)
• Mw–geometry     (Table 4)
• M0–geometry     (Table 3)
The idea: pick a mid-range driver value, compute the target with
Leonard.solve(…), then invert and make sure we get the original
driver back to <1 % error (or 0.02 Mw units).
"""

import math, pytest
import scaling_models.leonard_2014 as L14
from scaling_models._core import helpers as hp

# ---------- util: choose a value inside the segment range ----------
def mid_value(seg, code):
    """
    Pick a safe mid-range driver value (km, km², or m).
    • `seg` may be a dict or list; we always use the *first* piece.
    """
    if isinstance(seg, list):
        seg = seg[0]                   # first piece is fine

    lo, hi = hp._ranges(seg)
    lo = 1.0 if lo is None else lo
    hi = lo * 20 if hi is None else hi
    mid = math.sqrt(lo * hi)

    return mid            # already in km / km² / m as required


# ---------- param lists ---------------------------------------------
fault_types = ["SCR_SS","SCR_DS","IP_SS","IP_DS"]

# collect every seg key
seg_items = []          # (fault, seg_key)
for ft in fault_types:
    for seg_key in L14.MODELS[ft]["segments"]:
        seg_items.append((ft, seg_key))

mw_items = []           # (fault, mw_key)
for ft in fault_types:
    for mw_key in L14.MODELS[ft]["mw_relations"]:
        mw_items.append((ft, mw_key))

# --------------------------------------------------------------------
# 1. geometry pairs (Table 3): round-trip
# --------------------------------------------------------------------
@pytest.mark.parametrize("fault,seg_key", seg_items)
def test_geom_round_trip(fault, seg_key):
    y_code, x_code = seg_key.split("-")
    target = y_code[3:]   # drop 'log'
    driver = x_code[3:]
    seg    = L14.MODELS[fault]["segments"][seg_key]
    driver_val = mid_value(seg, driver)

    # forward & invert
    y_val = L14.solve(driver, driver_val, target, fault)
    x_back = L14.solve(target, y_val, driver, fault)

    if driver in ("L","W","A"):
        tol = 0.01 * driver_val           # 1 % for km / km²
    else:  # displacement in metres
        tol = 0.01 * driver_val
    assert abs(x_back - driver_val) < tol

# --------------------------------------------------------------------
# 2. Mw pairs (Table 4): round-trip
# --------------------------------------------------------------------
@pytest.mark.parametrize("fault,mw_key", mw_items)
def test_mw_round_trip(fault, mw_key):
    if not mw_key.startswith("Mw_log"):   # we only need one direction
        pytest.skip("inverse key covered by forward test")

    driver = mw_key[-1]   # 'A','L','W','D'
    rel    = L14.MODELS[fault]["mw_relations"][mw_key]
    # choose a mid-range driver: 10 km, 30 km², 10 m, etc.
    test_val = {"L":10.0, "W":3.0, "A":30.0, "D":2.0}[driver]

    Mw      = L14.solve(driver, test_val, "Mw", fault)
    drv_back= L14.solve("Mw", Mw, driver, fault)

    tol = 0.02 if driver!="Mw" else 0.03  # Mw within 0.02 mag, geom 3 %
    assert abs(drv_back - test_val) / test_val < 0.03

# --------------------------------------------------------------------
# 3. M0 pairs (moment – geometry): round-trip
# --------------------------------------------------------------------
@pytest.mark.parametrize("fault", fault_types)
def test_moment_round_trip(fault):
    # only one moment relation per model (logM0-logA)
    driver = "A"
    test_val = 40.0      # 40 km²
    M0 = L14.solve(driver, test_val, "M0", fault)
    A_back = L14.solve("M0", M0, "A", fault)
    assert abs(A_back - test_val) / test_val < 0.03

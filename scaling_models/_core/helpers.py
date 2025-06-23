import math

# ── scaling_models/_core/helpers.py
def _ranges(seg):
    """
    Return (lo, hi) for *one* segment.
    Works whether `seg` is a dict or already a list of dicts.
    """
    if isinstance(seg, list):          # first/only piece
        seg = seg[0]

    lo, hi = None, None
    if "range_km" in seg:
        lo, hi = seg["range_km"]
    elif "range_km2" in seg:
        lo, hi = seg["range_km2"]

    return lo, hi


def piecewise_log(x, segments):
    """log10-y from x for dict OR list[dict] segments."""
    seglist = segments if isinstance(segments, list) else [segments]
    for s in seglist:
        lo, hi = _ranges(s)
        if (lo is None or x >= lo) and (hi is None or x < hi):
            return s["b"] * math.log10(x) + s["a"]
    raise ValueError("x outside all segments")

def invert_piecewise(logy, segments):
    """x from log10-y."""
    seglist = segments if isinstance(segments, list) else [segments]
    for s in seglist:
        b, a = s["b"], s["a"]
        lo, hi = _ranges(s)
        logx = (logy - a) / b
        x = 10 ** logx
        if (lo is None or x >= lo) and (hi is None or x < hi):
            return x
    raise ValueError("y outside all segments")

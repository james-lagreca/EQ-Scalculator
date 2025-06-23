import math, pytest, scaling_models.yang_etal_2020 as Y

def test_mw_to_srl():
    Mw      = 7.0
    logLkm  = 0.50*Mw - 1.93
    L_exp   = 10 ** logLkm           # ≈ 37.2 km
    L_got   = Y.solve("Mw", Mw, "L") # wrapper returns km
    assert L_got == pytest.approx(L_exp, rel=5e-2)   # 5 % tol

def test_srl_to_mw():
    L_km    = 37.2
    Mw_exp  = (math.log10(L_km) + 1.93) / 0.50
    Mw_got  = Y.solve("L", L_km, "Mw")
    assert Mw_got == pytest.approx(Mw_exp, abs=0.02)

def test_round_trip_len_mw():
    L_km = 120
    Mw   = Y.solve("L", L_km, "Mw")
    L_rt = Y.solve("Mw", Mw, "L")
    assert L_rt == pytest.approx(L_km, rel=1e-3)
